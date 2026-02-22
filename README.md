# AEGIS — Autonomous Enemy & Ground Intelligence System

> AI-powered military target and equipment detection platform  
> Built with YOLO11 · PyTorch · OpenCV · Flask · Chart.js

**Version 2.0** — Now with Live Camera, Intelligence Dashboard, and Custom Model Training

---

## 🎯 Features

### Core Detection
- ✅ **File Upload Detection** - Drag & drop or browse images
- ✅ **Live Camera Detection** - Real-time webcam capture and analysis
- ✅ **YOLO11 AI Model** - State-of-the-art object detection
- ✅ **Threat Assessment** - Automatic risk level classification
- ✅ **Annotated Results** - Bounding boxes with confidence scores
- ✅ **Detection Logging** - CSV event log with timestamps

### Intelligence Dashboard (NEW v2.0)
- ✅ **Summary Statistics** - Total scans, detections, critical threats
- ✅ **Threat Distribution** - Doughnut chart by threat level
- ✅ **Timeline Analysis** - 30-day detection trends
- ✅ **Top Classes Chart** - Most detected objects
- ✅ **Activity Heatmap** - 7×24 detection frequency grid
- ✅ **Confidence Analysis** - Score distribution histogram
- ✅ **Recent Detections Table** - Sortable log with 25 latest entries
- ✅ **Auto-refresh** - Updates every 30 seconds
- ✅ **Export Functions** - Download CSV or JSON data

### Model Training Pipeline (NEW v2.0)
- ✅ **Dataset Preparation** - Merge multiple YOLO datasets
- ✅ **Training Scripts** - Optimized hyperparameters
- ✅ **Model Evaluation** - Performance metrics and recommendations
- ✅ **20 Military Classes** - Tanks, aircraft, ships, drones, etc.
- ✅ **Transfer Learning** - Fine-tune from YOLO11n base

### UI Enhancements (NEW v2.0)
- ✅ **Improved Readability** - Larger fonts, better contrast
- ✅ **Wider Panels** - More space for content
- ✅ **Warning Symbols** - High-risk items marked with ⚠
- ✅ **Detection Counter** - Live count badge
- ✅ **Auto-scroll** - Smooth UX improvements

---

## Architecture Overview

```
Browser (upload image)
       │
       ▼ POST /detect (multipart)
  ┌──────────────────────────┐
  │      Flask (app.py)      │
  │  ┌─────────────────────┐ │
  │  │  detection.py       │ │  ← YOLO11 inference + OpenCV annotation
  │  │  alert.py           │ │  ← Threat level assessment
  │  │  logger.py          │ │  ← CSV event logging
  │  └─────────────────────┘ │
  └──────────────────────────┘
       │
       ▼ JSON { detections, threat, annotated_path }
  Browser (render bounding boxes, threat banner, log table)
```

---

## Quick Start

### 1. Prerequisites

- Python 3.10 or later
- `pip` and `venv`
- *(Optional)* NVIDIA GPU + CUDA for accelerated inference

### 2. Clone / download

```bash
git clone <repo-url> military_detection_system
cd military_detection_system
```

### 3. Create a virtual environment

```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> **GPU support**: replace the `torch` line in `requirements.txt` with the
> appropriate CUDA wheel from https://pytorch.org/get-started/locally/

### 5. Run

```bash
python app.py
```

Then open:
- **Detection Page:** http://localhost:5001
- **Intelligence Dashboard:** http://localhost:5001/dashboard

---

## 📊 Pages

### Detection Page (`/`)
Upload images or use live camera to detect objects and assess threats.

**Features:**
- File upload or camera capture
- Real-time detection with YOLO11
- Threat level assessment (CRITICAL, HIGH, ELEVATED, LOW, CLEAR)
- Annotated images with bounding boxes
- Detection list with confidence scores
- Session history log

### Intelligence Dashboard (`/dashboard`)
Comprehensive analytics and trend visualization.

**Features:**
- Summary statistics cards
- Threat distribution chart
- 30-day timeline
- Top detected classes
- Activity heatmap (day × hour)
- Confidence distribution
- Sortable recent detections table
- CSV/JSON export

---

## API Reference

| Endpoint  | Method | Description |
|-----------|--------|-------------|
| `/`       | GET    | Serve detection page |
| `/dashboard` | GET | Serve intelligence dashboard |
| `/detect` | POST   | Accept image upload, return detections JSON |
| `/logs`   | GET    | Return 50 most recent detection log rows |
| `/api/dashboard-data` | GET | Return analytics data JSON |
| `/api/export-csv` | GET | Download full detection log CSV |
| `/health` | GET    | System health / readiness probe |

### POST /detect — request

```
Content-Type: multipart/form-data
Body field:   image   (image file)
```

### POST /detect — response

```jsonc
{
  "success": true,
  "detections": [
    {
      "id": 0,
      "class_name": "truck",
      "confidence": 0.891,
      "risk_level": "high",
      "box": { "x1": 120, "y1": 80, "x2": 340, "y2": 220,
               "width": 220, "height": 140, "cx": 230, "cy": 150 }
    }
  ],
  "threat": {
    "threat_level": "HIGH",
    "label": "HIGH ALERT",
    "description": "...",
    "color": "#ff6d00",
    "icon": "⚠",
    "high_risk_hits": ["truck"],
    "stats": {
      "total": 3,
      "high_risk": 1,
      "medium_risk": 1,
      "low_risk": 1,
      "avg_confidence": 0.763,
      "max_confidence": 0.891,
      "class_counts": { "truck": 1, "person": 2 }
    }
  },
  "annotated_path": "/static/uploads/annotated_abc123.jpg",
  "inference_ms": 42.5,
  "image_size": { "width": 1280, "height": 720 },
  "original_path": "/static/uploads/abc123_upload.jpg"
}
```

---

## 🎓 Training Custom Military Model

See **[TRAINING_GUIDE.md](TRAINING_GUIDE.md)** for complete instructions.

### Quick Overview

1. **Get Dataset** (see [DATASET_SOURCES.md](DATASET_SOURCES.md))
   - Download from Roboflow (fastest)
   - Or use DOTA v2.0 + xView + VEDAI

2. **Prepare Dataset**
   ```bash
   python scripts/prepare_dataset.py \
       --sources dota_yolo/ vedai_yolo/ \
       --output datasets/military/ \
       --split 0.8 0.1 0.1
   ```

3. **Train Model**
   ```bash
   yolo detect train \
       data=datasets/military/military.yaml \
       model=yolo11n.pt \
       epochs=100 \
       imgsz=640 \
       batch=16 \
       device=0 \
       name=aegis_military_v1 \
       project=runs/military
   ```

4. **Evaluate Model**
   ```bash
   python scripts/evaluate_model.py \
       --weights runs/military/aegis_military_v1/weights/best.pt \
       --data datasets/military/military.yaml
   ```

5. **Deploy Model**
   ```bash
   cp runs/military/aegis_military_v1/weights/best.pt models/best_model.pt
   python app.py  # Restart server
   ```

### Military Classes (20 total)

The custom model detects these military-specific classes:

- **Heavy Armor:** tank, armored_vehicle, artillery
- **Missiles:** missile_launcher, rocket_launcher, anti_aircraft_gun
- **Aircraft:** fighter_jet, attack_helicopter, military_helicopter
- **Naval:** warship, submarine, patrol_boat
- **Drones:** combat_drone, recon_drone
- **Support:** military_truck, radar_station, bunker
- **Infrastructure:** runway, helipad
- **Personnel:** military_personnel

---

## Configuration (`config.py`)

| Variable           | Default          | Description |
|--------------------|------------------|-------------|
| `MODEL_PATH`       | `models/best_model.pt` | Custom weights path |
| `YOLO_FALLBACK`    | `yolo11n.pt`     | Official fallback weights |
| `CONFIDENCE_THRESH`| `0.25`           | Min detection confidence |
| `IOU_THRESH`       | `0.45`           | NMS IoU threshold |
| `HIGH_RISK_CLASSES`| see config.py    | Classes triggering CRITICAL/HIGH alert |
| `DEVICE`           | `""`             | `""` = auto, `"cpu"`, `"cuda:0"` |
| `PORT`             | `5000`           | Flask server port |

---

## Project Structure

```
military_detection_system/
├── app.py                      # Flask app, routes, model loader
├── config.py                   # Configuration constants
├── requirements.txt            # Python dependencies
│
├── models/
│   ├── README.md               # Model deployment guide
│   └── best_model.pt           # ← Your trained model (after training)
│
├── services/
│   ├── __init__.py
│   ├── detection.py            # YOLO inference + OpenCV annotation
│   ├── alert.py                # Threat level assessment
│   ├── logger.py               # CSV event logger
│   └── analytics.py            # Dashboard analytics computation
│
├── static/
│   ├── css/
│   │   ├── style.css           # Main tactical dark HUD stylesheet
│   │   └── dashboard.css       # Dashboard-specific styles
│   ├── js/
│   │   ├── main.js             # Detection page controller
│   │   └── dashboard.js        # Dashboard controller with Chart.js
│   └── uploads/                # Saved originals + annotated images
│
├── templates/
│   ├── index.html              # Detection page
│   └── dashboard.html          # Intelligence dashboard
│
├── scripts/
│   ├── prepare_dataset.py      # Dataset merging and preparation
│   └── evaluate_model.py       # Model evaluation and analysis
│
├── datasets/
│   └── military/
│       ├── military.yaml       # YOLO training configuration
│       ├── images/             # Train/val/test images
│       └── labels/             # Train/val/test labels
│
├── logs/
│   └── detections.csv          # Auto-created detection event log
│
├── runs/                       # Training outputs (created during training)
│   └── military/
│       └── aegis_military_v1/
│           └── weights/
│               └── best.pt     # Trained model weights
│
├── TRAINING_GUIDE.md           # Complete training walkthrough
├── DATASET_SOURCES.md          # Dataset acquisition reference
├── UPGRADE_SUMMARY.md          # v2.0 upgrade documentation
└── README.md                   # This file
```

---

## Customising Threat Classes

Edit `HIGH_RISK_CLASSES` and `MEDIUM_RISK_CLASSES` in `config.py`:

```python
HIGH_RISK_CLASSES = {
    "tank", "missile", "gun", "rifle", "artillery",
    "armored_vehicle", "fighter_jet", "drone", "warship",
    # Add your model's class names here
}
```

The class names must match exactly what your YOLO model outputs in `result.names`.

---

## Logs

Detection events are appended to `logs/detections.csv` with columns:

```
timestamp, image_filename, threat_level, total_detections,
high_risk_count, class_name, confidence, risk_level,
box_x1, box_y1, box_x2, box_y2, inference_ms
```

---

## License

For authorised personnel only. Intended for legitimate surveillance,
security research, and defensive applications. The authors are not
responsible for misuse.

## Customising Threat Classes

Edit `HIGH_RISK_CLASSES` and `MEDIUM_RISK_CLASSES` in `config.py`:

```python
HIGH_RISK_CLASSES = {
    # Heavy armor & artillery
    "tank", "armored_vehicle", "missile_launcher", "artillery",
    "rocket_launcher", "anti_aircraft_gun",
    # Airborne threats
    "fighter_jet", "attack_helicopter", "combat_drone",
    # Naval threats
    "warship", "submarine",
    # Add your model's class names here
}
```

The class names must match exactly what your YOLO model outputs in `result.names`.

---

## 📈 Performance

### Current Model (COCO Pretrained)
- **Inference:** 20-50ms per image (GPU), 200-500ms (CPU)
- **Classes:** 80 general objects
- **Accuracy:** Good for vehicles, people, common objects

### Custom Military Model (After Training)
- **Inference:** Similar to base model
- **Classes:** 20 military-specific
- **Accuracy:** Optimized for military equipment (mAP@50 > 0.65)

---

## 📚 Documentation

- **[TRAINING_GUIDE.md](TRAINING_GUIDE.md)** - Complete model training guide
- **[DATASET_SOURCES.md](DATASET_SOURCES.md)** - Where to get training data
- **[UPGRADE_SUMMARY.md](UPGRADE_SUMMARY.md)** - v2.0 upgrade details
- **[models/README.md](models/README.md)** - Model deployment guide

---

## 🔧 Configuration

All settings in `config.py`:

| Variable           | Default          | Description |
|--------------------|------------------|-------------|
| `MODEL_PATH`       | `models/best_model.pt` | Custom weights path |
| `YOLO_FALLBACK`    | `yolo11n.pt`     | Official fallback weights |
| `CONFIDENCE_THRESH`| `0.25`           | Min detection confidence |
| `IOU_THRESH`       | `0.45`           | NMS IoU threshold |
| `HIGH_RISK_CLASSES`| see config.py    | Classes triggering CRITICAL/HIGH alert |
| `DEVICE`           | `""`             | `""` = auto, `"cpu"`, `"cuda:0"` |
| `PORT`             | `5000`           | Flask server port |

---

## 🐛 Troubleshooting

### Port 5000 Already in Use (macOS)

macOS AirPlay Receiver uses port 5000. Use a different port:

```bash
PORT=5001 python app.py
```

Or disable AirPlay Receiver in System Settings.

### Model Not Loading

Check logs for:
```
[INFO] Loading custom weights: models/best_model.pt
```

Or:
```
[WARNING] Falling back to 'yolo11n.pt' (COCO pre-trained)
```

### Poor Detection Performance

1. Lower confidence threshold in `config.py`
2. Train custom model on military data
3. Use GPU for faster inference
4. Increase image resolution

### Camera Not Working

- Check browser permissions
- Use HTTPS or localhost
- Try different browser (Chrome recommended)

---

## 🚀 Deployment

### Production Considerations

1. **Use Production WSGI Server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5001 app:app
   ```

2. **Enable HTTPS:**
   - Use nginx reverse proxy
   - Get SSL certificate (Let's Encrypt)

3. **Optimize Model:**
   - Export to ONNX or TensorRT
   - Use quantization for smaller size

4. **Security:**
   - Change `SECRET_KEY` in production
   - Add authentication
   - Rate limiting
   - Input validation

---

## 📝 Logs

Detection events are appended to `logs/detections.csv` with columns:

```
timestamp, image_filename, threat_level, total_detections,
high_risk_count, class_name, confidence, risk_level,
box_x1, box_y1, box_x2, box_y2, inference_ms
```

View in dashboard or export via `/api/export-csv`.

---

## 🎨 UI Theme

Tactical dark military HUD aesthetic:
- Background: `#050a07` (dark green-black)
- Accent: `#00ff6e` (bright green)
- Threat colors: Red, Orange, Yellow, Green, Cyan
- Fonts: Orbitron (display), Rajdhani (UI), Share Tech Mono (data)

---

## 🤝 Contributing

This is a demonstration project for educational purposes. For production use:
- Add comprehensive testing
- Implement authentication
- Add rate limiting
- Enhance error handling
- Add model versioning

---

## ⚖️ License

For authorised personnel only. Intended for legitimate surveillance,
security research, and defensive applications. The authors are not
responsible for misuse.

---

## 🙏 Acknowledgments

- **YOLO11** by Ultralytics
- **Chart.js** for dashboard visualizations
- **OpenCV** for image processing
- **Flask** for web framework

---

**AEGIS v2.0 — CLASSIFIED SYSTEM — AUTHORISED PERSONNEL ONLY**

Built with ❤️ for defense and security applications.
