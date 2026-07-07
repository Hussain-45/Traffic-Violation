# AI Pipeline Documentation

The Traffic Violation Detection AI Pipeline manages real-time frame capturing, object detection, vehicle tracking, license plate OCR, and violation log persistence.

```text
Camera Stream
     │
     ▼
Frame Capture  ──► Preprocessing ──► Vehicle Detection
                                            │
                                            ▼
Violation Engine ◄── Evidence Gen ◄── Vehicle Tracking
       │
       ▼
License Plate Detection ──► Plate OCR ──► Database Persistence
                                                │
                                                ▼
Dashboard ◄────────────────────────────── Email Alert Trigger
```

## Step-by-Step Processing Flow

1. **Camera**: Real-time RTSP/HTTP video input feeds.
2. **Frame Capture**: Frame grabbing using high-performance queues (OpenCV thread).
3. **Preprocessing**: Image resizing, colorspace conversions, and batched normalization.
4. **Vehicle Detection**: YOLOv8 model detects vehicles (cars, trucks, buses, motorcycles).
5. **Vehicle Tracking**: ByteTrack assigns stable track IDs across consecutive frames.
6. **Violation Engine**: Analyzes vehicle tracks against virtual lines (Speed limits, Red lights, Lane lines, Helmet compliance, Seat Belt compliance).
7. **Evidence Generator**: Crops high-resolution frames of the vehicle, the driver, and license plate area.
8. **Number Plate Detection**: Extracts the license plate bounding box from the vehicle crop.
9. **OCR**: easyocr transcribes the plate character sequence.
10. **Database**: Saves violation records in the SQL database.
11. **Email Service**: Send SMTP alerts to authorities with the evidence images attached.
12. **Dashboard**: Updates live stats over WebSockets.
