"""
services/analytics.py
---------------------
Dashboard analytics computation from detection logs.

Reads logs/detections.csv and computes aggregated statistics for the
Intelligence Dashboard at /dashboard.
"""

import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict, Counter

import pandas as pd

from config import LOG_PATH, HIGH_RISK_CLASSES, MEDIUM_RISK_CLASSES

logger = logging.getLogger(__name__)


def compute_dashboard_data() -> dict:
    """
    Compute all dashboard analytics from the detection log CSV.
    
    Returns a dict with keys:
        - summary: total scans, detections, critical today, most detected class
        - threat_distribution: count by threat level
        - detections_over_time: daily counts for last 30 days
        - top_classes: top 10 detected classes with risk level
        - hourly_heatmap: 7x24 grid of detection counts by day/hour
        - confidence_histogram: 10 bins of confidence distribution
        - recent_rows: last 25 detection rows
    """
    
    # Handle missing or empty CSV
    if not os.path.exists(LOG_PATH) or os.path.getsize(LOG_PATH) == 0:
        return _empty_dashboard_data()
    
    try:
        df = pd.read_csv(LOG_PATH)
    except Exception as exc:
        logger.error("Failed to read CSV: %s", exc)
        return _empty_dashboard_data()
    
    if df.empty:
        return _empty_dashboard_data()
    
    # Parse timestamps
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df = df.dropna(subset=['timestamp'])
    
    if df.empty:
        return _empty_dashboard_data()
    
    # Filter out NONE detections for most calculations
    df_real = df[df['class_name'] != 'NONE'].copy()
    
    # ── Summary stats ──────────────────────────────────────────────────
    total_scans = df['image_filename'].nunique()
    total_detections = len(df_real)
    
    today = datetime.now().date()
    critical_today = len(df[(df['threat_level'] == 'CRITICAL') & 
                             (df['timestamp'].dt.date == today)])
    
    if len(df_real) > 0:
        most_detected = df_real['class_name'].value_counts().index[0]
    else:
        most_detected = "None"
    
    summary = {
        "total_scans": int(total_scans),
        "total_detections": int(total_detections),
        "critical_today": int(critical_today),
        "most_detected_class": most_detected
    }
    
    # ── Threat distribution ────────────────────────────────────────────
    threat_counts = df.groupby('image_filename')['threat_level'].first().value_counts()
    threat_distribution = {
        "CRITICAL": int(threat_counts.get("CRITICAL", 0)),
        "HIGH": int(threat_counts.get("HIGH", 0)),
        "ELEVATED": int(threat_counts.get("ELEVATED", 0)),
        "LOW": int(threat_counts.get("LOW", 0)),
        "CLEAR": int(threat_counts.get("CLEAR", 0))
    }
    
    # ── Detections over time (last 30 days) ────────────────────────────
    end_date = datetime.now()
    start_date = end_date - timedelta(days=29)
    
    date_range = pd.date_range(start=start_date.date(), end=end_date.date(), freq='D')
    daily_counts = df_real.groupby(df_real['timestamp'].dt.date).size()
    
    detections_over_time = []
    for date in date_range:
        count = int(daily_counts.get(date.date(), 0))
        detections_over_time.append({
            "date": date.strftime("%Y-%m-%d"),
            "count": count
        })
    
    # ── Top 10 classes ─────────────────────────────────────────────────
    class_counts = df_real['class_name'].value_counts().head(10)
    top_classes = []
    for class_name, count in class_counts.items():
        risk = _get_risk_level(class_name)
        top_classes.append({
            "class_name": class_name,
            "count": int(count),
            "risk": risk
        })
    
    # ── Hourly heatmap (day of week x hour) ────────────────────────────
    df_real['day_of_week'] = df_real['timestamp'].dt.day_name()
    df_real['hour'] = df_real['timestamp'].dt.hour
    
    heatmap_data = df_real.groupby(['day_of_week', 'hour']).size()
    
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    hourly_heatmap = {}
    
    for day in days_order:
        day_short = day[:3]
        hourly_heatmap[day_short] = {}
        for hour in range(24):
            count = int(heatmap_data.get((day, hour), 0))
            hourly_heatmap[day_short][hour] = count
    
    # ── Confidence histogram ───────────────────────────────────────────
    if len(df_real) > 0:
        df_real['confidence'] = pd.to_numeric(df_real['confidence'], errors='coerce')
        df_real = df_real.dropna(subset=['confidence'])
        
        bins = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        bin_labels = [f"{bins[i]:.1f}-{bins[i+1]:.1f}" for i in range(len(bins)-1)]
        
        df_real['conf_bin'] = pd.cut(df_real['confidence'], bins=bins, labels=bin_labels, include_lowest=True)
        conf_counts = df_real['conf_bin'].value_counts().sort_index()
        
        confidence_histogram = []
        for bin_label in bin_labels:
            count = int(conf_counts.get(bin_label, 0))
            confidence_histogram.append({
                "bin": bin_label,
                "count": count
            })
    else:
        confidence_histogram = [{"bin": f"{i/10:.1f}-{(i+1)/10:.1f}", "count": 0} for i in range(10)]
    
    # ── Recent rows (last 25) ──────────────────────────────────────────
    recent_df = df.tail(25).sort_values('timestamp', ascending=False)
    recent_rows = recent_df.to_dict('records')
    
    # Convert timestamps to strings
    for row in recent_rows:
        if isinstance(row.get('timestamp'), pd.Timestamp):
            row['timestamp'] = row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "summary": summary,
        "threat_distribution": threat_distribution,
        "detections_over_time": detections_over_time,
        "top_classes": top_classes,
        "hourly_heatmap": hourly_heatmap,
        "confidence_histogram": confidence_histogram,
        "recent_rows": recent_rows
    }


def _get_risk_level(class_name: str) -> str:
    """Determine risk level for a class name."""
    name = class_name.lower().replace(" ", "_")
    if name in HIGH_RISK_CLASSES:
        return "high"
    if name in MEDIUM_RISK_CLASSES:
        return "medium"
    return "low"


def _empty_dashboard_data() -> dict:
    """Return zeroed-out dashboard data structure."""
    return {
        "summary": {
            "total_scans": 0,
            "total_detections": 0,
            "critical_today": 0,
            "most_detected_class": "None"
        },
        "threat_distribution": {
            "CRITICAL": 0,
            "HIGH": 0,
            "ELEVATED": 0,
            "LOW": 0,
            "CLEAR": 0
        },
        "detections_over_time": [
            {"date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"), "count": 0}
            for i in range(29, -1, -1)
        ],
        "top_classes": [],
        "hourly_heatmap": {
            day: {hour: 0 for hour in range(24)}
            for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        },
        "confidence_histogram": [
            {"bin": f"{i/10:.1f}-{(i+1)/10:.1f}", "count": 0}
            for i in range(10)
        ],
        "recent_rows": []
    }
