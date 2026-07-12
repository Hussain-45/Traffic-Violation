import os
import time
import datetime
import json
import uuid
import cv2
import shutil
import threading
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from loguru import logger

from backend.app.database import get_db, SessionLocal
from backend.app.models import Violation, Vehicle, Camera, FineRule, User, ActivityLog, Notification, EmailLogModel
from backend.app.models.video_analysis_model import AnalysisJob
from backend.app.models.evidence_model import EvidenceModel
from backend.app.auth.jwt import get_current_user
from backend.app.config import settings
from backend.app.schemas.video_analysis_schema import VideoJobCreate, VideoJobOut

from ai.pipelines.pipeline_manager import pipeline_manager
from ai.pipelines.registry import module_registry
from backend.app.services.tracking_service import tracking_service
from backend.app.services.inference_service import inference_service
from ai.services.trajectory_service import trajectory_service
from ai.services.violation_aggregation_service import violation_aggregation_service
from ai.services.plate_recognition_service import plate_recognition_service
from ai.services.rider_association_service import rider_association_service
from ai.services.plate_association_service import plate_association_service
from backend.app.services.camera_manager import camera_manager

try:
    import psutil
except ImportError:
    psutil = None

try:
    import torch
except ImportError:
    torch = None

router = APIRouter(prefix="/video", tags=["Video Analysis"])
pipeline_processing_lock = threading.Lock()

def get_system_usage():
    mem_mb = 0.0
    if psutil:
        try:
            mem_mb = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
        except:
            pass
    
    gpu_str = "N/A"
    if torch:
        try:
            if torch.cuda.is_available():
                gpu_str = f"CUDA:{torch.cuda.current_device()} (Alloc: {torch.cuda.memory_allocated() / (1024*1024):.1f}MB)"
        except:
            pass
        
    return mem_mb, gpu_str

def reset_all_pipeline_services():
    logger.info("[Video Analysis] Resetting all stateful pipeline services caches...")
    try:
        tracking_service.reset()
    except Exception as e:
        logger.error(f"Error resetting tracking_service: {e}")
        
    try:
        trajectory_service.trajectories.clear()
        trajectory_service.track_ages.clear()
        trajectory_service.motion_cache.clear()
    except Exception as e:
        logger.error(f"Error clearing trajectory_service: {e}")
        
    try:
        violation_aggregation_service.reset()
    except Exception as e:
        logger.error(f"Error resetting violation_aggregation_service: {e}")
        
    try:
        plate_recognition_service.recognition_states.clear()
    except Exception as e:
        logger.error(f"Error clearing plate_recognition_service: {e}")
        
    try:
        rider_association_service.reset()
    except Exception as e:
        logger.error(f"Error resetting rider_association_service: {e}")
        
    try:
        plate_association_service.associations.clear()
    except Exception as e:
        logger.error(f"Error clearing plate_association_service: {e}")
    logger.info("[Video Analysis] Stateful services caches reset complete.")

def get_or_create_video_camera(db: Session) -> Camera:
    cam = db.query(Camera).filter(Camera.id == "CAM-VIDEO").first()
    if not cam:
        cam = Camera(
            id="CAM-VIDEO",
            name="Offline Video Analysis Node",
            location="Uploaded Video File Stream",
            status="online",
            health_status="good",
            lat=28.6139,
            lng=77.2090
        )
        db.add(cam)
        db.commit()
        db.refresh(cam)
    return cam

def analyze_video_task(job_id: int, payload: dict, created_by_id: int):
    failure_stage = "Job Initialization"
    logger.info(f"[Video Analysis] Background task started for Job #{job_id}.")
    db = SessionLocal()
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        logger.error(f"[Video Analysis] Job #{job_id} not found in database. Exiting background task.")
        db.close()
        return

    # Store camera manager paused state before starting
    original_camera_paused = getattr(camera_manager, "paused", False)

    try:
        failure_stage = "Video File Validation"
        logger.info(f"[Video Analysis] Job Created. Target Video Filename: {job.filename}")
        video_path = os.path.abspath(job.original_video_path)
        logger.info(f"[Video Analysis] Video Absolute Path: {video_path}")
        
        video_exists = os.path.exists(video_path)
        logger.info(f"[Video Analysis] Video Exists on Disk: {video_exists}")
        if not video_exists:
            raise FileNotFoundError(f"Video file does not exist at absolute path: {video_path}")
            
        video_size = os.path.getsize(video_path)
        logger.info(f"[Video Analysis] Video Size: {video_size} bytes")
        if video_size <= 0:
            raise ValueError(f"Video file is empty (size = {video_size} bytes)")

        # Pause camera manager to avoid concurrent inference deadlocks and tracker/aggregation state pollution
        logger.info("[Video Analysis] Pausing camera manager inference thread...")
        camera_manager.paused = True

        # Reset all stateful services for clean tracking and context matching
        reset_all_pipeline_services()

        job.status = "processing"
        job.started_at = datetime.datetime.utcnow()
        job.progress = 0.0
        db.commit()

        failure_stage = "VideoCapture Setup"
        cap = cv2.VideoCapture(video_path)
        logger.info(f"[Video Analysis] VideoCapture Created")
        
        is_opened = cap.isOpened()
        logger.info(f"[Video Analysis] VideoCapture.isOpened(): {is_opened}")
        if not is_opened:
            raise ValueError(f"OpenCV failed to open video file at {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        if fps <= 0:
            fps = 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        logger.info(f"[Video Analysis] Video Properties - FPS: {fps}, Resolution: {width}x{height}, Total Frames: {total_frames}")

        job.total_frames = total_frames
        db.commit()

        # Create output video writer
        out_fn = f"output_{uuid.uuid4()}.mp4"
        out_path = os.path.join(settings.UPLOAD_DIR, "videos", "output", out_fn)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out_writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

        # Setup virtual camera
        camera = get_or_create_video_camera(db)

        # Config override preparation
        enabled_modules = payload.get("enabled_modules", [])
        conf_thresh = payload.get("confidence_threshold", 0.45)
        
        if not enabled_modules:
            enabled_modules = ["vehicle_detection", "vehicle_tracking"]
        if "vehicle_detection" not in enabled_modules:
            enabled_modules.insert(0, "vehicle_detection")
        if "vehicle_tracking" not in enabled_modules:
            enabled_modules.insert(1, "vehicle_tracking")
        if "violation_engine" not in enabled_modules:
            enabled_modules.append("violation_engine")

        failure_stage = "Pipeline Initialization Verification"
        logger.info("[Video Analysis] Verifying pipeline initialization state...")
        if not pipeline_manager.is_running:
            raise RuntimeError("Pipeline Manager is not running.")
        
        # Verify YOLO vehicle detection module
        veh_detect_mod = module_registry.get("vehicle_detection")
        if not veh_detect_mod:
            raise RuntimeError("YOLO Vehicle Detection module is not loaded in pipeline.")
        if inference_service.model is None:
            raise RuntimeError("YOLO Vehicle Detection model weights are not loaded.")
        logger.info("[Video Analysis] YOLO Vehicle Detection model verified successfully.")

        # Verify tracker
        tracker_mod = module_registry.get("vehicle_tracking")
        if not tracker_mod:
            raise RuntimeError("Vehicle Tracking module is not loaded in pipeline.")
        if tracking_service is None:
            raise RuntimeError("Tracking service is not initialized.")
        logger.info("[Video Analysis] Tracker verified successfully.")

        # Verify Helmet model if enabled
        if "helmet_detection" in enabled_modules:
            helmet_mod = module_registry.get("helmet_detection")
            if not helmet_mod:
                raise RuntimeError("Helmet Detection module is not loaded in pipeline.")
            if getattr(helmet_mod, "model", None) is None and getattr(helmet_mod, "mock_mode", False) is False:
                raise RuntimeError("Helmet Detection model weights are not loaded.")
            logger.info("[Video Analysis] Helmet model verified successfully.")

        # Verify OCR if enabled
        if "ocr" in enabled_modules:
            ocr_mod = module_registry.get("ocr")
            if not ocr_mod:
                raise RuntimeError("OCR module is not loaded in pipeline.")
            if getattr(ocr_mod, "reader", None) is None and getattr(ocr_mod, "mock_mode", False) is False:
                raise RuntimeError("EasyOCR reader is not initialized.")
            logger.info("[Video Analysis] OCR verified successfully.")

        logger.info("[Video Analysis] Pipeline Initialized and verified.")

        t_start = time.time()
        processed_frames = 0
        vehicles_set = set()
        violations_count = 0
        timeline_events = []

        logger.info(f"[Video Analysis] Starting processing loop for job #{job_id} ({total_frames} frames)...")

        failure_stage = "Inference Frame Processing"
        while cap.isOpened():
            ret, frame = cap.read()
            
            # Step 4: Validate First Frame
            if processed_frames == 0:
                logger.info(f"[Video Analysis] First Frame Read - ret: {ret}, frame is None: {frame is None}, frame.shape: {frame.shape if frame is not None else 'N/A'}")
                if not ret:
                    raise ValueError("Failed to read the first frame from the video source. The file may be corrupted or codec unsupported.")

            if not ret:
                break

            processed_frames += 1
            f_id = processed_frames
            timestamp_sec = f_id / fps
            timestamp_str = f"{int(timestamp_sec // 60):02d}:{int(timestamp_sec % 60):02d}"

            t_frame_start = time.time()

            with pipeline_processing_lock:
                original_camera_id = pipeline_manager.config.get("camera_id")
                original_enabled = pipeline_manager.enabled_modules
                original_conf = pipeline_manager.config.get("modules", {}).get("vehicle_detection", {}).get("confidence_threshold", 0.45)
                
                pipeline_manager.enabled_modules = enabled_modules
                pipeline_manager.config.setdefault("modules", {}).setdefault("vehicle_detection", {})["confidence_threshold"] = conf_thresh
                pipeline_manager.config["camera_id"] = camera.id

                result = pipeline_manager.process_frame(frame, frame_id=f_id, timestamp=t_start + timestamp_sec)

                pipeline_manager.enabled_modules = original_enabled
                pipeline_manager.config["modules"]["vehicle_detection"]["confidence_threshold"] = original_conf
                if original_camera_id is not None:
                    pipeline_manager.config["camera_id"] = original_camera_id
                else:
                    pipeline_manager.config.pop("camera_id", None)

            drawn = result.visualized_frame if result.visualized_frame is not None else frame
            out_writer.write(drawn)

            if processed_frames == 1:
                thumb_fn = f"thumb_{job_id}.jpg"
                thumb_path = os.path.join(settings.UPLOAD_DIR, "videos", "thumbnails", thumb_fn)
                cv2.imwrite(thumb_path, frame)
                job.thumbnail_path = os.path.join("data/uploads/videos/thumbnails", thumb_fn)
                db.commit()
                logger.info(f"Frame 1 processed. Thumbnail saved to {thumb_path}")

            # Progress log every 100 frames
            if processed_frames % 100 == 0 or processed_frames == 1:
                logger.info(f"Frame {processed_frames} processed")

            if result.counts:
                for v_class, count in result.counts.items():
                    if count > 0:
                        vehicles_set.add(v_class)

            # Detailed stage debugging logs
            elapsed_frame = time.time() - t_frame_start
            mem_mb, gpu_str = get_system_usage()

            logger.info(f"[Video Analysis] Frame {f_id}/{total_frames} | "
                         f"Processing Time: {elapsed_frame*1000:.1f}ms | "
                         f"Memory: {mem_mb:.1f}MB | GPU: {gpu_str}")

            veh_count = result.counts.get("total_vehicles", 0) if result.counts else 0
            logger.info(f"  Stage 3: Vehicle Detection | Count: {veh_count} | Timing: {result.timing.get('vehicle_detection_time_ms', 0.0)}ms")

            active_tracks = result.metadata.get("vehicle_tracking", {}).get("active_tracks", 0)
            logger.info(f"  Stage 4: Vehicle Tracking | Active Tracks: {active_tracks} | Timing: {result.timing.get('vehicle_tracking_time_ms', 0.0)}ms")

            if "helmet_detection" in enabled_modules:
                helmet_stats = result.metadata.get("helmet_detection", {})
                logger.info(f"  Stage 5a: Helmet Detection | Active Riders: {helmet_stats.get('active_riders', 0)} | Violations: {helmet_stats.get('helmet_violations', 0)} | Timing: {result.timing.get('helmet_detection_time_ms', 0.0)}ms")

            if "seat_belt_detection" in enabled_modules:
                seat_belt_stats = result.metadata.get("seat_belt_detection", {})
                logger.info(f"  Stage 5b: Seat Belt Detection | Active Checked: {seat_belt_stats.get('checked_vehicles', 0)} | Violations: {seat_belt_stats.get('seatbelt_violations', 0)} | Timing: {result.timing.get('seatbelt_detection_time_ms', 0.0)}ms")

            if "phone_detection" in enabled_modules:
                phone_stats = result.metadata.get("phone_detection", {})
                logger.info(f"  Stage 5c: Mobile Phone Detection | Active Checked: {phone_stats.get('checked_vehicles', 0)} | Violations: {phone_stats.get('phone_violations', 0)} | Timing: {result.timing.get('phone_detection_time_ms', 0.0)}ms")

            if "wrong_side_detection" in enabled_modules:
                wrong_side_stats = result.metadata.get("wrong_side_detection", {})
                logger.info(f"  Stage 5d: Wrong Side Detection | Matches: {wrong_side_stats.get('matches_count', 0)} | Timing: {result.timing.get('wrong_side_detection_time_ms', 0.0)}ms")

            if "traffic_signal_detection" in enabled_modules:
                logger.info(f"  Stage 5e: Red Light Detection | Timing: {result.timing.get('traffic_signal_detection_time_ms', 0.0)}ms")

            if "number_plate_detection" in enabled_modules:
                logger.info(f"  Stage 5f: Number Plate Detection | Timing: {result.timing.get('number_plate_detection_time_ms', 0.0)}ms")

            if "ocr" in enabled_modules:
                logger.info(f"  Stage 5g: License Plate OCR | Timing: {result.timing.get('ocr_time_ms', 0.0)}ms")

            records = result.metadata.get("violation_engine", {}).get("records", [])
            logger.info(f"  Stage 6: Violation Engine | Records: {len(records)} | Timing: {result.timing.get('violation_engine_time_ms', 0.0)}ms")

            if records:
                for r in records:
                    decision = r.get("decision_status")
                    track_id = r.get("tracking_id")
                    v_type = r.get("violation_type")
                    conf = r.get("confidence", 0.90)

                    if decision == "Confirmed":
                        logger.info(f"    - CONFIRMED: Track #{track_id} -> {v_type} | Conf: {conf}")
                        plate_str = r.get("verified_plate") or "N/A"
                        violation_type = r.get("violation_type")
                        
                        vehicle = db.query(Vehicle).filter(Vehicle.license_plate == plate_str).first()
                        if not vehicle and plate_str != "N/A":
                            vehicle = Vehicle(
                                license_plate=plate_str,
                                type="car",
                                brand="Toyota",
                                color="White",
                                owner_name="Unknown Owner",
                                status="valid"
                            )
                            db.add(vehicle)
                            db.commit()
                            db.refresh(vehicle)
                        
                        rule = db.query(FineRule).filter(FineRule.violation_type == violation_type).first()
                        fine_val = rule.amount if rule else 1000.0

                        evidence_records = result.metadata.get("evidence_records", [])
                        matching_evidence = None
                        for ev in evidence_records:
                            if ev.get("tracking_id") == r.get("tracking_id") and ev.get("violation_type") == violation_type:
                                matching_evidence = ev
                                break

                        violation = Violation(
                            vehicle_id=vehicle.id if vehicle else 1,
                            camera_id=camera.id,
                            type=violation_type,
                            location=camera.location,
                            fine_amount=fine_val,
                            status="pending",
                            evidence_image_path=matching_evidence.get("annotated_frame_path") if matching_evidence else None,
                            evidence_video_path=os.path.join("data/uploads/videos/output", out_fn),
                            confidence_score=conf,
                            timestamp=datetime.datetime.utcnow()
                        )
                        db.add(violation)
                        db.commit()
                        db.refresh(violation)

                        violations_count += 1
                        
                        if matching_evidence:
                            db_evidence = EvidenceModel(
                                evidence_id=matching_evidence.get("evidence_id"),
                                violation_id=violation.id,
                                tracking_id=matching_evidence.get("tracking_id"),
                                verified_plate=matching_evidence.get("verified_plate"),
                                vehicle_class=matching_evidence.get("vehicle_class"),
                                violation_type=matching_evidence.get("violation_type"),
                                severity=matching_evidence.get("severity"),
                                timestamp=matching_evidence.get("timestamp") or time.time(),
                                frame_id=matching_evidence.get("frame_id"),
                                camera_id=camera.id,
                                location=camera.location,
                                confidence=matching_evidence.get("confidence"),
                                original_frame_path=matching_evidence.get("original_frame_path"),
                                annotated_frame_path=matching_evidence.get("annotated_frame_path"),
                                vehicle_crop_path=matching_evidence.get("vehicle_crop_path"),
                                plate_crop_path=matching_evidence.get("plate_crop_path"),
                                hash=matching_evidence.get("hash"),
                                metadata=matching_evidence.get("metadata")
                            )
                            db.add(db_evidence)
                            db.commit()

                        notif = Notification(
                            user_id=created_by_id,
                            title="Fine Challan Generated",
                            message=f"New {violation_type.replace('_', ' ').title()} logged for Vehicle {plate_str} during Video Analysis. Fine: Rs. {fine_val}",
                            type="fine"
                        )
                        db.add(notif)
                        db.commit()

                        timeline_events.append({
                            "timestamp_sec": timestamp_sec,
                            "timestamp_str": timestamp_str,
                            "type": violation_type,
                            "plate": plate_str,
                            "confidence": conf
                        })
                    else:
                        ctx = violation_aggregation_service.get_context(track_id)
                        reason = ""
                        if not ctx:
                            reason = "No violation context initialized"
                        elif not ctx.stable_detection:
                            reason = f"Track age unstable (frame count {ctx.frame_count} < 3)"
                        elif conf < conf_thresh:
                            reason = f"Confidence {conf} < threshold {conf_thresh}"
                        logger.info(f"    - PENDING/REJECTED: Track #{track_id} -> {v_type} | Reason: {reason}")

            # Update DB progress: commit on Frame 1, and every 10 frames thereafter
            if processed_frames == 1 or processed_frames % 10 == 0:
                elapsed = time.time() - t_start
                job.processed_frames = processed_frames
                job.progress = min(99.0, round((processed_frames / total_frames) * 100.0, 1))
                job.vehicles_detected = len(vehicles_set)
                job.violations_detected = violations_count
                job.processing_fps = round(processed_frames / elapsed if elapsed > 0 else 0.0, 2)
                db.commit()

        cap.release()
        out_writer.release()

        failure_stage = "Report Generation"
        t_end = time.time()
        elapsed_total = t_end - t_start

        report_fn = f"report_video_{job_id}_{int(time.time())}.csv"
        report_path = os.path.join("data", "reports", report_fn)
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, "w", encoding="utf-8") as rf:
            rf.write("Timestamp,Type,License Plate,Confidence\n")
            for ev in timeline_events:
                rf.write(f"{ev['timestamp_str']},{ev['type']},{ev['plate']},{ev['confidence']}\n")

        job.status = "completed"
        job.progress = 100.0
        job.processed_frames = processed_frames
        job.vehicles_detected = len(vehicles_set)
        job.violations_detected = violations_count
        job.processing_fps = round(processed_frames / elapsed_total if elapsed_total > 0 else 0.0, 2)
        job.processing_time = round(elapsed_total, 2)
        job.completed_at = datetime.datetime.utcnow()
        job.processed_video_path = os.path.join("data/uploads/videos/output", out_fn)
        job.annotated_video_path = os.path.join("data/uploads/videos/output", out_fn)
        job.report_path = f"/data/reports/{report_fn}"
        job.timestamps = json.dumps(timeline_events)
        db.commit()

        log = ActivityLog(
            user_id=created_by_id,
            action=f"Completed Offline Video Analysis Job #{job_id} ({job.filename})"
        )
        db.add(log)
        db.commit()
        logger.info(f"[Video Analysis] Background task ended successfully for Job #{job_id}.")

    except Exception as e:
        import traceback
        st = traceback.format_exc()
        logger.error(f"Error in video analysis job {job_id} during stage '{failure_stage}': {e}\n{st}")
        
        job.status = "failed"
        job.error_message = f"[{failure_stage}] {str(e)}\n\nStack Trace:\n{st}"
        db.commit()
        logger.info(f"[Video Analysis] Background task ended with failure for Job #{job_id}.")
        raise
    finally:
        # Restore camera manager state
        logger.info(f"[Video Analysis] Restoring camera manager paused state to {original_camera_paused}...")
        camera_manager.paused = original_camera_paused

        # Reset services caches to ensure clean start for live camera monitor
        reset_all_pipeline_services()

        db.close()

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".mp4", ".avi", ".mov", ".mkv"]:
        raise HTTPException(status_code=400, detail="Unsupported video format. Please upload MP4, AVI, MOV, or MKV.")

    unique_fn = f"{uuid.uuid4()}{file_ext}"
    input_path = os.path.join(settings.UPLOAD_DIR, "videos", "input", unique_fn)
    
    os.makedirs(os.path.dirname(input_path), exist_ok=True)
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cap = cv2.VideoCapture(input_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    duration = total_frames / fps if fps > 0 else 0

    return {
        "filename": file.filename,
        "saved_filename": unique_fn,
        "original_video_path": os.path.join("data/uploads/videos/input", unique_fn),
        "resolution": f"{width}x{height}",
        "fps": fps,
        "duration": round(duration, 2),
        "size_bytes": os.path.getsize(input_path)
    }

@router.post("/analyze", response_model=VideoJobOut)
def start_video_analysis(
    payload: VideoJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    input_local_path = os.path.join(settings.UPLOAD_DIR, "videos", "input", payload.filename)
    if not os.path.exists(input_local_path):
        raise HTTPException(status_code=404, detail="Uploaded video file not found on server.")

    job = AnalysisJob(
        filename=payload.filename,
        original_video_path=input_local_path,
        status="pending",
        progress=0.0,
        created_by=current_user.id
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        analyze_video_task,
        job_id=job.id,
        payload=payload.dict(),
        created_by_id=current_user.id
    )

    return job

@router.get("/jobs", response_model=List[VideoJobOut])
def get_all_jobs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(AnalysisJob).order_by(AnalysisJob.created_at.desc()).all()

@router.get("/job/{id}", response_model=VideoJobOut)
def get_job_details(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    return job

@router.get("/status/{id}")
def get_job_status(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    return {
        "status": job.status,
        "progress": job.progress,
        "processed_frames": job.processed_frames,
        "total_frames": job.total_frames,
        "vehicles_detected": job.vehicles_detected,
        "violations_detected": job.violations_detected,
        "processing_fps": job.processing_fps,
        "processing_time": job.processing_time,
        "error_message": job.error_message
    }

@router.get("/result/{id}")
def get_job_result(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    
    evidence = db.query(EvidenceModel).join(Violation, EvidenceModel.violation_id == Violation.id).filter(Violation.evidence_video_path == job.processed_video_path).all()

    timestamps = []
    if job.timestamps:
        try:
            timestamps = json.loads(job.timestamps)
        except:
            pass

    return {
        "job_id": job.id,
        "filename": job.filename,
        "vehicles_detected": job.vehicles_detected,
        "violations_detected": job.violations_detected,
        "timeline": timestamps,
        "evidence": [
            {
                "evidence_id": ev.evidence_id,
                "violation_id": ev.violation_id,
                "verified_plate": ev.verified_plate,
                "violation_type": ev.violation_type,
                "severity": ev.severity,
                "confidence": ev.confidence,
                "timestamp": ev.timestamp,
                "frame_id": ev.frame_id,
                "original_frame_path": ev.original_frame_path,
                "annotated_frame_path": ev.annotated_frame_path,
                "vehicle_crop_path": ev.vehicle_crop_path,
                "plate_crop_path": ev.plate_crop_path
            }
            for ev in evidence
        ]
    }

@router.get("/download/{id}")
def download_processed_video(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == id).first()
    if not job or not job.processed_video_path:
        raise HTTPException(status_code=404, detail="Processed video not found or job not completed")
    
    if not os.path.exists(job.processed_video_path):
        raise HTTPException(status_code=404, detail="Processed video file missing on disk")
        
    return FileResponse(
        path=job.processed_video_path,
        media_type="video/mp4",
        filename=os.path.basename(job.processed_video_path)
    )

@router.delete("/job/{id}")
def delete_job(id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    for path in [job.original_video_path, job.processed_video_path, job.thumbnail_path]:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass

    db.delete(job)
    db.commit()
    return {"status": "success", "message": f"Job #{id} deleted successfully."}
