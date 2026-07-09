import asyncio
from fastapi import APIRouter, Response, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Union
import os
from backend.app.services.camera_manager import camera_manager
from backend.app.services.tracking_service import tracking_service
from ai.pipelines.pipeline_manager import pipeline_manager
from ai.pipelines.registry import module_registry
from loguru import logger

router = APIRouter()

class ConnectRequest(BaseModel):
    source: Union[int, str] = Field(
        ..., 
        description="Camera index integer (e.g., 0) or file path string / RTSP URL."
    )

@router.get("/status")
def get_camera_status():
    """
    Returns current connection parameters and diagnostics.
    """
    helmet_mod = module_registry.get("helmet_detection")
    helmet_enabled = "helmet_detection" in pipeline_manager.enabled_modules
    helmet_model_loaded = helmet_mod is not None and helmet_mod.health()
    helmet_weights_exist = os.path.exists("models/trained/helmet_best.pt")

    sb_mod = module_registry.get("seat_belt_detection")
    sb_enabled = "seat_belt_detection" in pipeline_manager.enabled_modules
    sb_model_loaded = sb_mod is not None and sb_mod.health()
    sb_weights_exist = os.path.exists("models/trained/seatbelt_best.pt")

    mp_mod = module_registry.get("phone_detection")
    mp_enabled = "phone_detection" in pipeline_manager.enabled_modules
    mp_model_loaded = mp_mod is not None and mp_mod.health()
    mp_weights_exist = os.path.exists("models/trained/mobile_best.pt")

    ts_mod = module_registry.get("traffic_signal_detection")
    ts_enabled = "traffic_signal_detection" in pipeline_manager.enabled_modules
    ts_model_loaded = ts_mod is not None and ts_mod.health()
    ts_weights_exist = os.path.exists("models/trained/traffic_light_best.pt")

    ws_mod = module_registry.get("wrong_side_detection")
    ws_enabled = "wrong_side_detection" in pipeline_manager.enabled_modules
    ws_model_loaded = ws_mod is not None and ws_mod.health()

    tr_mod = module_registry.get("triple_riding_detection")
    tr_enabled = "triple_riding_detection" in pipeline_manager.enabled_modules
    tr_model_loaded = tr_mod is not None and tr_mod.health()
    
    return {
        "connected": camera_manager.is_connected,
        "fps": round(camera_manager.actual_fps, 2),
        "width": camera_manager.width,
        "height": camera_manager.height,
        "source_type": camera_manager.source_type,
        "source": camera_manager.current_source,
        "dropped_frames": camera_manager.dropped_frames,
        "reconnect_attempts": camera_manager.reconnect_attempts,
        "detections": camera_manager.latest_counts,
        "tracking": tracking_service.get_stats(),
        "helmet_stats": {
            "helmet_count": camera_manager.latest_counts.get("helmet", 0),
            "no_helmet_count": camera_manager.latest_counts.get("no_helmet", 0),
            "detection_status": "Active" if helmet_enabled else "Inactive",
            "model_status": "Loaded" if helmet_model_loaded else "Not Loaded",
            "training_status": "Pre-trained Weights Available" if helmet_weights_exist else "Not Trained"
        },
        "seat_belt_stats": {
            "seat_belt_count": camera_manager.latest_counts.get("seat_belt", 0),
            "no_seat_belt_count": camera_manager.latest_counts.get("no_seat_belt", 0),
            "unknown_count": camera_manager.latest_counts.get("unknown_seat_belt", 0),
            "detection_status": "Active" if sb_enabled else "Inactive",
            "model_status": "Loaded" if sb_model_loaded else "Not Loaded",
            "training_status": "Pre-trained Weights Available" if sb_weights_exist else "Not Trained"
        },
        "mobile_phone_stats": {
            "phone_count": camera_manager.latest_counts.get("mobile_phone", 0),
            "no_phone_count": camera_manager.latest_counts.get("no_mobile_phone", 0),
            "unknown_count": camera_manager.latest_counts.get("unknown_mobile_phone", 0),
            "detection_status": "Active" if mp_enabled else "Inactive",
            "model_status": "Loaded" if mp_model_loaded else "Not Loaded",
            "training_status": "Pre-trained Weights Available" if mp_weights_exist else "Not Trained"
        },
        "traffic_signal_stats": {
            "red_count": camera_manager.latest_counts.get("traffic_red", 0),
            "yellow_count": camera_manager.latest_counts.get("traffic_yellow", 0),
            "green_count": camera_manager.latest_counts.get("traffic_green", 0),
            "unknown_count": camera_manager.latest_counts.get("traffic_unknown", 0),
            "detection_status": "Active" if ts_enabled else "Inactive",
            "model_status": "Loaded" if ts_model_loaded else "Not Loaded",
            "training_status": "Pre-trained Weights Available" if ts_weights_exist else "Not Trained"
        },
        "wrong_side_stats": {
            "wrong_side_count": camera_manager.latest_counts.get("wrong_side", 0),
            "correct_direction_count": camera_manager.latest_counts.get("correct_direction", 0),
            "unknown_count": camera_manager.latest_counts.get("wrong_side_unknown", 0),
            "detection_status": "Active" if ws_enabled else "Inactive",
            "model_status": "Loaded" if ws_model_loaded else "Not Loaded",
            "training_status": "Rule-based (No Model Required)"
        },
        "triple_riding_stats": {
            "single_rider_count": camera_manager.latest_counts.get("single_rider", 0),
            "double_riding_count": camera_manager.latest_counts.get("double_riding", 0),
            "triple_riding_count": camera_manager.latest_counts.get("triple_riding", 0),
            "unknown_count": camera_manager.latest_counts.get("triple_unknown", 0),
            "detection_status": "Active" if tr_enabled else "Inactive",
            "model_status": "Loaded" if tr_model_loaded else "Not Loaded",
            "association_status": "Active" if tr_enabled else "Inactive"
        }
    }

@router.get("/sources")
def get_camera_sources():
    """
    Lists supported camera sources.
    """
    return ["Webcam", "Video File", "IP Camera", "RTSP"]

@router.post("/connect")
def connect_camera(request: ConnectRequest):
    """
    Disconnects any active camera and establishes connection to the new source.
    """
    # Parse source string to integer if it represents a digit
    source = request.source
    if isinstance(source, str) and source.isdigit():
        source = int(source)

    success, msg = camera_manager.connect(source)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )
    return {"status": "success", "message": msg}

@router.post("/disconnect")
def disconnect_camera():
    """
    Disconnects the active camera.
    """
    camera_manager.disconnect()
    return {"status": "success", "message": "Camera disconnected successfully"}

@router.get("/frame")
def get_camera_frame():
    """
    Returns the single current JPEG image frame.
    """
    jpeg_bytes, _ = camera_manager.get_frame()
    if not jpeg_bytes:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Frame buffer empty"
        )
    return Response(content=jpeg_bytes, media_type="image/jpeg")

async def frame_generator():
    """
    Generates JPEG frames for MJPEG streaming.
    """
    logger.info("Starting MJPEG video stream generation.")
    try:
        while True:
            jpeg_bytes, _ = camera_manager.get_frame()
            if jpeg_bytes:
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n'
                )
            # Cap generator pace to the target FPS
            await asyncio.sleep(1.0 / camera_manager.target_fps)
    except asyncio.CancelledError:
        logger.info("MJPEG stream cancelled by client.")
    except Exception as e:
        logger.exception(f"Unexpected error in MJPEG generator: {e}")

@router.get("/stream")
def get_camera_stream():
    """
    MJPEG streaming endpoint suitable for html img tags.
    """
    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
