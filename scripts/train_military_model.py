#!/usr/bin/env python3
"""
AEGIS Military Model Training Script
Trains YOLO11n on military vehicle dataset (CPU optimized)
"""

import os
import sys
from pathlib import Path
from ultralytics import YOLO
import torch

def main():
    print("=" * 60)
    print("AEGIS MILITARY MODEL TRAINING")
    print("=" * 60)
    
    # Check device
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"\n[INFO] Training device: {device.upper()}")
    
    if device == 'cpu':
        print("[WARNING] Training on CPU - this will take 8-15 hours")
        print("[INFO] Consider using Google Colab with GPU for faster training")
    
    # Paths
    project_root = Path(__file__).parent.parent
    data_yaml = project_root / "military-vehicle.v6i.yolov8" / "data.yaml"
    base_model = project_root / "yolo11n.pt"
    
    print(f"\n[INFO] Dataset config: {data_yaml}")
    print(f"[INFO] Base model: {base_model}")
    
    if not data_yaml.exists():
        print(f"[ERROR] Dataset config not found: {data_yaml}")
        sys.exit(1)
    
    if not base_model.exists():
        print(f"[ERROR] Base model not found: {base_model}")
        sys.exit(1)
    
    # Load model
    print("\n[INFO] Loading YOLO11n base model...")
    model = YOLO(str(base_model))
    
    # Training parameters (CPU optimized)
    print("\n[INFO] Starting training with CPU-optimized settings...")
    print("  - Epochs: 30")
    print("  - Image size: 416x416")
    print("  - Batch size: 4")
    print("  - Workers: 2")
    print("  - Device: CPU")
    
    # Train
    results = model.train(
        data=str(data_yaml),
        epochs=30,              # Reduced for CPU
        imgsz=416,              # Reduced for CPU
        batch=4,                # Small batch for CPU
        device=device,
        workers=2,              # Reduced workers for CPU
        patience=10,            # Early stopping
        save=True,
        save_period=5,          # Save checkpoint every 5 epochs
        project=str(project_root / "runs" / "train"),
        name="military_model",
        exist_ok=True,
        pretrained=True,
        optimizer='Adam',
        verbose=True,
        seed=42,
        deterministic=True,
        single_cls=True,        # Single class dataset
        rect=False,
        cos_lr=True,            # Cosine learning rate
        close_mosaic=10,        # Disable mosaic last 10 epochs
        amp=False,              # Disable AMP for CPU
        fraction=1.0,           # Use full dataset
        profile=False,
        freeze=None,
        lr0=0.001,              # Lower learning rate for CPU
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        box=7.5,
        cls=0.5,
        dfl=1.5,
        pose=12.0,
        kobj=1.0,
        label_smoothing=0.0,
        nbs=64,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=0.0,
        translate=0.1,
        scale=0.5,
        shear=0.0,
        perspective=0.0,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.0,
        copy_paste=0.0
    )
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)
    
    # Find best model
    best_model_path = project_root / "runs" / "train" / "military_model" / "weights" / "best.pt"
    
    if best_model_path.exists():
        print(f"\n[SUCCESS] Best model saved at: {best_model_path}")
        
        # Copy to models directory
        models_dir = project_root / "models"
        models_dir.mkdir(exist_ok=True)
        
        target_path = models_dir / "best_model.pt"
        
        import shutil
        shutil.copy(best_model_path, target_path)
        
        print(f"[SUCCESS] Model copied to: {target_path}")
        print("\n[NEXT STEPS]")
        print("1. Restart the Flask server")
        print("2. The system will automatically use the new model")
        print("3. Test with tank images - should detect as 'military-vehicle'")
    else:
        print(f"\n[ERROR] Best model not found at: {best_model_path}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
