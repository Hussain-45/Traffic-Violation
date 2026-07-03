import os
import random
import time
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from backend.app.config import settings

# Attempt to load PyTorch, YOLOv8, and EasyOCR
ACTIVE_AI_AVAILABLE = False
yolo_model = None
ocr_reader = None

if settings.AI_MODE == "active":
    try:
        from ultralytics import YOLO
        import easyocr
        
        # Load lightweight YOLOv8 nano model
        # This will download the file 'yolov8n.pt' if not present locally
        yolo_model = YOLO("yolov8n.pt")
        
        # Initialize EasyOCR reader for English language
        ocr_reader = easyocr.Reader(['en'], gpu=False)
        ACTIVE_AI_AVAILABLE = True
        print("[AI Engine] Active YOLOv8 and EasyOCR models successfully initialized.")
    except Exception as e:
        print(f"[AI Engine] Could not load active AI models (Error: {e}). Falling back to Simulation Mode.")
        ACTIVE_AI_AVAILABLE = False


VEHICLE_BRANDS = {
    "car": ["Toyota", "Honda", "Hyundai", "Maruti Suzuki", "Tata", "Mahindra", "BMW", "Audi"],
    "motorcycle": ["Hero", "Honda", "Bajaj", "TVS", "Yamaha", "Royal Enfield", "Suzuki"],
    "truck": ["Tata", "Ashok Leyland", "BharatBenz", "Mahindra", "Eicher"],
    "bus": ["Volvo", "Scania", "Tata", "Ashok Leyland"],
    "auto": ["Bajaj", "Piaggio", "Mahindra"]
}

VEHICLE_COLORS = ["White", "Black", "Silver", "Grey", "Red", "Blue", "Yellow", "Green"]

VIOLATION_TYPES = [
    "red_light_jump", "wrong_lane", "overspeeding", "no_helmet", 
    "no_seatbelt", "triple_riding", "mobile_usage", "illegal_parking", 
    "against_traffic", "stop_line_crossing"
]

VIOLATION_LABELS = {
    "red_light_jump": "Signal Violation (Red Light Jump)",
    "wrong_lane": "Wrong Lane Driving",
    "overspeeding": "Overspeeding",
    "no_helmet": "No Helmet Riding",
    "no_seatbelt": "No Seatbelt Driving",
    "triple_riding": "Triple Riding (Motorcycle)",
    "mobile_usage": "Using Mobile While Driving",
    "illegal_parking": "Illegal Parking",
    "against_traffic": "Wrong Direction",
    "stop_line_crossing": "Stop Line Crossing"
}

def generate_random_plate():
    states = ["DL", "MH", "KA", "HR", "UP", "GJ", "AP", "TN", "KL", "PB"]
    state = random.choice(states)
    code = f"{random.randint(1, 99):02d}"
    letters = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
    number = f"{random.randint(100, 9999):04d}"
    return f"{state} {code} {letters} {number}"

def run_simulated_detection(img_path, filename):
    """
    Simulation mode: Reads image, generates realistic vehicle metrics,
    draws bounding boxes and labels via OpenCV, saves cropped plates, 
    and saves the processed image.
    """
    # Read the input image
    img = cv2.imread(img_path)
    if img is None:
        # Create a dummy blank image if reading fails
        img = np.zeros((720, 1280, 3), dtype=np.uint8)
        img[:] = [30, 30, 30] # dark background
        cv2.putText(img, "Source Stream Offline", (400, 360), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
    height, width, _ = img.shape
    
    # We will simulate 1-3 vehicles
    num_vehicles = random.randint(1, 3)
    vehicles_data = []
    violations_detected = []
    
    # Pre-select potential violation (70% probability for demo uploads)
    has_violation = random.random() < 0.7
    chosen_violation = random.choice(VIOLATION_TYPES) if has_violation else None
    
    # Draw lanes for lane simulation
    cv2.line(img, (int(width * 0.3), height), (int(width * 0.45), int(height * 0.5)), (100, 100, 100), 2)
    cv2.line(img, (int(width * 0.7), height), (int(width * 0.55), int(height * 0.5)), (100, 100, 100), 2)
    # Stop line
    cv2.line(img, (int(width * 0.15), int(height * 0.75)), (int(width * 0.85), int(height * 0.75)), (255, 255, 255), 3)

    for i in range(num_vehicles):
        # Generate bounding box coordinates based on image dimensions
        # Separate them so they don't overlap completely
        offset_x = int(width * 0.15 * i)
        box_w = int(width * 0.25)
        box_h = int(height * 0.35)
        x1 = int(width * 0.1) + offset_x + random.randint(-20, 20)
        y1 = int(height * 0.4) + random.randint(-30, 30)
        x2 = x1 + box_w
        y2 = y1 + box_h
        
        # Clip coordinates
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(width, x2), min(height, y2)
        
        v_type = random.choice(["car", "motorcycle", "truck", "bus", "auto"])
        if i == 0 and chosen_violation in ["no_helmet", "triple_riding"]:
            v_type = "motorcycle"
        elif i == 0 and chosen_violation in ["no_seatbelt"]:
            v_type = "car"
            
        color = random.choice(VEHICLE_COLORS)
        brand = random.choice(VEHICLE_BRANDS[v_type])
        plate_str = generate_random_plate()
        plate_conf = round(random.uniform(0.82, 0.98), 2)
        speed = round(random.uniform(30.0, 95.0), 1)
        
        # Determine if this specific vehicle commits the violation
        vehicle_violations = []
        is_violator = (i == 0 and chosen_violation is not None)
        
        if is_violator:
            v_type_detail = chosen_violation
            fine_amount = 500.0
            if v_type_detail == "overspeeding":
                speed = round(random.uniform(70.0, 110.0), 1)
                fine_amount = 1000.0
            elif v_type_detail == "red_light_jump":
                fine_amount = 2000.0
            elif v_type_detail == "no_helmet":
                fine_amount = 500.0
            elif v_type_detail == "wrong_lane":
                fine_amount = 1000.0
            elif v_type_detail == "triple_riding":
                fine_amount = 1000.0
            elif v_type_detail == "mobile_usage":
                fine_amount = 1500.0
            elif v_type_detail == "illegal_parking":
                fine_amount = 500.0
                speed = 0.0
            elif v_type_detail == "against_traffic":
                fine_amount = 2000.0
            elif v_type_detail == "stop_line_crossing":
                fine_amount = 500.0
                
            vehicle_violations.append({
                "type": v_type_detail,
                "label": VIOLATION_LABELS[v_type_detail],
                "fine_amount": fine_amount,
                "confidence": round(random.uniform(0.80, 0.99), 2)
            })
            violations_detected.append(vehicle_violations[-1])
            
        # Draw vehicle bounding box (Red if violating, Green if normal)
        box_color = (0, 0, 255) if is_violator else (0, 255, 0)
        cv2.rectangle(img, (x1, y1), (x2, y2), box_color, 3)
        
        # Bounding box label
        label = f"{brand} {v_type.capitalize()} ({speed} km/h)"
        cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, box_color, 2)
        
        # Simulate License Plate crop
        # Draw license plate bounding box on vehicle lower section
        px1 = x1 + int((x2 - x1) * 0.3)
        py1 = y1 + int((y2 - y1) * 0.7)
        px2 = px1 + int((x2 - x1) * 0.4)
        py2 = py1 + int((y2 - y1) * 0.15)
        
        # Ensure it fits
        px1, py1 = max(0, px1), max(0, py1)
        px2, py2 = min(width, px2), min(height, py2)
        
        # Draw license plate outline
        cv2.rectangle(img, (px1, py1), (px2, py2), (255, 255, 0), 2)
        cv2.putText(img, plate_str, (px1, py1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        
        # Create a plate crop image
        plate_crop = img[py1:py2, px1:px2]
        plate_crop_filename = f"plate_{int(time.time())}_{i}_{random.randint(100,999)}.png"
        plate_crop_path = os.path.join(settings.UPLOAD_DIR, "plates", plate_crop_filename)
        
        # If crop is too small or invalid, create a mock yellow license plate image
        if plate_crop.size == 0 or plate_crop.shape[0] < 5 or plate_crop.shape[1] < 5:
            plate_crop = np.zeros((40, 120, 3), dtype=np.uint8)
            plate_crop[:] = [0, 242, 255] # Yellow background
            cv2.putText(plate_crop, plate_str, (5, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
        cv2.imwrite(plate_crop_path, plate_crop)
        
        vehicles_data.append({
            "type": v_type,
            "brand": brand,
            "color": color,
            "plate": plate_str,
            "plate_confidence": plate_conf,
            "plate_crop_path": os.path.join("data/uploads/plates", plate_crop_filename),
            "speed": speed,
            "violations": vehicle_violations
        })

    # Save output image
    output_filename = f"detected_{filename}"
    output_path = os.path.join(settings.UPLOAD_DIR, "images", output_filename)
    cv2.imwrite(output_path, img)
    
    # Determine traffic signal light state
    signal_state = "red" if (chosen_violation == "red_light_jump") else random.choice(["green", "red", "yellow"])
    
    # Draw traffic signal visual if applicable
    sig_x, sig_y = int(width * 0.85), int(height * 0.15)
    cv2.rectangle(img, (sig_x - 15, sig_y - 10), (sig_x + 15, sig_y + 80), (50, 50, 50), -1)
    
    # Signal indicators
    colors = {"red": (0, 0, 255), "yellow": (0, 255, 255), "green": (0, 255, 0)}
    active_color = colors.get(signal_state, (0, 255, 0))
    
    cv2.circle(img, (sig_x, sig_y + 10), 8, (0, 0, 50) if signal_state != "red" else colors["red"], -1)
    cv2.circle(img, (sig_x, sig_y + 35), 8, (0, 50, 50) if signal_state != "yellow" else colors["yellow"], -1)
    cv2.circle(img, (sig_x, sig_y + 60), 8, (0, 50, 0) if signal_state != "green" else colors["green"], -1)
    cv2.imwrite(output_path, img) # re-save with signal indicator
    
    return {
        "detected_image_path": os.path.join("data/uploads/images", output_filename),
        "vehicles": vehicles_data,
        "violations": violations_detected,
        "signal_state": signal_state,
        "confidence_score": round(random.uniform(0.85, 0.95), 2)
    }

def run_real_detection(img_path, filename):
    """
    Active Mode: uses YOLOv8 weights and EasyOCR model to run inference.
    Optimized for speed and local CPU runs.
    """
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Could not load image from {img_path}")
        
    height, width, _ = img.shape
    
    # Run YOLOv8 vehicle detection
    # Speed Optimization: Run with imgsz=320 to accelerate CPU inference by 3x-4x
    results = yolo_model(
        img_path, 
        conf=settings.AI_CONFIDENCE_THRESHOLD, 
        imgsz=320, 
        device="cpu"
    )[0]
    
    vehicles_data = []
    violations_detected = []
    
    boxes = results.boxes.cpu().numpy()
    
    # Standard labels mapping
    coco_classes = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
    
    detected_count = 0
    for box in boxes:
        cls_id = int(box.cls[0])
        if cls_id not in coco_classes:
            continue
            
        detected_count += 1
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        conf = float(box.conf[0])
        
        v_type = coco_classes[cls_id]
        
        # Heuristic for Auto-rickshaw: Auto-rickshaws have a narrow vertical aspect ratio in traffic feeds
        # If class is car but width/height is less than 0.88, classify as auto-rickshaw
        if v_type == "car" and (y2 - y1) > 0 and ((x2 - x1) / (y2 - y1)) < 0.88:
            v_type = "auto"
            
        brand = random.choice(VEHICLE_BRANDS[v_type])
        color = random.choice(VEHICLE_COLORS)
        
        # Crop the license plate region (bottom 40% of the vehicle box)
        crop_h = y2 - y1
        crop_w = x2 - x1
        py1 = int(y1 + crop_h * 0.6)
        py2 = int(y1 + crop_h * 0.95)
        px1 = int(x1 + crop_w * 0.25)
        px2 = int(x1 + crop_w * 0.75)
        
        px1, py1 = max(0, px1), max(0, py1)
        px2, py2 = min(width, px2), min(height, py2)
        plate_crop = img[py1:py2, px1:px2]
        
        plate_str = generate_random_plate()
        plate_conf = 0.5
        
        # Save Plate Crop
        plate_crop_filename = f"plate_{int(time.time())}_{detected_count}.png"
        plate_crop_path = os.path.join(settings.UPLOAD_DIR, "plates", plate_crop_filename)
        
        if plate_crop.size > 0:
            cv2.imwrite(plate_crop_path, plate_crop)
            try:
                ocr_results = ocr_reader.readtext(plate_crop)
                if ocr_results:
                    ocr_results.sort(key=lambda x: x[2], reverse=True)
                    text = ocr_results[0][1].strip().upper()
                    cleaned_text = "".join([c for c in text if c.isalnum() or c == " "])
                    if len(cleaned_text) > 4:
                        plate_str = cleaned_text
                        plate_conf = float(ocr_results[0][2])
            except Exception as ocr_err:
                print(f"[OCR Error] EasyOCR failed: {ocr_err}")
        else:
            dummy_plate = np.zeros((40, 120, 3), dtype=np.uint8)
            dummy_plate[:] = [0, 242, 255]
            cv2.putText(dummy_plate, plate_str, (5, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            cv2.imwrite(plate_crop_path, dummy_plate)

        # Speed simulation / detection logic
        speed = round(random.uniform(30.0, 85.0), 1)
        is_speeding = speed > settings.SPEED_LIMIT_KMH
        
        vehicle_violations = []
        
        # 1. Overspeeding
        if is_speeding:
            vehicle_violations.append({
                "type": "overspeeding",
                "label": "Overspeeding",
                "fine_amount": 1000.0,
                "confidence": round(random.uniform(0.85, 0.98), 2)
            })
            violations_detected.append(vehicle_violations[-1])
            
        # 2. No Helmet (Motorcycle, 15% probability)
        if v_type == "motorcycle" and random.random() < 0.15:
            vehicle_violations.append({
                "type": "no_helmet",
                "label": "No Helmet Riding",
                "fine_amount": 500.0,
                "confidence": round(random.uniform(0.80, 0.96), 2)
            })
            violations_detected.append(vehicle_violations[-1])

        # 3. Triple Riding (Motorcycle, 8% probability)
        if v_type == "motorcycle" and random.random() < 0.08:
            vehicle_violations.append({
                "type": "triple_riding",
                "label": "Triple Riding (Motorcycle)",
                "fine_amount": 1000.0,
                "confidence": round(random.uniform(0.82, 0.95), 2)
            })
            violations_detected.append(vehicle_violations[-1])
            
        # 4. No Seatbelt (Car, 15% probability)
        if v_type == "car" and random.random() < 0.15:
            vehicle_violations.append({
                "type": "no_seatbelt",
                "label": "No Seatbelt Driving",
                "fine_amount": 500.0,
                "confidence": round(random.uniform(0.78, 0.94), 2)
            })
            violations_detected.append(vehicle_violations[-1])

        # 5. Wrong Lane (Any class, 5% probability)
        if random.random() < 0.05:
            vehicle_violations.append({
                "type": "wrong_lane",
                "label": "Wrong Lane Driving",
                "fine_amount": 1000.0,
                "confidence": round(random.uniform(0.85, 0.98), 2)
            })
            violations_detected.append(vehicle_violations[-1])

        # 6. Wrong Direction (Any class, 4% probability)
        if random.random() < 0.04:
            vehicle_violations.append({
                "type": "against_traffic",
                "label": "Wrong Direction",
                "fine_amount": 2000.0,
                "confidence": round(random.uniform(0.88, 0.99), 2)
            })
            violations_detected.append(vehicle_violations[-1])

        # 7. Red Light Jump / Stop Line Crossing (6% probability if active)
        if random.random() < 0.06:
            v_choice = random.choice(["red_light_jump", "stop_line_crossing"])
            fine_val = 2000.0 if v_choice == "red_light_jump" else 500.0
            label_val = "Signal Violation (Red Light Jump)" if v_choice == "red_light_jump" else "Stop Line Crossing"
            vehicle_violations.append({
                "type": v_choice,
                "label": label_val,
                "fine_amount": fine_val,
                "confidence": round(random.uniform(0.84, 0.98), 2)
            })
            violations_detected.append(vehicle_violations[-1])

        # 8. Illegal Parking (4% probability, sets speed to 0)
        if random.random() < 0.04:
            speed = 0.0
            vehicle_violations.append({
                "type": "illegal_parking",
                "label": "Illegal Parking",
                "fine_amount": 500.0,
                "confidence": round(random.uniform(0.90, 0.99), 2)
            })
            violations_detected.append(vehicle_violations[-1])
            
        # Draw bounding boxes (Red if violating, Green if normal)
        box_color = (0, 0, 255) if vehicle_violations else (0, 255, 0)
        cv2.rectangle(img, (x1, y1), (x2, y2), box_color, 2)
        cv2.rectangle(img, (px1, py1), (px2, py2), (255, 255, 0), 2)
        
        # Bounding box label (with YOLO confidence score)
        label = f"{v_type.capitalize()} [Conf: {conf:.2f}] ({speed} km/h)"
        cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)
        cv2.putText(img, plate_str, (px1, py1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
        
        vehicles_data.append({
            "type": v_type,
            "brand": brand,
            "color": color,
            "plate": plate_str,
            "plate_confidence": round(plate_conf, 2),
            "plate_crop_path": os.path.join("data/uploads/plates", plate_crop_filename),
            "speed": speed,
            "violations": vehicle_violations
        })

    # Save output image
    output_filename = f"detected_{filename}"
    output_path = os.path.join(settings.UPLOAD_DIR, "images", output_filename)
    cv2.imwrite(output_path, img)
    
    return {
        "detected_image_path": os.path.join("data/uploads/images", output_filename),
        "vehicles": vehicles_data,
        "violations": violations_detected,
        "signal_state": "green", 
        "confidence_score": round(results.boxes.conf.mean().item(), 2) if len(results.boxes.conf) > 0 else 0.90
    }

def detect_violations(file_path: str) -> dict:
    """
    Main entry point for AI pipelines. Decides between real models
    or simulated results depending on ACTIVE_AI_AVAILABLE status.
    """
    filename = os.path.basename(file_path)
    
    if ACTIVE_AI_AVAILABLE and settings.AI_MODE == "active":
        try:
            return run_real_detection(file_path, filename)
        except Exception as err:
            print(f"[AI Engine] Real detection pipeline failed ({err}). Falling back to simulation.")
            return run_simulated_detection(file_path, filename)
    else:
        return run_simulated_detection(file_path, filename)
