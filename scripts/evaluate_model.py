#!/usr/bin/env python3
"""
scripts/evaluate_model.py
-------------------------
Evaluate trained YOLO model on test set and generate performance report.

Usage:
    python scripts/evaluate_model.py \
        --weights models/best_model.pt \
        --data datasets/military/military.yaml

This script:
1. Runs YOLO validation on the test split
2. Captures mAP@50, mAP@50-95, precision, recall per class
3. Generates confusion matrix image
4. Prints per-class AP table sorted from worst to best
5. Saves JSON summary with all metrics
6. Provides recommendations for classes needing more data
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime

import yaml
import numpy as np
from ultralytics import YOLO

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Evaluate YOLO model on military detection dataset"
    )
    parser.add_argument(
        "--weights",
        required=True,
        help="Path to trained model weights (.pt file)"
    )
    parser.add_argument(
        "--data",
        required=True,
        help="Path to dataset YAML file"
    )
    parser.add_argument(
        "--output",
        default="runs/military/eval",
        help="Output directory for evaluation results"
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Image size for inference"
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold"
    )
    parser.add_argument(
        "--iou",
        type=float,
        default=0.45,
        help="IoU threshold for NMS"
    )
    return parser.parse_args()


def load_class_names(data_yaml: str):
    """Load class names from dataset YAML."""
    with open(data_yaml, "r") as f:
        data = yaml.safe_load(f)
    
    if isinstance(data["names"], dict):
        return [data["names"][i] for i in sorted(data["names"].keys())]
    return data["names"]


def run_validation(model, data_yaml, args):
    """Run YOLO validation and return metrics."""
    log.info("Running validation on test set...")
    
    metrics = model.val(
        data=data_yaml,
        split="test",
        imgsz=args.imgsz,
        conf=args.conf,
        iou=args.iou,
        save_json=True,
        save_hybrid=False,
        plots=True,
        verbose=True
    )
    
    return metrics


def extract_per_class_metrics(metrics, class_names):
    """Extract per-class metrics from validation results."""
    per_class = []
    
    # Get per-class AP values
    if hasattr(metrics, "ap_class_index") and hasattr(metrics, "ap"):
        ap_values = metrics.ap  # AP per class
        
        for i, class_name in enumerate(class_names):
            if i < len(ap_values):
                ap50 = float(ap_values[i, 0]) if ap_values.ndim > 1 else float(ap_values[i])
                ap50_95 = float(np.mean(ap_values[i])) if ap_values.ndim > 1 else float(ap_values[i])
            else:
                ap50 = 0.0
                ap50_95 = 0.0
            
            per_class.append({
                "class_id": i,
                "class_name": class_name,
                "ap50": ap50,
                "ap50_95": ap50_95
            })
    else:
        # Fallback if metrics structure is different
        for i, class_name in enumerate(class_names):
            per_class.append({
                "class_id": i,
                "class_name": class_name,
                "ap50": 0.0,
                "ap50_95": 0.0
            })
    
    return per_class


def print_per_class_table(per_class_metrics):
    """Print formatted table of per-class AP sorted from worst to best."""
    log.info("=" * 70)
    log.info("PER-CLASS AVERAGE PRECISION (AP)")
    log.info("=" * 70)
    
    # Sort by AP50 (worst to best)
    sorted_metrics = sorted(per_class_metrics, key=lambda x: x["ap50"])
    
    print(f"{'Rank':<6} {'Class Name':<25} {'AP@50':<10} {'AP@50-95':<10}")
    print("-" * 70)
    
    for rank, item in enumerate(sorted_metrics, 1):
        ap50_str = f"{item['ap50']:.3f}"
        ap50_95_str = f"{item['ap50_95']:.3f}"
        
        # Color code based on performance
        if item['ap50'] < 0.3:
            marker = "❌"
        elif item['ap50'] < 0.5:
            marker = "⚠️"
        else:
            marker = "✅"
        
        print(f"{rank:<6} {marker} {item['class_name']:<23} {ap50_str:<10} {ap50_95_str:<10}")
    
    log.info("=" * 70)


def generate_recommendations(per_class_metrics):
    """Generate recommendations for improving model performance."""
    log.info("=" * 70)
    log.info("RECOMMENDATIONS")
    log.info("=" * 70)
    
    weak_classes = [m for m in per_class_metrics if m["ap50"] < 0.5]
    
    if not weak_classes:
        log.info("✅ All classes have AP@50 >= 0.5. Model performance is good!")
        return []
    
    log.info(f"⚠️  {len(weak_classes)} classes have AP@50 < 0.5 and need improvement:")
    log.info("")
    
    recommendations = []
    
    for item in sorted(weak_classes, key=lambda x: x["ap50"]):
        class_name = item["class_name"]
        ap50 = item["ap50"]
        
        log.info(f"  • {class_name} (AP@50: {ap50:.3f})")
        
        if ap50 < 0.1:
            rec = f"CRITICAL: {class_name} - Collect significantly more training data (10x current amount)"
        elif ap50 < 0.3:
            rec = f"HIGH: {class_name} - Add more diverse examples and apply heavy augmentation"
        else:
            rec = f"MEDIUM: {class_name} - Increase training data by 2-3x and verify annotations"
        
        recommendations.append(rec)
        log.info(f"    → {rec}")
    
    log.info("")
    log.info("Suggested augmentation strategies:")
    log.info("  1. Increase mosaic augmentation (mosaic=1.0)")
    log.info("  2. Add mixup augmentation (mixup=0.15)")
    log.info("  3. Increase rotation range (degrees=20)")
    log.info("  4. Add more scale variation (scale=0.7)")
    log.info("  5. Use copy-paste augmentation for rare classes")
    log.info("=" * 70)
    
    return recommendations


def save_results(output_dir, metrics, per_class_metrics, recommendations, args):
    """Save evaluation results to JSON file."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "model_weights": args.weights,
        "dataset": args.data,
        "overall_metrics": {
            "map50": float(metrics.box.map50) if hasattr(metrics.box, "map50") else 0.0,
            "map50_95": float(metrics.box.map) if hasattr(metrics.box, "map") else 0.0,
            "precision": float(metrics.box.mp) if hasattr(metrics.box, "mp") else 0.0,
            "recall": float(metrics.box.mr) if hasattr(metrics.box, "mr") else 0.0,
        },
        "per_class_metrics": per_class_metrics,
        "recommendations": recommendations,
        "config": {
            "imgsz": args.imgsz,
            "conf_threshold": args.conf,
            "iou_threshold": args.iou
        }
    }
    
    results_path = output_dir / "results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    log.info(f"Results saved to: {results_path}")
    
    # Also save a simple text summary
    summary_path = output_dir / "summary.txt"
    with open(summary_path, "w") as f:
        f.write("AEGIS Model Evaluation Summary\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Timestamp: {results['timestamp']}\n")
        f.write(f"Model: {args.weights}\n")
        f.write(f"Dataset: {args.data}\n\n")
        f.write("Overall Metrics:\n")
        f.write(f"  mAP@50:    {results['overall_metrics']['map50']:.4f}\n")
        f.write(f"  mAP@50-95: {results['overall_metrics']['map50_95']:.4f}\n")
        f.write(f"  Precision: {results['overall_metrics']['precision']:.4f}\n")
        f.write(f"  Recall:    {results['overall_metrics']['recall']:.4f}\n\n")
        f.write("Recommendations:\n")
        for rec in recommendations:
            f.write(f"  • {rec}\n")
    
    log.info(f"Summary saved to: {summary_path}")


def main():
    args = parse_args()
    
    # Validate inputs
    if not os.path.exists(args.weights):
        log.error(f"Model weights not found: {args.weights}")
        sys.exit(1)
    
    if not os.path.exists(args.data):
        log.error(f"Dataset YAML not found: {args.data}")
        sys.exit(1)
    
    log.info("=" * 70)
    log.info("AEGIS MODEL EVALUATION")
    log.info("=" * 70)
    log.info(f"Model weights: {args.weights}")
    log.info(f"Dataset: {args.data}")
    log.info(f"Output directory: {args.output}")
    log.info("=" * 70)
    
    # Load model
    log.info("Loading model...")
    model = YOLO(args.weights)
    
    # Load class names
    class_names = load_class_names(args.data)
    log.info(f"Loaded {len(class_names)} classes")
    
    # Run validation
    metrics = run_validation(model, args.data, args)
    
    # Extract per-class metrics
    per_class_metrics = extract_per_class_metrics(metrics, class_names)
    
    # Print results
    log.info("")
    log.info("=" * 70)
    log.info("OVERALL METRICS")
    log.info("=" * 70)
    log.info(f"mAP@50:    {metrics.box.map50:.4f}")
    log.info(f"mAP@50-95: {metrics.box.map:.4f}")
    log.info(f"Precision: {metrics.box.mp:.4f}")
    log.info(f"Recall:    {metrics.box.mr:.4f}")
    log.info("=" * 70)
    log.info("")
    
    # Print per-class table
    print_per_class_table(per_class_metrics)
    
    # Generate recommendations
    recommendations = generate_recommendations(per_class_metrics)
    
    # Save results
    save_results(args.output, metrics, per_class_metrics, recommendations, args)
    
    # Note about confusion matrix
    log.info("")
    log.info("=" * 70)
    log.info("Confusion matrix and other plots saved to:")
    log.info(f"  {Path(args.weights).parent}")
    log.info("=" * 70)
    
    log.info("")
    log.info("✅ Evaluation complete!")


if __name__ == "__main__":
    main()
