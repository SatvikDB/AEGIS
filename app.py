"""
app.py
------
Entry point for the Military Target Detection System.

Startup sequence
----------------
1. Load environment variables from .env
2. Verify / create required directories (uploads, logs, models).
3. Load the YOLO model once into memory.
4. Serve the single-page frontend.
5. Expose REST endpoints: /detect, /logs, /health, /dashboard, /api/*.

Run with:
    python app.py
"""

import os
import sys

# ── Load environment variables FIRST ─────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()  # Load .env file before importing config

import uuid
import logging
from pathlib import Path

from flask import (
    Flask, render_template, request,
    jsonify, send_from_directory,
)
from werkzeug.utils import secure_filename

# ── Ensure project root is on path ───────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from services.detection import run_detection
from services.alert      import check_threat
from services.logger     import log_detections, get_recent_logs
from services.analyst    import generate_sitrep, analyst_chat, build_detection_context
from services.sitrep_store import get_store
from services.geo_service import extract_gps

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt = "%H:%M:%S",
)
log = logging.getLogger("app")

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key              = config.SECRET_KEY
app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH

# ── Directory bootstrap ───────────────────────────────────────────────────────
for directory in [config.UPLOAD_FOLDER, "logs", "models"]:
    Path(directory).mkdir(parents=True, exist_ok=True)

# ── Model loading ─────────────────────────────────────────────────────────────
def _load_model():
    """
    Load YOLO model at startup.
    Supports multiple model types: military, dota, coco
    Model selection via MODEL_TYPE environment variable
    """
    from ultralytics import YOLO  # imported here so the import error is clear

    model_type = config.MODEL_TYPE
    
    # Determine which model to load
    if model_type == "dota":
        if os.path.exists(config.DOTA_MODEL_PATH):
            weights = config.DOTA_MODEL_PATH
            log.info("Loading DOTA aerial detection model: %s", weights)
        else:
            log.warning("DOTA model not found at '%s'. Falling back to COCO.", config.DOTA_MODEL_PATH)
            weights = config.COCO_MODEL_PATH
    
    elif model_type == "military":
        if os.path.exists(config.MILITARY_MODEL_PATH):
            weights = config.MILITARY_MODEL_PATH
            log.info("Loading military detection model: %s", weights)
        else:
            log.warning("Military model not found at '%s'. Falling back to COCO.", config.MILITARY_MODEL_PATH)
            weights = config.COCO_MODEL_PATH
    
    elif model_type == "coco":
        weights = config.COCO_MODEL_PATH
        log.info("Loading COCO pretrained model: %s", weights)
    
    else:  # auto - try to detect best available model
        if os.path.exists(config.MILITARY_MODEL_PATH):
            weights = config.MILITARY_MODEL_PATH
            log.info("Auto-detected military model: %s", weights)
        elif os.path.exists(config.DOTA_MODEL_PATH):
            weights = config.DOTA_MODEL_PATH
            log.info("Auto-detected DOTA model: %s", weights)
        else:
            weights = config.COCO_MODEL_PATH
            log.warning(
                "No custom models found. "
                "Falling back to '%s' (COCO pre-trained). "
                "Train a custom model for better results.",
                weights,
            )

    model = YOLO(weights)
    # Warm-up inference to pre-allocate GPU memory and JIT compile layers
    import numpy as np
    dummy = np.zeros((640, 640, 3), dtype=np.uint8)
    model.predict(source=dummy, verbose=False)
    log.info("Model ready ✓  (device: %s)", model.device)
    return model


log.info("Loading YOLO model — this may take a moment …")
MODEL = _load_model()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _allowed_file(filename: str) -> bool:
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS
    )


def _unique_filename(filename: str) -> str:
    """Prefix with a UUID to avoid collisions and path-traversal issues."""
    stem = Path(secure_filename(filename)).stem[:40]  # truncate long names
    ext  = Path(secure_filename(filename)).suffix
    return f"{uuid.uuid4().hex[:8]}_{stem}{ext}"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the single-page frontend."""
    return render_template("index.html")


@app.route("/detect", methods=["POST"])
def detect():
    """
    POST /detect
    ------------
    Accepts a multipart/form-data image upload.
    Returns JSON:
        {
          "success": true,
          "detections": [...],
          "threat": {...},
          "annotated_path": "/static/uploads/annotated_xxx.jpg",
          "inference_ms": 42.1,
          "image_size": {"width": 1280, "height": 720}
        }
    """
    # ── Validate upload ────────────────────────────────────────────────────
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image field in request."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected."}), 400

    if not _allowed_file(file.filename):
        return jsonify({
            "success": False,
            "error": f"File type not allowed. Accepted: {', '.join(config.ALLOWED_EXTENSIONS)}",
        }), 415

    # ── Save original upload ───────────────────────────────────────────────
    unique_name  = _unique_filename(file.filename)
    save_path    = os.path.join(config.UPLOAD_FOLDER, unique_name)
    file.save(save_path)
    log.info("Image saved: %s", save_path)

    # ── Extract GPS data if present ────────────────────────────────────────
    geo_data = extract_gps(save_path)

    # ── Run detection ──────────────────────────────────────────────────────
    try:
        result = run_detection(MODEL, save_path)
    except Exception as exc:
        log.exception("Detection failed for %s", save_path)
        return jsonify({"success": False, "error": str(exc)}), 500

    # ── Threat assessment ──────────────────────────────────────────────────
    threat = check_threat(result["detections"])

    # ── Log to CSV ─────────────────────────────────────────────────────────
    log_detections(
        image_filename = unique_name,
        detections     = result["detections"],
        threat_report  = threat,
        inference_ms   = result["inference_ms"],
    )

    # ── Generate AI SITREP ─────────────────────────────────────────────
    scan_id = unique_name.split('_')[0]  # Use first part of filename as scan ID
    sitrep_result = {"success": False, "error": "Analyst disabled"}
    
    if config.ANALYST_ENABLED:
        # Build full detection data for analyst
        detection_data = {
            "detections": result["detections"],
            "threat": threat,
            "annotated_path": result["annotated_path"],
            "inference_ms": result["inference_ms"],
            "image_size": result["image_size"],
            "original_path": f"/static/uploads/{unique_name}"
        }
        
        # Generate SITREP
        sitrep_result = generate_sitrep(detection_data)
        
        # Store SITREP if successful
        if sitrep_result["success"]:
            detection_context = build_detection_context(detection_data)
            get_store().save_sitrep(
                scan_id=scan_id,
                detection_context=detection_context,
                sitrep=sitrep_result["sitrep"],
                model=sitrep_result["model"],
                tokens=sitrep_result["tokens"]
            )

    # ── Build response ─────────────────────────────────────────────────
    return jsonify({
        "success":        True,
        "detections":     result["detections"],
        "threat":         threat,
        "annotated_path": result["annotated_path"],
        "inference_ms":   result["inference_ms"],
        "image_size":     result["image_size"],
        "original_path":  f"/static/uploads/{unique_name}",
        "scan_id":        scan_id,
        "sitrep":         sitrep_result,
        "analyst_enabled": config.ANALYST_ENABLED,
        "geo":            geo_data
    })


@app.route("/logs")
def logs():
    """GET /logs — return the 50 most recent detection log rows as JSON."""
    rows = get_recent_logs(limit=50)
    return jsonify({"success": True, "logs": rows})


@app.route("/health")
def health():
    """GET /health — simple health check / readiness probe."""
    return jsonify({
        "status":      "ok",
        "model_ready": MODEL is not None,
        "device":      str(MODEL.device) if MODEL else "none",
    })


@app.route("/dashboard")
def dashboard():
    """GET /dashboard — serve the intelligence dashboard page."""
    return render_template("dashboard.html")


@app.route("/globe")
def globe():
    """GET /globe — serve the 3D globe geo-intelligence page."""
    return render_template("globe.html")


@app.route("/api/dashboard-data")
def dashboard_data():
    """GET /api/dashboard-data — return analytics data as JSON."""
    from services.analytics import compute_dashboard_data
    data = compute_dashboard_data()
    return jsonify({"success": True, "data": data})


@app.route("/api/export-csv")
def export_csv():
    """GET /api/export-csv — download the full detection log CSV."""
    if not os.path.exists(config.LOG_PATH):
        return jsonify({"success": False, "error": "No log file found"}), 404
    return send_from_directory(
        os.path.dirname(config.LOG_PATH),
        os.path.basename(config.LOG_PATH),
        as_attachment=True,
        download_name="aegis_detections.csv",
        mimetype="text/csv"
    )


@app.route("/api/sitrep/<scan_id>")
def get_sitrep(scan_id):
    """GET /api/sitrep/<scan_id> — retrieve SITREP for a specific scan."""
    sitrep_data = get_store().get_sitrep(scan_id)
    
    if not sitrep_data:
        return jsonify({"success": False, "error": "SITREP not found"}), 404
    
    return jsonify({
        "success": True,
        "scan_id": scan_id,
        "sitrep": sitrep_data.get("sitrep", ""),
        "model": sitrep_data.get("model", ""),
        "tokens": sitrep_data.get("tokens", 0),
        "timestamp": sitrep_data.get("timestamp", "")
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    """POST /api/chat — handle follow-up questions about a scan."""
    data = request.get_json()
    
    if not data:
        return jsonify({"success": False, "error": "No JSON data provided"}), 400
    
    scan_id = data.get("scan_id")
    message = data.get("message")
    
    if not scan_id or not message:
        return jsonify({"success": False, "error": "Missing scan_id or message"}), 400
    
    # Retrieve SITREP data
    sitrep_data = get_store().get_sitrep(scan_id)
    
    if not sitrep_data:
        return jsonify({"success": False, "error": "Scan not found"}), 404
    
    # Get chat history
    chat_history = get_store().get_chat_history(scan_id)
    
    # Call analyst
    response = analyst_chat(
        scan_id=scan_id,
        user_message=message,
        detection_context=sitrep_data.get("detection_context", ""),
        sitrep=sitrep_data.get("sitrep", ""),
        chat_history=chat_history
    )
    
    if response["success"]:
        # Store messages in history
        get_store().add_chat_message(scan_id, "user", message)
        get_store().add_chat_message(scan_id, "assistant", response["answer"])
    
    return jsonify(response)


# ── Dev server ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    log.info("Starting Military Detection System on http://%s:%s", config.HOST, config.PORT)
    app.run(
        host  = config.HOST,
        port  = config.PORT,
        debug = config.DEBUG,
        use_reloader = False,   # disable reloader so model loads only once
    )
