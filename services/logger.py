"""
services/logger.py
------------------
Append detection events to a persistent CSV log file.

CSV columns
-----------
timestamp, image_filename, threat_level, total_detections,
high_risk_count, class_name, confidence, risk_level,
box_x1, box_y1, box_x2, box_y2, inference_ms
"""

import csv
import os
import logging
from datetime import datetime

from config import LOG_PATH

_file_logger = logging.getLogger(__name__)

# CSV column headers (written once when the file is first created)
CSV_HEADERS = [
    "timestamp",
    "image_filename",
    "threat_level",
    "total_detections",
    "high_risk_count",
    "class_name",
    "confidence",
    "risk_level",
    "box_x1",
    "box_y1",
    "box_x2",
    "box_y2",
    "inference_ms",
]


def _ensure_log_file():
    """Create the CSV file with headers if it does not already exist."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    if not os.path.exists(LOG_PATH) or os.path.getsize(LOG_PATH) == 0:
        with open(LOG_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


def log_detections(
    image_filename: str,
    detections: list,
    threat_report: dict,
    inference_ms: float,
) -> None:
    """
    Append one row per detection (or a single 'no-detection' row) to the CSV.

    Parameters
    ----------
    image_filename : original uploaded filename
    detections     : list of detection dicts from detection.run_detection()
    threat_report  : dict from alert.check_threat()
    inference_ms   : inference duration in milliseconds
    """
    _ensure_log_file()

    timestamp     = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    threat_level  = threat_report["threat_level"]
    total         = threat_report["stats"]["total"]
    high_risk_cnt = threat_report["stats"]["high_risk"]

    rows = []

    if detections:
        for det in detections:
            rows.append([
                timestamp,
                image_filename,
                threat_level,
                total,
                high_risk_cnt,
                det["class_name"],
                f"{det['confidence']:.4f}",
                det["risk_level"],
                det["box"]["x1"],
                det["box"]["y1"],
                det["box"]["x2"],
                det["box"]["y2"],
                inference_ms,
            ])
    else:
        # Log even when nothing is detected so the event is recorded
        rows.append([
            timestamp,
            image_filename,
            threat_level,
            0, 0,
            "NONE", "0.0000", "none",
            0, 0, 0, 0,
            inference_ms,
        ])

    try:
        with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        _file_logger.info("Logged %d detection rows for %s", len(rows), image_filename)
    except OSError as exc:
        _file_logger.error("Failed to write detection log: %s", exc)


def get_recent_logs(limit: int = 50) -> list[dict]:
    """
    Read the most recent *limit* rows from the CSV and return as list of dicts.
    Used by the /logs API endpoint.
    """
    _ensure_log_file()
    rows = []
    try:
        with open(LOG_PATH, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    except OSError:
        pass
    return rows[-limit:]  # return tail
