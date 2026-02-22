#!/usr/bin/env python3
"""
scripts/prepare_dataset.py
--------------------------
Merge multiple YOLO-format datasets into a unified military detection dataset.

Usage:
    python scripts/prepare_dataset.py \
        --sources dota_yolo/ vedai_yolo/ \
        --output datasets/military/ \
        --split 0.8 0.1 0.1

This script:
1. Walks each source directory for images/ and labels/ subdirs
2. Reads each dataset's class mapping (classes.txt or data.yaml)
3. Remaps class indices to unified UNIFIED_CLASSES indices
4. Copies images to output/images/{train,val,test}/
5. Writes remapped labels to output/labels/{train,val,test}/
6. Performs train/val/test split using the specified ratios
7. Writes output/military.yaml with all class names
"""

import os
import sys
import shutil
import random
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Tuple

import yaml

# ── Unified military class list ──────────────────────────────────────────────
UNIFIED_CLASSES = [
    "tank",
    "armored_vehicle",
    "missile_launcher",
    "artillery",
    "fighter_jet",
    "attack_helicopter",
    "warship",
    "submarine",
    "rocket_launcher",
    "anti_aircraft_gun",
    "military_truck",
    "patrol_boat",
    "military_helicopter",
    "radar_station",
    "recon_drone",
    "combat_drone",
    "military_personnel",
    "bunker",
    "runway",
    "helipad"
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Merge YOLO datasets into unified military detection dataset"
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        required=True,
        help="Source dataset directories (YOLO format with images/ and labels/)"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output directory for merged dataset"
    )
    parser.add_argument(
        "--split",
        nargs=3,
        type=float,
        default=[0.8, 0.1, 0.1],
        help="Train/val/test split ratios (default: 0.8 0.1 0.1)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible splits"
    )
    return parser.parse_args()


def load_class_mapping(source_dir: Path) -> Dict[int, str]:
    """
    Load class mapping from source dataset.
    Tries data.yaml first, then classes.txt.
    """
    # Try data.yaml
    yaml_path = source_dir / "data.yaml"
    if yaml_path.exists():
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
            if "names" in data:
                # Handle both dict and list formats
                if isinstance(data["names"], dict):
                    return {int(k): v for k, v in data["names"].items()}
                elif isinstance(data["names"], list):
                    return {i: name for i, name in enumerate(data["names"])}
    
    # Try classes.txt
    classes_path = source_dir / "classes.txt"
    if classes_path.exists():
        with open(classes_path, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
            return {i: name for i, name in enumerate(lines)}
    
    log.warning(f"No class mapping found in {source_dir}, using numeric indices")
    return {}


def normalize_class_name(name: str) -> str:
    """Normalize class name to match UNIFIED_CLASSES format."""
    return name.lower().replace(" ", "_").replace("-", "_")


def find_unified_class_index(class_name: str) -> int:
    """
    Find the index of a class name in UNIFIED_CLASSES.
    Returns -1 if not found.
    """
    normalized = normalize_class_name(class_name)
    
    # Exact match
    if normalized in UNIFIED_CLASSES:
        return UNIFIED_CLASSES.index(normalized)
    
    # Fuzzy matching for common variations
    mappings = {
        "tank": ["main_battle_tank", "light_tank", "heavy_tank"],
        "armored_vehicle": ["apc", "ifv", "armored_car", "armoured_vehicle"],
        "fighter_jet": ["fighter", "jet_fighter", "combat_aircraft"],
        "attack_helicopter": ["helicopter_gunship", "combat_helicopter"],
        "military_truck": ["truck", "cargo_truck", "transport_truck"],
        "military_personnel": ["soldier", "personnel", "troops"],
        "warship": ["naval_vessel", "destroyer", "frigate", "cruiser"],
        "patrol_boat": ["boat", "small_boat"],
        "artillery": ["howitzer", "cannon", "field_gun"],
        "missile_launcher": ["mlrs", "sam_launcher"],
    }
    
    for unified_name, variations in mappings.items():
        if normalized in variations or any(v in normalized for v in variations):
            return UNIFIED_CLASSES.index(unified_name)
    
    return -1


def remap_label_file(
    label_path: Path,
    source_mapping: Dict[int, str],
    output_path: Path
) -> bool:
    """
    Remap class indices in a YOLO label file.
    Returns True if any valid classes were found, False otherwise.
    """
    if not label_path.exists():
        return False
    
    remapped_lines = []
    
    with open(label_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            
            old_class_id = int(parts[0])
            old_class_name = source_mapping.get(old_class_id, f"class_{old_class_id}")
            
            new_class_id = find_unified_class_index(old_class_name)
            
            if new_class_id == -1:
                log.debug(f"Skipping unmapped class: {old_class_name}")
                continue
            
            # Replace class ID, keep bbox coordinates
            parts[0] = str(new_class_id)
            remapped_lines.append(" ".join(parts))
    
    if remapped_lines:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write("\n".join(remapped_lines) + "\n")
        return True
    
    return False


def collect_dataset_files(source_dir: Path) -> List[Tuple[Path, Path]]:
    """
    Collect all image-label pairs from a source dataset.
    Returns list of (image_path, label_path) tuples.
    """
    pairs = []
    
    # Look for images in images/ or train/images/, val/images/, etc.
    image_dirs = []
    if (source_dir / "images").exists():
        image_dirs.append(source_dir / "images")
    
    for subdir in ["train", "val", "test", "valid"]:
        img_dir = source_dir / subdir / "images"
        if img_dir.exists():
            image_dirs.append(img_dir)
    
    for img_dir in image_dirs:
        for img_path in img_dir.rglob("*"):
            if img_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]:
                # Find corresponding label
                label_path = img_path.parent.parent / "labels" / img_path.stem
                label_path = label_path.with_suffix(".txt")
                
                if not label_path.exists():
                    # Try alternate structure
                    label_path = img_path.parent.parent.parent / "labels" / img_path.parent.name / img_path.stem
                    label_path = label_path.with_suffix(".txt")
                
                pairs.append((img_path, label_path))
    
    return pairs


def process_dataset(
    source_dir: Path,
    output_dir: Path,
    split_ratios: List[float],
    seed: int
) -> Dict[str, int]:
    """
    Process a single source dataset and merge into output.
    Returns statistics dict.
    """
    log.info(f"Processing dataset: {source_dir}")
    
    # Load class mapping
    class_mapping = load_class_mapping(source_dir)
    log.info(f"Loaded {len(class_mapping)} classes from {source_dir}")
    
    # Collect all image-label pairs
    pairs = collect_dataset_files(source_dir)
    log.info(f"Found {len(pairs)} image-label pairs")
    
    if not pairs:
        log.warning(f"No valid pairs found in {source_dir}")
        return {"total": 0, "train": 0, "val": 0, "test": 0, "skipped": 0}
    
    # Shuffle for random split
    random.seed(seed)
    random.shuffle(pairs)
    
    # Calculate split indices
    n_total = len(pairs)
    n_train = int(n_total * split_ratios[0])
    n_val = int(n_total * split_ratios[1])
    
    splits = {
        "train": pairs[:n_train],
        "val": pairs[n_train:n_train + n_val],
        "test": pairs[n_train + n_val:]
    }
    
    stats = {"total": n_total, "train": 0, "val": 0, "test": 0, "skipped": 0}
    
    # Process each split
    for split_name, split_pairs in splits.items():
        for img_path, label_path in split_pairs:
            # Generate unique filename
            unique_name = f"{source_dir.name}_{img_path.stem}_{hash(str(img_path)) % 100000}"
            
            output_img_path = output_dir / "images" / split_name / f"{unique_name}{img_path.suffix}"
            output_label_path = output_dir / "labels" / split_name / f"{unique_name}.txt"
            
            # Remap and write label
            if remap_label_file(label_path, class_mapping, output_label_path):
                # Copy image
                output_img_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(img_path, output_img_path)
                stats[split_name] += 1
            else:
                stats["skipped"] += 1
    
    log.info(f"Processed {source_dir.name}: train={stats['train']}, val={stats['val']}, test={stats['test']}, skipped={stats['skipped']}")
    return stats


def write_data_yaml(output_dir: Path):
    """Write the YOLO data.yaml configuration file."""
    data = {
        "path": str(output_dir.absolute()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "nc": len(UNIFIED_CLASSES),
        "names": {i: name for i, name in enumerate(UNIFIED_CLASSES)}
    }
    
    yaml_path = output_dir / "military.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    log.info(f"Written data config to {yaml_path}")


def main():
    args = parse_args()
    
    # Validate split ratios
    if abs(sum(args.split) - 1.0) > 0.01:
        log.error(f"Split ratios must sum to 1.0, got {sum(args.split)}")
        sys.exit(1)
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    log.info("=" * 60)
    log.info("AEGIS Military Dataset Preparation")
    log.info("=" * 60)
    log.info(f"Output directory: {output_dir}")
    log.info(f"Split ratios: train={args.split[0]}, val={args.split[1]}, test={args.split[2]}")
    log.info(f"Unified classes: {len(UNIFIED_CLASSES)}")
    log.info("=" * 60)
    
    # Process each source dataset
    total_stats = {"total": 0, "train": 0, "val": 0, "test": 0, "skipped": 0}
    
    for source in args.sources:
        source_path = Path(source)
        if not source_path.exists():
            log.warning(f"Source directory not found: {source_path}")
            continue
        
        stats = process_dataset(source_path, output_dir, args.split, args.seed)
        for key in total_stats:
            total_stats[key] += stats[key]
    
    # Write data.yaml
    write_data_yaml(output_dir)
    
    # Summary
    log.info("=" * 60)
    log.info("DATASET PREPARATION COMPLETE")
    log.info("=" * 60)
    log.info(f"Total images processed: {total_stats['total']}")
    log.info(f"  Train: {total_stats['train']}")
    log.info(f"  Val:   {total_stats['val']}")
    log.info(f"  Test:  {total_stats['test']}")
    log.info(f"  Skipped (no valid classes): {total_stats['skipped']}")
    log.info("=" * 60)
    log.info(f"Dataset ready at: {output_dir}")
    log.info(f"Config file: {output_dir / 'military.yaml'}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
