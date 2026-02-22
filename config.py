"""
config.py
---------
Central configuration for the Military Target Detection System.
All tunable parameters live here — no magic numbers elsewhere.
"""

import os

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH    = os.path.join(BASE_DIR, "models", "best_model.pt")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
LOG_PATH      = os.path.join(BASE_DIR, "logs", "detections.csv")

# ── Model settings ────────────────────────────────────────────────────────────
# Model type selection: "auto", "military", "dota", "coco"
MODEL_TYPE = os.environ.get("MODEL_TYPE", "auto").lower()

# Model paths for different datasets
MILITARY_MODEL_PATH = os.path.join(BASE_DIR, "models", "best_model.pt")
DOTA_MODEL_PATH = os.path.join(BASE_DIR, "models", "dota_model.pt")
COCO_MODEL_PATH = "yolo11n.pt"  # downloaded automatically by Ultralytics

# Fallback to the standard COCO-pretrained YOLOv11n when no custom weights exist.
# Replace MODEL_PATH above with your own fine-tuned weights to detect
# domain-specific military equipment.
YOLO_FALLBACK      = "yolo11n.pt"     # downloaded automatically by Ultralytics
CONFIDENCE_THRESH  = 0.25            # minimum confidence to report a detection
IOU_THRESH         = 0.45            # NMS IoU threshold
MAX_DETECTIONS     = 100             # cap on detections per image
DEVICE             = ""              # "" = auto (CUDA if available, else CPU)

# ── Threat classification ─────────────────────────────────────────────────────
# Military class names for custom-trained model.
# These match the UNIFIED_CLASSES in scripts/prepare_dataset.py
# Update these after deploying your custom military model.

# DOTA CLASSES (Aerial Object Detection)
DOTA_HIGH_RISK_CLASSES = {
    # Military aircraft
    "plane", "helicopter",
    # Naval vessels
    "ship", "harbor",
    # Large vehicles (potential military)
    "large-vehicle",
    # Strategic infrastructure
    "bridge",
}

DOTA_MEDIUM_RISK_CLASSES = {
    # Civilian vehicles
    "small-vehicle",
    # Infrastructure
    "storage-tank", "ground-track-field",
    # Sports facilities (potential gathering points)
    "baseball-diamond", "tennis-court", "basketball-court",
    "soccer-ball-field", "swimming-pool",
    # Traffic
    "roundabout",
}

# MILITARY CLASSES (Ground-level Military Equipment)
# HIGH RISK: Direct combat threats and heavy military equipment
MILITARY_HIGH_RISK_CLASSES = {
    # Heavy armor & artillery
    "tank", "armored_vehicle", "missile_launcher", "artillery",
    "rocket_launcher", "anti_aircraft_gun",
    # Airborne threats
    "fighter_jet", "attack_helicopter", "combat_drone",
    # Naval threats
    "warship", "submarine",
}

# MEDIUM RISK: Support equipment and reconnaissance
MILITARY_MEDIUM_RISK_CLASSES = {
    # Support vehicles & equipment
    "military_truck", "patrol_boat", "military_helicopter",
    "radar_station", "bunker",
    # Reconnaissance
    "recon_drone",
    # Personnel
    "military_personnel",
    # Infrastructure
    "runway", "helipad",
}

# COCO CLASSES (General Object Detection - Fallback)
COCO_HIGH_RISK_CLASSES = {
    # Vehicles (COCO fallback classes for pretrained model)
    "truck", "bus", "car", "airplane", "helicopter",
    # Weapons (COCO fallback)
    "knife", "scissors",
}

COCO_MEDIUM_RISK_CLASSES = {
    # COCO fallback classes
    "person", "backpack", "handbag", "boat", "train",
    "bicycle", "motorcycle",
}

# Dynamic class selection based on MODEL_TYPE
def get_risk_classes():
    """Get appropriate risk classes based on current model type"""
    model_type = os.environ.get("MODEL_TYPE", "auto").lower()
    
    if model_type == "dota":
        return DOTA_HIGH_RISK_CLASSES, DOTA_MEDIUM_RISK_CLASSES
    elif model_type == "military":
        return MILITARY_HIGH_RISK_CLASSES, MILITARY_MEDIUM_RISK_CLASSES
    elif model_type == "coco":
        return COCO_HIGH_RISK_CLASSES, COCO_MEDIUM_RISK_CLASSES
    else:  # auto - try to detect from model
        return COCO_HIGH_RISK_CLASSES, COCO_MEDIUM_RISK_CLASSES

# Default classes (for backward compatibility)
HIGH_RISK_CLASSES, MEDIUM_RISK_CLASSES = get_risk_classes()

# ── Upload constraints ────────────────────────────────────────────────────────
ALLOWED_EXTENSIONS  = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "tiff"}
MAX_CONTENT_LENGTH  = 32 * 1024 * 1024  # 32 MB

# ── Flask ─────────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", "mil-detect-dev-key-change-in-prod")
DEBUG      = os.environ.get("DEBUG", "true").lower() == "true"
PORT       = int(os.environ.get("PORT", 5000))
HOST       = os.environ.get("HOST", "0.0.0.0")

# ── Annotation colours (BGR for OpenCV) ──────────────────────────────────────
COLOR_HIGH_RISK   = (0,   0,   255)   # red
COLOR_MEDIUM_RISK = (0,  140,  255)   # orange
COLOR_LOW_RISK    = (0,  200,   80)   # green
COLOR_TEXT_BG     = (0,   0,    0)    # black pill behind label text


# ── AI Tactical Analyst ───────────────────────────────────────────────────
# Multi-provider LLM configuration for situational intelligence
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openrouter").lower()

# API Keys for different providers
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Model and endpoint configuration
LLM_MODEL = os.environ.get("LLM_MODEL", "meta-llama/llama-3.2-3b-instruct:free")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MAX_TOKENS = int(os.environ.get("LLM_MAX_TOKENS", "2048"))
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.7"))

# Determine if analyst is enabled based on provider
def _check_analyst_enabled():
    if LLM_PROVIDER == "anthropic":
        return bool(ANTHROPIC_API_KEY)
    elif LLM_PROVIDER == "openai":
        return bool(OPENAI_API_KEY)
    elif LLM_PROVIDER == "groq":
        return bool(GROQ_API_KEY)
    elif LLM_PROVIDER == "gemini":
        return bool(GEMINI_API_KEY)
    elif LLM_PROVIDER == "openrouter":
        return bool(OPENROUTER_API_KEY)
    return False

ANALYST_ENABLED = _check_analyst_enabled()
SITREP_STORE_PATH = os.path.join(BASE_DIR, "logs", "sitreps.json")

# Legacy Claude-specific settings (for backward compatibility)
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-20250514")
CLAUDE_MAX_TOKENS = int(os.environ.get("CLAUDE_MAX_TOKENS", "2048"))
