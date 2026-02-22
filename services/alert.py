"""
services/alert.py
-----------------
Threat assessment logic.

Converts a list of raw detection dicts (from detection.py) into a structured
threat report that the frontend can render without any additional computation.
"""

from config import HIGH_RISK_CLASSES, MEDIUM_RISK_CLASSES


# ── Threat levels ─────────────────────────────────────────────────────────────

THREAT_LEVELS = {
    "CRITICAL": {
        "label":       "CRITICAL THREAT",
        "description": "High-risk military target(s) detected. Immediate action required.",
        "color":       "#ff1744",
        "icon":        "☢",
    },
    "HIGH": {
        "label":       "HIGH ALERT",
        "description": "Multiple concerning objects detected in the area.",
        "color":       "#ff6d00",
        "icon":        "⚠",
    },
    "ELEVATED": {
        "label":       "ELEVATED RISK",
        "description": "Suspicious activity or equipment detected. Monitor closely.",
        "color":       "#ffd600",
        "icon":        "🔶",
    },
    "LOW": {
        "label":       "LOW RISK",
        "description": "No immediate threats detected. Routine surveillance.",
        "color":       "#00e676",
        "icon":        "✔",
    },
    "CLEAR": {
        "label":       "ALL CLEAR",
        "description": "No objects detected in image.",
        "color":       "#40c4ff",
        "icon":        "✔",
    },
}


def check_threat(detections: list) -> dict:
    """
    Evaluate a list of detection dicts and return a threat assessment report.

    Parameters
    ----------
    detections : list of dicts produced by detection.run_detection()

    Returns
    -------
    dict:
        threat_level   – one of the THREAT_LEVELS keys
        label          – human-readable level string
        description    – prose explanation
        color          – hex colour for UI badge
        icon           – emoji icon
        high_risk_hits – list of class names that triggered high-risk flag
        stats          – summary counts
    """
    if not detections:
        level = "CLEAR"
        high_risk_hits = []
    else:
        high_risk_hits = [
            d["class_name"]
            for d in detections
            if d["risk_level"] == "high"
        ]
        medium_hits = [
            d["class_name"]
            for d in detections
            if d["risk_level"] == "medium"
        ]

        high_count   = len(high_risk_hits)
        medium_count = len(medium_hits)

        if high_count >= 2:
            level = "CRITICAL"
        elif high_count == 1:
            level = "HIGH"
        elif medium_count >= 2:
            level = "ELEVATED"
        else:
            level = "LOW"

    stats = _compute_stats(detections)
    meta  = THREAT_LEVELS[level]

    return {
        "threat_level":   level,
        "label":          meta["label"],
        "description":    meta["description"],
        "color":          meta["color"],
        "icon":           meta["icon"],
        "high_risk_hits": high_risk_hits,
        "stats":          stats,
    }


def _compute_stats(detections: list) -> dict:
    """Aggregate counts and confidence stats from detections."""
    if not detections:
        return {
            "total":         0,
            "high_risk":     0,
            "medium_risk":   0,
            "low_risk":      0,
            "avg_confidence": 0.0,
            "max_confidence": 0.0,
            "class_counts":  {},
        }

    confs = [d["confidence"] for d in detections]
    class_counts: dict[str, int] = {}
    risk_counts   = {"high": 0, "medium": 0, "low": 0}

    for d in detections:
        class_counts[d["class_name"]] = class_counts.get(d["class_name"], 0) + 1
        risk_counts[d["risk_level"]] += 1

    return {
        "total":          len(detections),
        "high_risk":      risk_counts["high"],
        "medium_risk":    risk_counts["medium"],
        "low_risk":       risk_counts["low"],
        "avg_confidence": round(sum(confs) / len(confs), 4),
        "max_confidence": round(max(confs), 4),
        "class_counts":   class_counts,
    }
