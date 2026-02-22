# AEGIS Model Weights Directory

This directory contains YOLO model weights for the AEGIS detection system.

---

## 📁 Directory Structure

```
models/
├── README.md           # This file
└── best_model.pt       # Your custom trained model (place here after training)
```

---

## 🎯 Model Loading Priority

The system loads models in this order:

1. **Custom Model** (if exists): `models/best_model.pt`
   - Your trained military detection model
   - Detects 20 military-specific classes
   - Highest priority

2. **Fallback Model** (auto-downloaded): `yolo11n.pt`
   - COCO pretrained model (80 general classes)
   - Downloaded automatically by Ultralytics on first run
   - Used when custom model is not found

---

## 🚀 Deploying Your Trained Model

After training your custom model (see `TRAINING_GUIDE.md`):

```bash
# Copy best weights from training run
cp runs/military/aegis_military_v1/weights/best.pt models/best_model.pt

# Restart the server
PORT=5001 python app.py
```

The system will automatically detect and load your custom model.

---

## 📊 Model Information

### Current Model (COCO Pretrained - Fallback)

- **Model:** YOLO11n (nano)
- **Classes:** 80 (COCO dataset)
- **Size:** ~6 MB
- **Speed:** ~20-50ms per image (GPU), ~200-500ms (CPU)
- **Accuracy:** Good for general objects, limited for military equipment

**Detected Classes Include:**
- Vehicles: car, truck, bus, motorcycle, bicycle, airplane, boat, train
- People: person
- Common objects: backpack, handbag, bottle, etc.

### Custom Military Model (After Training)

- **Model:** YOLO11n fine-tuned
- **Classes:** 20 (military-specific)
- **Size:** ~6-8 MB
- **Speed:** Similar to base model
- **Accuracy:** Optimized for military equipment detection

**Military Classes:**
1. tank
2. armored_vehicle
3. missile_launcher
4. artillery
5. fighter_jet
6. attack_helicopter
7. warship
8. submarine
9. rocket_launcher
10. anti_aircraft_gun
11. military_truck
12. patrol_boat
13. military_helicopter
14. radar_station
15. recon_drone
16. combat_drone
17. military_personnel
18. bunker
19. runway
20. helipad

---

## 🔄 Model Versions

You can maintain multiple model versions:

```bash
models/
├── best_model.pt              # Current production model
├── best_model_v1_backup.pt    # Backup of v1
├── best_model_v2_testing.pt   # Testing new version
└── README.md
```

To switch models, rename the file you want to use to `best_model.pt`.

---

## 📈 Model Performance Metrics

After training, check your model's performance:

```bash
python scripts/evaluate_model.py \
    --weights models/best_model.pt \
    --data datasets/military/military.yaml
```

**Target Metrics:**
- mAP@50: > 0.65
- mAP@50-95: > 0.45
- Inference time: < 100ms per image

---

## 🛠️ Model Optimization

### For Faster Inference

**Export to ONNX:**
```bash
yolo export model=models/best_model.pt format=onnx
```

**Export to TensorRT (NVIDIA GPUs):**
```bash
yolo export model=models/best_model.pt format=engine device=0
```

### For Smaller File Size

**Use INT8 Quantization:**
```bash
yolo export model=models/best_model.pt format=onnx int8=True
```

---

## 🔍 Verifying Model

Check which model is loaded:

```bash
# Start server and check logs
python app.py

# Look for:
# [INFO] Loading custom weights: models/best_model.pt
# OR
# [WARNING] Falling back to 'yolo11n.pt' (COCO pre-trained)
```

Or check via API:
```bash
curl http://localhost:5001/health
```

---

## 📚 Training Your Own Model

See `TRAINING_GUIDE.md` for complete instructions on:
- Dataset acquisition
- Dataset preparation
- Model training
- Model evaluation
- Model deployment

---

## ⚠️ Important Notes

1. **Model Size:** Keep models under 100MB for fast loading
2. **Compatibility:** Use YOLO11 or YOLOv8 format (.pt files)
3. **Class Names:** Must match exactly with `config.py` definitions
4. **Backup:** Always keep a backup of working models
5. **Version Control:** Consider using Git LFS for model versioning

---

## 🆘 Troubleshooting

### Model Not Loading

**Check file exists:**
```bash
ls -lh models/best_model.pt
```

**Verify file is valid:**
```bash
python -c "from ultralytics import YOLO; model = YOLO('models/best_model.pt'); print('Model loaded successfully')"
```

### Wrong Classes Detected

- Verify model was trained on correct dataset
- Check `config.py` class definitions match training
- Re-run evaluation script

### Poor Detection Performance

- Model may need more training epochs
- Dataset may need more examples
- Try larger model (yolo11s.pt or yolo11m.pt)

---

**AEGIS v2.0 — MODEL WEIGHTS — CLASSIFIED**
