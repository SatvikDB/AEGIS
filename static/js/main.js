/**
 * main.js
 * -------
 * Frontend controller for the AEGIS Military Detection System.
 *
 * Responsibilities:
 *  - Real-time UTC clock
 *  - Image drag-and-drop / file picker
 *  - POSTing image to /detect via Fetch API
 *  - Rendering detection results, threat banner, stats bar
 *  - Fetching & rendering session log table
 *  - Animated progress bar during inference
 */

"use strict";

/* ── DOM references ──────────────────────────────────────────────── */
const $ = id => document.getElementById(id);

const modeToggle     = $("modeToggle");
const uploadMode     = $("uploadMode");
const cameraMode     = $("cameraMode");
const dropZone       = $("dropZone");
const fileInput      = $("fileInput");
const browseBtn      = $("browseBtn");
const cameraVideo    = $("cameraVideo");
const cameraCanvas   = $("cameraCanvas");
const startCameraBtn = $("startCameraBtn");
const captureBtn     = $("captureBtn");
const stopCameraBtn  = $("stopCameraBtn");
const analyseBtn     = $("analyseBtn");
const previewWrap    = $("previewWrap");
const previewImg     = $("previewImg");
const previewMeta    = $("previewMeta");
const progressBar    = $("progressBar");
const progressFill   = $("progressFill");
const progressLabel  = $("progressLabel");
const viewerPlaceholder = $("viewerPlaceholder");
const annotatedImg   = $("annotatedImg");
const statsBar       = $("statsBar");
const statTotal      = $("statTotal");
const statHigh       = $("statHigh");
const statInfer      = $("statInfer");
const statRes        = $("statRes");
const threatBanner   = $("threatBanner");
const threatIcon     = $("threatIcon");
const threatLevel    = $("threatLevel");
const threatDesc     = $("threatDesc");
const detList        = $("detList");
const detectionCount = $("detectionCount");
const logTableWrap   = $("logTableWrap");
const statusPill     = $("statusPill");
const statusText     = $("statusText");
const downloadBtn    = $("downloadBtn");
const refreshLogsBtn = $("refreshLogsBtn");
const clockEl        = $("clock");

/* ── State ───────────────────────────────────────────────────────── */
let selectedFile  = null;
let isProcessing  = false;
let progressTimer = null;
let cameraStream  = null;
let currentMode   = "upload";

/* ── UTC clock ───────────────────────────────────────────────────── */
function updateClock() {
  const now = new Date();
  const hh  = String(now.getUTCHours()).padStart(2, "0");
  const mm  = String(now.getUTCMinutes()).padStart(2, "0");
  const ss  = String(now.getUTCSeconds()).padStart(2, "0");
  clockEl.textContent = `${hh}:${mm}:${ss} UTC`;
}
setInterval(updateClock, 1000);
updateClock();

/* ── Status helpers ──────────────────────────────────────────────── */
function setStatus(state, text) {
  // state: 'ready' | 'busy' | 'alert'
  statusPill.className = "status-pill" + (state !== "ready" ? ` status--${state}` : "");
  statusText.textContent = text;
}

/* ── Mode toggle ─────────────────────────────────────────────────── */
modeToggle.addEventListener("click", (e) => {
  if (e.target.classList.contains("mode-btn")) {
    const mode = e.target.dataset.mode;
    switchMode(mode);
  }
});

function switchMode(mode) {
  if (mode === currentMode) return;
  
  currentMode = mode;
  
  // Update button states
  document.querySelectorAll(".mode-btn").forEach(btn => {
    btn.classList.toggle("mode-btn--active", btn.dataset.mode === mode);
  });
  
  // Switch UI
  if (mode === "upload") {
    uploadMode.classList.remove("hidden");
    cameraMode.classList.add("hidden");
    stopCamera();
  } else {
    uploadMode.classList.add("hidden");
    cameraMode.classList.remove("hidden");
  }
  
  // Reset state
  selectedFile = null;
  analyseBtn.disabled = true;
  previewWrap.classList.add("hidden");
  setStatus("ready", "SYSTEM READY");
}

/* ── Camera controls ─────────────────────────────────────────────── */
startCameraBtn.addEventListener("click", startCamera);
stopCameraBtn.addEventListener("click", stopCamera);
captureBtn.addEventListener("click", captureImage);

async function startCamera() {
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "environment", width: { ideal: 1280 }, height: { ideal: 720 } }
    });
    
    cameraVideo.srcObject = cameraStream;
    cameraVideo.classList.remove("hidden");
    cameraCanvas.classList.add("hidden");
    
    startCameraBtn.classList.add("hidden");
    captureBtn.classList.remove("hidden");
    stopCameraBtn.classList.remove("hidden");
    
    setStatus("ready", "CAMERA ACTIVE");
  } catch (err) {
    console.error("Camera error:", err);
    alert("Could not access camera. Please check permissions.");
    setStatus("ready", "CAMERA ERROR");
  }
}

function stopCamera() {
  if (cameraStream) {
    cameraStream.getTracks().forEach(track => track.stop());
    cameraStream = null;
  }
  
  cameraVideo.srcObject = null;
  cameraVideo.classList.add("hidden");
  
  startCameraBtn.classList.remove("hidden");
  captureBtn.classList.add("hidden");
  stopCameraBtn.classList.add("hidden");
  
  if (currentMode === "camera") {
    setStatus("ready", "CAMERA STOPPED");
  }
}

function captureImage() {
  if (!cameraStream) return;
  
  // Set canvas size to match video
  cameraCanvas.width = cameraVideo.videoWidth;
  cameraCanvas.height = cameraVideo.videoHeight;
  
  // Draw current frame to canvas
  const ctx = cameraCanvas.getContext("2d");
  ctx.drawImage(cameraVideo, 0, 0);
  
  // Convert to blob
  cameraCanvas.toBlob((blob) => {
    if (!blob) {
      alert("Failed to capture image");
      return;
    }
    
    // Create file from blob
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    selectedFile = new File([blob], `camera_capture_${timestamp}.jpg`, { type: "image/jpeg" });
    
    // Show preview
    const url = URL.createObjectURL(blob);
    previewImg.src = url;
    previewWrap.classList.remove("hidden");
    previewMeta.textContent = `Camera Capture  ·  ${(blob.size / 1024).toFixed(1)} KB  ·  ${cameraCanvas.width}×${cameraCanvas.height}`;
    
    // Show canvas instead of video
    cameraVideo.classList.add("hidden");
    cameraCanvas.classList.remove("hidden");
    
    analyseBtn.disabled = false;
    setStatus("ready", "IMAGE CAPTURED");
  }, "image/jpeg", 0.92);
}

/* ── File selection ──────────────────────────────────────────────── */
browseBtn.addEventListener("click", () => fileInput.click());
dropZone.addEventListener("click", e => {
  if (e.target !== browseBtn) fileInput.click();
});

fileInput.addEventListener("change", () => {
  if (fileInput.files.length > 0) handleFile(fileInput.files[0]);
});

/* Drag-and-drop */
["dragenter", "dragover"].forEach(evt => {
  dropZone.addEventListener(evt, e => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });
});

["dragleave", "drop"].forEach(evt => {
  dropZone.addEventListener(evt, e => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
  });
});

dropZone.addEventListener("drop", e => {
  const dt   = e.dataTransfer;
  const file = dt.files[0];
  if (file) handleFile(file);
});

function handleFile(file) {
  if (!file.type.startsWith("image/")) {
    alert("Please select a valid image file.");
    return;
  }
  selectedFile = file;

  // Show preview
  const url = URL.createObjectURL(file);
  previewImg.src = url;
  previewWrap.classList.remove("hidden");
  
  // Show original filename, truncate if too long
  const displayName = file.name.length > 30 
    ? file.name.substring(0, 27) + "..." 
    : file.name;
  previewMeta.textContent =
    `${displayName}  ·  ${(file.size / 1024).toFixed(1)} KB  ·  ${file.type}`;

  analyseBtn.disabled = false;
  setStatus("ready", "IMAGE LOADED");
}

/* ── Analyse button ──────────────────────────────────────────────── */
analyseBtn.addEventListener("click", runDetection);

async function runDetection() {
  if (!selectedFile || isProcessing) return;

  isProcessing = true;
  analyseBtn.disabled = true;
  setStatus("busy", "PROCESSING…");

  // Reset UI
  annotatedImg.classList.add("hidden");
  viewerPlaceholder.classList.remove("hidden");
  statsBar.classList.add("hidden");
  downloadBtn.disabled = true;

  // Show progress bar
  progressBar.classList.remove("hidden");
  animateProgress(0, 40, 800, "Uploading image…");

  const formData = new FormData();
  formData.append("image", selectedFile);

  let data;
  try {
    animateProgress(40, 75, 1200, "Running YOLO inference…");

    const response = await fetch("/detect", {
      method: "POST",
      body:   formData,
    });

    animateProgress(75, 95, 400, "Processing results…");

    data = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(data.error || `Server error ${response.status}`);
    }
  } catch (err) {
    console.error("Detection error:", err);
    setStatus("ready", "ERROR — RETRY");
    finishProgress(false, err.message);
    isProcessing = false;
    analyseBtn.disabled = false;
    return;
  }

  animateProgress(95, 100, 200, "Complete");
  setTimeout(() => {
    progressBar.classList.add("hidden");
    clearInterval(progressTimer);

    renderResults(data);
    isProcessing = false;
    analyseBtn.disabled = false;
    fetchLogs();
  }, 400);
}

/* ── Progress animation ──────────────────────────────────────────── */
function animateProgress(from, to, duration, label) {
  clearInterval(progressTimer);
  progressLabel.textContent = label;
  const steps  = 30;
  const delay  = duration / steps;
  const delta  = (to - from) / steps;
  let current  = from;
  progressFill.style.width = `${from}%`;

  progressTimer = setInterval(() => {
    current += delta;
    if (current >= to) {
      current = to;
      clearInterval(progressTimer);
    }
    progressFill.style.width = `${current}%`;
  }, delay);
}

function finishProgress(success, message = "") {
  clearInterval(progressTimer);
  progressFill.style.width = "100%";
  progressLabel.textContent = success ? "Complete" : `Error: ${message}`;
  setTimeout(() => progressBar.classList.add("hidden"), 1500);
}

/* ── Render detection results ────────────────────────────────────── */
function renderResults(data) {
  const { detections, threat, annotated_path, inference_ms, image_size } = data;

  // ── Annotated image ──────────────────────────────────────────────
  annotatedImg.src = annotated_path + "?t=" + Date.now();  // bust cache
  annotatedImg.classList.remove("hidden");
  viewerPlaceholder.classList.add("hidden");

  // Download button
  downloadBtn.disabled = false;
  downloadBtn.onclick = () => {
    const a = document.createElement("a");
    a.href     = annotated_path;
    a.download = "aegis_annotated.jpg";
    a.click();
  };

  // ── Stats bar ────────────────────────────────────────────────────
  statTotal.textContent = detections.length;
  statHigh.textContent  = threat.stats.high_risk;
  statInfer.textContent = `${inference_ms} ms`;
  statRes.textContent   = `${image_size.width}×${image_size.height}`;
  statsBar.classList.remove("hidden");

  // ── Threat banner ────────────────────────────────────────────────
  threatBanner.className = `threat-banner threat--${threat.threat_level}`;
  threatIcon.textContent  = threat.icon;
  threatLevel.textContent = threat.label;
  threatDesc.textContent  = threat.description;

  // Update header status
  if (threat.threat_level === "CRITICAL" || threat.threat_level === "HIGH") {
    setStatus("alert", threat.label);
  } else {
    setStatus("ready", "SCAN COMPLETE");
  }

  // ── Detection list ───────────────────────────────────────────────
  detList.innerHTML = "";

  if (detections.length === 0) {
    detList.innerHTML = '<li class="det-list__empty">No objects detected.</li>';
    detectionCount.textContent = "";
    return;
  }

  // Update detection count badge
  detectionCount.textContent = `[${detections.length}]`;

  detections.forEach(det => {
    const li = document.createElement("li");
    li.className = `det-item det-item--${det.risk_level}`;
    
    // Add warning symbol for high-risk items
    const warningPrefix = det.risk_level === "high" ? "⚠ " : "";
    
    li.innerHTML = `
      <div class="det-item__risk"></div>
      <span class="det-item__name">${warningPrefix}${escHtml(det.class_name)}</span>
      <span class="det-item__conf">${(det.confidence * 100).toFixed(1)}%</span>
      <span class="det-item__box">${det.box.width}×${det.box.height}</span>
    `;
    li.title = `Box: (${det.box.x1}, ${det.box.y1}) → (${det.box.x2}, ${det.box.y2})`;
    detList.appendChild(li);
  });

  // Scroll detection list to top so threat banner is visible
  detList.scrollTop = 0;

  // ── AI Tactical Analyst ──────────────────────────────────────────
  // Call analyst.js to fetch and display SITREP
  if (typeof renderAnalyst === "function") {
    renderAnalyst(data);
  }

  // ── Geo-Intelligence ─────────────────────────────────────────────
  // Call geo.js to display GPS location if present
  console.log('Geo data received:', data.geo);
  if (typeof renderGeo === "function" && data.geo) {
    renderGeo(data.geo);
  }
}

/* ── Session log ─────────────────────────────────────────────────── */
refreshLogsBtn.addEventListener("click", fetchLogs);

async function fetchLogs() {
  try {
    const res  = await fetch("/logs");
    const data = await res.json();
    if (!data.success || !data.logs.length) {
      logTableWrap.innerHTML = '<p class="log-empty">No session logs yet.</p>';
      return;
    }
    renderLogTable(data.logs);
  } catch {
    logTableWrap.innerHTML = '<p class="log-empty">Could not load logs.</p>';
  }
}

function renderLogTable(rows) {
  // Show most recent 15 rows
  const recent = rows.slice(-15).reverse();

  const table = document.createElement("table");
  table.className = "log-table";

  table.innerHTML = `
    <thead>
      <tr>
        <th>TIME</th>
        <th>CLASS</th>
        <th>CONF</th>
        <th>RISK</th>
        <th>THREAT</th>
      </tr>
    </thead>
    <tbody>
      ${recent.map(r => `
        <tr>
          <td>${(r.timestamp || "").slice(11, 19)}</td>
          <td>${escHtml(r.class_name || "—")}</td>
          <td>${r.confidence !== undefined ? (parseFloat(r.confidence) * 100).toFixed(0) + "%" : "—"}</td>
          <td>${escHtml(r.risk_level || "—")}</td>
          <td><span class="badge badge--${r.threat_level}">${escHtml(r.threat_level || "—")}</span></td>
        </tr>
      `).join("")}
    </tbody>
  `;

  logTableWrap.innerHTML = "";
  logTableWrap.appendChild(table);
}

/* ── Utils ───────────────────────────────────────────────────────── */
function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/* ── Initial log fetch ────────────────────────────────────────────── */
fetchLogs();

/* ── Cleanup on page unload ───────────────────────────────────────── */
window.addEventListener("beforeunload", () => {
  stopCamera();
});
