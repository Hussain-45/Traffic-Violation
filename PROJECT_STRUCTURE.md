# Project Structure - Layout Documentation

The Traffic Violation AI Project follows a standardized, modular design to separate data pipelines, models, service layers, and frontend interfaces.

```text
Traffic-Violation-AI/
├── backend/              # FastAPI application (Python 3.10)
│   ├── app/
│   │   ├── api/          # Route handlers (endpoints)
│   │   ├── core/         # Core config and security
│   │   ├── models/       # DB models (ORM schemas)
│   │   ├── schemas/      # Pydantic validation schemas
│   │   └── services/     # Model inference & logging logic
│   └── requirements.txt
├── frontend/             # Next.js / React application (TypeScript, Tailwind)
│   └── src/
│       ├── components/   # Reusable UI widgets
│       ├── pages/        # Router pages
│       ├── styles/       # CSS/Tailwind configs
│       └── utils/        # API clients
├── datasets/             # All datasets organized by model type
│   ├── detection/        # Object detection datasets (YOLO / Pascal XML)
│   │   ├── helmet/
│   │   ├── seat_belt/
│   │   ├── number_plate/
│   │   ├── traffic_light/
│   │   └── computer_vision/
│   ├── classification/   # Driver action classification
│   │   └── driver_behavior/
│   ├── ocr/              # Character recognition
│   │   └── number_plate_ocr/
│   └── custom/           # Custom user-provided files
├── models/               # Model weights and experiments
│   ├── pretrained/       # Official YOLO weights (e.g. yolov8n.pt)
│   ├── trained/          # Custom fine-tuned weights
│   ├── experiments/      # Training checkpoint logs
│   └── exports/          # Exported formats (ONNX, TensorRT, TFLite)
├── uploads/              # Input media directory
│   ├── images/
│   ├── videos/
│   └── violations/
├── reports/              # Output violation reports
│   ├── pdf/
│   ├── csv/
│   └── excel/
├── database/             # SQLite / PostgreSQL schema files
├── docs/                 # General documentation & workflow specs
├── tests/                # Unit & integration test suites
├── notebooks/            # Research & prototyping notebooks
├── configs/              # Hyperparameters & model configurations
├── logs/                 # System and model log files
├── scripts/              # Helper utility scripts
└── README.md             # Overview
```

### Folder Purposes

- **`backend/`**: Serves model predictions, logs detections to database, and exposes REST endpoints.
- **`frontend/`**: Displays livestream detection views, violation history logs, analytics charts, and report generation controls.
- **`datasets/`**: Contains raw and split data files. Kept clean and modular for separate training runs.
- **`models/`**: Standard weights storage directory to avoid scattering `.pt` files.
- **`uploads/`**: Serves as a staging ground for raw inputs processed by the backend.
- **`reports/`**: Exports generated PDF summaries of violations for traffic authority usage.