#!/usr/bin/env python3
"""
DOTA Model Training Script
Trains YOLO11 on DOTA aerial object detection dataset
"""

import os
import sys
from pathlib import Path
from ultralytics import YOLO

def train_dota_model():
    """Train YOLO11 on DOTA dataset"""
    
    print("=" * 60)
    print("DOTA MODEL TRAINING")
    print("=" * 60)
    print()
    
    # Check if dataset exists
    data_yaml = Path("datasets/dota/data.yaml")
    if not data_yaml.exists():
        print("❌ ERROR: DOTA dataset not found!")
        print()
        print("Please download DOTA dataset first:")
        print("1. Run: python3 scripts/download_dota.py")
        print("2. Follow the instructions to download from Roboflow")
        print("3. Extract to: datasets/dota/")
        print()
        sys.exit(1)
    
    print(f"✓ Found dataset config: {data_yaml}")
    print()
    
    # Training parameters
    print("Training Configuration:")
    print("-" * 60)
    print(f"Model: yolo11n.pt (YOLO11 Nano)")
    print(f"Dataset: {data_yaml}")
    print(f"Epochs: 30 (recommended for M2 CPU)")
    print(f"Image Size: 640x640")
    print(f"Batch Size: 8 (optimized for CPU)")
    print(f"Device: CPU (Apple M2)")
    print(f"Estimated Time: 6-8 hours")
    print("-" * 60)
    print()
    
    # Confirm training
    response = input("Start training? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Training cancelled.")
        sys.exit(0)
    
    print()
    print("=" * 60)
    print("TRAINING STARTED")
    print("=" * 60)
    print()
    print("This will take approximately 6-8 hours on Apple M2 CPU.")
    print("You can monitor progress in the terminal.")
    print()
    print("Training outputs will be saved to:")
    print("  runs/dota/dota_aerial_v1/")
    print()
    print("Press Ctrl+C to stop training (not recommended)")
    print()
    print("=" * 60)
    print()
    
    # Load model
    model = YOLO("yolo11n.pt")
    
    # Train
    results = model.train(
        data=str(data_yaml),
        epochs=30,
        imgsz=640,
        batch=8,
        device="cpu",
        name="dota_aerial_v1",
        project="runs/dota",
        patience=10,
        save_period=5,
        lr0=0.01,
        lrf=0.01,
        warmup_epochs=3,
        cos_lr=True,
        augment=True,
        mosaic=1.0,
        mixup=0.1,
        degrees=15.0,
        flipud=0.5,
        fliplr=0.5,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4
    )
    
    print()
    print("=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)
    print()
    print("Model saved to:")
    print("  runs/dota/dota_aerial_v1/weights/best.pt")
    print()
    print("Next steps:")
    print("1. Evaluate model: python3 scripts/evaluate_dota_model.py")
    print("2. Deploy model: python3 scripts/deploy_dota_model.py")
    print()
    print("=" * 60)

if __name__ == "__main__":
    train_dota_model()
