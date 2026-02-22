#!/usr/bin/env python3
"""
DOTA Model Evaluation Script
Evaluates trained DOTA model performance
"""

import os
import sys
from pathlib import Path
from ultralytics import YOLO

def evaluate_dota_model():
    """Evaluate DOTA model on test set"""
    
    print("=" * 60)
    print("DOTA MODEL EVALUATION")
    print("=" * 60)
    print()
    
    # Check if model exists
    model_path = Path("runs/dota/dota_aerial_v1/weights/best.pt")
    if not model_path.exists():
        print("❌ ERROR: Trained model not found!")
        print()
        print("Please train the model first:")
        print("  python3 scripts/train_dota_model.py")
        print()
        sys.exit(1)
    
    # Check if dataset exists
    data_yaml = Path("datasets/dota/data.yaml")
    if not data_yaml.exists():
        print("❌ ERROR: DOTA dataset not found!")
        print()
        sys.exit(1)
    
    print(f"✓ Found model: {model_path}")
    print(f"✓ Found dataset: {data_yaml}")
    print()
    
    # Load model
    print("Loading model...")
    model = YOLO(str(model_path))
    
    # Evaluate
    print()
    print("Running evaluation on test set...")
    print("This may take 5-10 minutes...")
    print()
    
    results = model.val(
        data=str(data_yaml),
        split="test",
        imgsz=640,
        batch=8,
        device="cpu"
    )
    
    print()
    print("=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    print()
    print(f"mAP@50:    {results.box.map50:.3f}")
    print(f"mAP@50-95: {results.box.map:.3f}")
    print(f"Precision: {results.box.mp:.3f}")
    print(f"Recall:    {results.box.mr:.3f}")
    print()
    
    # Performance interpretation
    map50 = results.box.map50
    if map50 >= 0.7:
        status = "✅ EXCELLENT"
        comment = "Model performs very well on aerial imagery"
    elif map50 >= 0.5:
        status = "✓ GOOD"
        comment = "Model performs adequately, consider more training"
    else:
        status = "⚠ NEEDS IMPROVEMENT"
        comment = "Model needs more training or better data"
    
    print(f"Status: {status}")
    print(f"Comment: {comment}")
    print()
    
    # Per-class results
    print("Per-Class Performance:")
    print("-" * 60)
    if hasattr(results.box, 'ap_class_index'):
        for i, ap in enumerate(results.box.ap50):
            class_name = model.names[i] if i in model.names else f"class_{i}"
            print(f"  {class_name:20s} AP@50: {ap:.3f}")
    print()
    
    print("=" * 60)
    print()
    print("Next step:")
    print("  python3 scripts/deploy_dota_model.py")
    print()

if __name__ == "__main__":
    evaluate_dota_model()
