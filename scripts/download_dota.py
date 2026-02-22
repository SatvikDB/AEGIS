#!/usr/bin/env python3
"""
DOTA Dataset Downloader
Downloads DOTA dataset from Roboflow (pre-converted to YOLO format)
"""

import os
import sys
import requests
from pathlib import Path

def download_dota_roboflow():
    """
    Download DOTA dataset from Roboflow Universe
    Already in YOLO format - no conversion needed!
    """
    print("=" * 60)
    print("DOTA DATASET DOWNLOADER")
    print("=" * 60)
    print()
    print("This script will guide you through downloading DOTA dataset")
    print("from Roboflow Universe (already in YOLO format).")
    print()
    print("Steps:")
    print("1. Go to: https://universe.roboflow.com/")
    print("2. Search for: 'DOTA aerial object detection'")
    print("3. Select a DOTA dataset (look for one with 15-18 classes)")
    print("4. Click 'Download Dataset'")
    print("5. Select format: 'YOLOv8' (compatible with YOLO11)")
    print("6. Copy the download code/link")
    print()
    print("Recommended datasets:")
    print("- 'DOTA-v1.0' or 'DOTA-v1.5' or 'DOTA-v2.0'")
    print("- Look for datasets with these classes:")
    print("  plane, ship, storage-tank, baseball-diamond, tennis-court,")
    print("  basketball-court, ground-track-field, harbor, bridge,")
    print("  large-vehicle, small-vehicle, helicopter, roundabout,")
    print("  soccer-ball-field, swimming-pool")
    print()
    print("=" * 60)
    print()
    
    # Create datasets directory
    datasets_dir = Path("datasets/dota")
    datasets_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Created directory: {datasets_dir}")
    print()
    print("NEXT STEPS:")
    print("1. Download the dataset from Roboflow")
    print("2. Extract the .zip file to: datasets/dota/")
    print("3. Verify structure:")
    print("   datasets/dota/")
    print("   ├── train/")
    print("   │   ├── images/")
    print("   │   └── labels/")
    print("   ├── valid/")
    print("   │   ├── images/")
    print("   │   └── labels/")
    print("   ├── test/")
    print("   │   ├── images/")
    print("   │   └── labels/")
    print("   └── data.yaml")
    print()
    print("4. Run: python3 scripts/train_dota_model.py")
    print()
    print("=" * 60)

if __name__ == "__main__":
    download_dota_roboflow()
