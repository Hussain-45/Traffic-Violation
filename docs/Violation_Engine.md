# Violation Detection Engine

This document describes the business logic and algorithms used to detect various categories of traffic violations.

## Monitored Violations

### 1. Helmet Detection
* **Logic**: Cascaded YOLOv8. First detects motorcycles, then detects riders, and finally classifies if a helmet is present on the rider's head.
* **Alert Trigger**: Motorcycle rider detected without a helmet.

### 2. Seat Belt Detection
* **Logic**: Bounding box / instance segmentation model scans the windshield area of the vehicle to detect driver and passenger seatbelt presence.
* **Alert Trigger**: Driver/passenger active without a visible seatbelt strap.

### 3. Mobile Phone Detection
* **Logic**: Bounding box model scans the driver's hand/head region to identify distraction activities.
* **Alert Trigger**: Driver holding a mobile device near their face/steering wheel.

### 4. Wrong Side Detection
* **Logic**: Compares the direction vector of a tracked vehicle (trajectory track IDs) against the defined traffic direction vector.
* **Alert Trigger**: Vehicle heading in the opposite direction.

### 5. Signal Crossing (Red Light Violation)
* **Logic**: Defines virtual line overlays (zones) over the stop line. Triggers if a vehicle crossing event occurs while the traffic light classification status is Red.
* **Alert Trigger**: Bounding box crossing the stop line during Red phase.

### 6. Triple Riding
* **Logic**: Bounding box classifier counts the number of riders on a detected motorcycle.
* **Alert Trigger**: Bounding box intersections showing more than 2 people on a single motorcycle.

### 7. Overspeed Detection
* **Logic**: Measures the pixel travel time across virtual calibration lines. Converts pixel distance to speed in km/h based on ground calibration.
* **Alert Trigger**: Vehicle speed exceeds the zone speed limit.

### 8. Evidence Capture
* **Logic**: Automated crop generator crops the full frame (context), vehicle frame, driver crop, and license plate crop. Saves them to `uploads/evidence/`.

### 9. Email Automation
* **Logic**: Background worker grabs the evidence files, generates an HTML report, and sends an SMTP email to local traffic authorities.
