"""
services/detection.py
---------------------
Handles YOLO model loading and inference.

Design choices
--------------
* The model is loaded **once** at app startup (passed in, not re-loaded per request).
* OpenCV is used for annotation so we stay pure-Python without PIL/Pillow deps.
* Returns both a JSON-serialisable detection list AND the path to the annotated image.
"""

import os
import time
import logging
from pathlib import Path

import cv2
import numpy as np

from config import (
    CONFIDENCE_THRESH, IOU_THRESH, MAX_DETECTIONS, DEVICE,
    HIGH_RISK_CLASSES, MEDIUM_RISK_CLASSES,
    COLOR_HIGH_RISK, COLOR_MEDIUM_RISK, COLOR_LOW_RISK,
    UPLOAD_FOLDER,
)

logger = logging.getLogger(__name__)


# ── Risk helper ───────────────────────────────────────────────────────────────

def _risk_level(class_name: str) -> str:
    """Return 'high', 'medium', or 'low' for a given class name."""
    name = class_name.lower().replace(" ", "_")
    if name in HIGH_RISK_CLASSES:
        return "high"
    if name in MEDIUM_RISK_CLASSES:
        return "medium"
    return "low"


def _risk_color(risk: str):
    return {
        "high":   COLOR_HIGH_RISK,
        "medium": COLOR_MEDIUM_RISK,
        "low":    COLOR_LOW_RISK,
    }.get(risk, COLOR_LOW_RISK)


# ── Annotation ────────────────────────────────────────────────────────────────

def _annotate(image: np.ndarray, detections: list) -> np.ndarray:
    """
    Draw bounding boxes and labels onto *image* (BGR numpy array).
    Returns a new annotated image (original is not mutated).
    """
    annotated = image.copy()
    h, w = annotated.shape[:2]
    font       = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = max(0.4, min(w, h) / 1200)
    thickness  = max(1, int(min(w, h) / 400))

    for det in detections:
        x1, y1, x2, y2 = det["box"]["x1"], det["box"]["y1"], det["box"]["x2"], det["box"]["y2"]
        risk   = det["risk_level"]
        color  = _risk_color(risk)
        label  = f"{det['class_name']}  {det['confidence']:.0%}"

        # Bounding box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness + 1)

        # Label pill
        (lw, lh), baseline = cv2.getTextSize(label, font, font_scale, thickness)
        pill_y1 = max(y1 - lh - baseline - 6, 0)
        pill_y2 = max(y1, lh + baseline + 6)
        cv2.rectangle(annotated, (x1, pill_y1), (x1 + lw + 8, pill_y2), color, -1)
        cv2.putText(
            annotated, label,
            (x1 + 4, pill_y2 - baseline - 2),
            font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA,
        )

    return annotated


# ── Main inference function ───────────────────────────────────────────────────

def run_detection(model, image_path: str) -> dict:
    """
    Run YOLO inference on *image_path*.

    Parameters
    ----------
    model       : loaded Ultralytics YOLO instance
    image_path  : absolute path to the uploaded image

    Returns
    -------
    dict with keys:
        detections      – list of detection dicts
        annotated_path  – URL-relative path to annotated image
        inference_ms    – inference time in milliseconds
        image_size      – (width, height)
    """
    # ── Load image ─────────────────────────────────────────────────────────────
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    h, w = image.shape[:2]

    # ── Run YOLO ───────────────────────────────────────────────────────────────
    t0 = time.perf_counter()
    results = model.predict(
        source     = image_path,
        conf       = CONFIDENCE_THRESH,
        iou        = IOU_THRESH,
        max_det    = MAX_DETECTIONS,
        device     = DEVICE,
        verbose    = False,
    )
    inference_ms = round((time.perf_counter() - t0) * 1000, 1)

    # ── Parse results ──────────────────────────────────────────────────────────
    detections = []
    result = results[0]  # single image → single result

    if result.boxes is not None:
        boxes_xyxy = result.boxes.xyxy.cpu().numpy()   # shape (N,4)
        confs      = result.boxes.conf.cpu().numpy()   # shape (N,)
        cls_ids    = result.boxes.cls.cpu().numpy().astype(int)  # shape (N,)
        names      = result.names                      # {id: class_name}

        for i, (box, conf, cls_id) in enumerate(zip(boxes_xyxy, confs, cls_ids)):
            x1, y1, x2, y2 = [int(v) for v in box]
            class_name = names.get(cls_id, f"class_{cls_id}")
            risk       = _risk_level(class_name)

            detections.append({
                "id":         i,
                "class_name": class_name,
                "confidence": float(round(conf, 4)),
                "risk_level": risk,
                "box": {
                    "x1": x1, "y1": y1,
                    "x2": x2, "y2": y2,
                    "width":  x2 - x1,
                    "height": y2 - y1,
                    "cx":     (x1 + x2) // 2,
                    "cy":     (y1 + y2) // 2,
                },
            })

    # Sort: high-risk first, then by confidence descending
    _priority = {"high": 0, "medium": 1, "low": 2}
    detections.sort(key=lambda d: (_priority[d["risk_level"]], -d["confidence"]))

    # ── Annotate & save ────────────────────────────────────────────────────────
    annotated_img   = _annotate(image, detections)
    orig_stem       = Path(image_path).stem
    annotated_name  = f"annotated_{orig_stem}.jpg"
    annotated_path  = os.path.join(UPLOAD_FOLDER, annotated_name)
    cv2.imwrite(annotated_path, annotated_img, [cv2.IMWRITE_JPEG_QUALITY, 92])

    # URL path (relative to /static/)
    annotated_url = f"/static/uploads/{annotated_name}"

    logger.info(
        "Detection complete | %d objects found | %.1f ms | image=%s",
        len(detections), inference_ms, image_path,
    )

    return {
        "detections":     detections,
        "annotated_path": annotated_url,
        "inference_ms":   inference_ms,
        "image_size":     {"width": w, "height": h},
    }
