/**
 * dashboard.js
 * ------------
 * Intelligence Dashboard controller for AEGIS.
 * Fetches analytics data and renders charts, heatmaps, and tables.
 */

"use strict";

/* ── DOM references ──────────────────────────────────────────────── */
const $ = id => document.getElementById(id);

const clockEl = $("clock");
const lastUpdated = $("lastUpdated");
const exportCsvBtn = $("exportCsvBtn");
const exportJsonBtn = $("exportJsonBtn");
const refreshBtn = $("refreshBtn");

const statTotalScans = $("statTotalScans");
const statTotalDetections = $("statTotalDetections");
const statCriticalToday = $("statCriticalToday");
const statMostDetected = $("statMostDetected");

const recentTableBody = $("recentTableBody");

/* ── State ───────────────────────────────────────────────────────── */
let charts = {};
let currentData = null;
let sortColumn = "timestamp";
let sortAscending = false;

/* ── UTC clock ───────────────────────────────────────────────────── */
function updateClock() {
  const now = new Date();
  const hh = String(now.getUTCHours()).padStart(2, "0");
  const mm = String(now.getUTCMinutes()).padStart(2, "0");
  const ss = String(now.getUTCSeconds()).padStart(2, "0");
  clockEl.textContent = `${hh}:${mm}:${ss} UTC`;
}
setInterval(updateClock, 1000);
updateClock();

/* ── Chart.js global config ──────────────────────────────────────── */
Chart.defaults.color = "#c8ffda";
Chart.defaults.borderColor = "rgba(0,255,110,0.1)";
Chart.defaults.backgroundColor = "rgba(0,255,110,0.2)";
Chart.defaults.font.family = "'Rajdhani', sans-serif";
Chart.defaults.font.size = 12;

/* ── Fetch dashboard data ────────────────────────────────────────── */
async function fetchDashboardData() {
  try {
    const response = await fetch("/api/dashboard-data");
    const json = await response.json();
    
    if (!json.success) {
      throw new Error("Failed to fetch dashboard data");
    }
    
    currentData = json.data;
    renderDashboard(currentData);
    updateLastUpdatedTime();
  } catch (err) {
    console.error("Dashboard data fetch error:", err);
    alert("Failed to load dashboard data. Check console for details.");
  }
}

function updateLastUpdatedTime() {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  const ss = String(now.getSeconds()).padStart(2, "0");
  lastUpdated.textContent = `${hh}:${mm}:${ss}`;
}

/* ── Render dashboard ────────────────────────────────────────────── */
function renderDashboard(data) {
  renderSummaryStats(data.summary);
  renderThreatChart(data.threat_distribution);
  renderTopClassesChart(data.top_classes);
  renderTimelineChart(data.detections_over_time);
  renderHeatmap(data.hourly_heatmap);
  renderConfidenceChart(data.confidence_histogram);
  renderRecentTable(data.recent_rows);
}

/* ── Summary stats ───────────────────────────────────────────────── */
function renderSummaryStats(summary) {
  statTotalScans.textContent = summary.total_scans.toLocaleString();
  statTotalDetections.textContent = summary.total_detections.toLocaleString();
  statCriticalToday.textContent = summary.critical_today.toLocaleString();
  statMostDetected.textContent = summary.most_detected_class;
}

/* ── Threat distribution doughnut chart ──────────────────────────── */
function renderThreatChart(distribution) {
  const ctx = $("threatChart");
  
  if (charts.threat) {
    charts.threat.destroy();
  }
  
  const data = {
    labels: ["CRITICAL", "HIGH", "ELEVATED", "LOW", "CLEAR"],
    datasets: [{
      data: [
        distribution.CRITICAL,
        distribution.HIGH,
        distribution.ELEVATED,
        distribution.LOW,
        distribution.CLEAR
      ],
      backgroundColor: [
        "#ff1744",
        "#ff6d00",
        "#ffd600",
        "#00e676",
        "#40c4ff"
      ],
      borderWidth: 2,
      borderColor: "#050a07"
    }]
  };
  
  charts.threat = new Chart(ctx, {
    type: "doughnut",
    data: data,
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: "right",
          labels: {
            color: "#c8ffda",
            padding: 15,
            font: { size: 13 }
          }
        }
      }
    }
  });
}

/* ── Top classes horizontal bar chart ────────────────────────────── */
function renderTopClassesChart(topClasses) {
  const ctx = $("topClassesChart");
  
  if (charts.topClasses) {
    charts.topClasses.destroy();
  }
  
  const labels = topClasses.map(c => c.class_name);
  const counts = topClasses.map(c => c.count);
  const colors = topClasses.map(c => {
    if (c.risk === "high") return "#ff1744";
    if (c.risk === "medium") return "#ff6d00";
    return "#00e676";
  });
  
  charts.topClasses = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Detections",
        data: counts,
        backgroundColor: colors,
        borderWidth: 0
      }]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { color: "rgba(0,255,110,0.1)" },
          ticks: { color: "#7aad8c" }
        },
        y: {
          grid: { display: false },
          ticks: { color: "#c8ffda", font: { size: 11 } }
        }
      }
    }
  });
}

/* ── Timeline line chart ─────────────────────────────────────────── */
function renderTimelineChart(timeline) {
  const ctx = $("timelineChart");
  
  if (charts.timeline) {
    charts.timeline.destroy();
  }
  
  const labels = timeline.map(d => {
    const date = new Date(d.date);
    return `${date.getDate()}/${date.getMonth() + 1}`;
  });
  const counts = timeline.map(d => d.count);
  
  charts.timeline = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [{
        label: "Detections",
        data: counts,
        borderColor: "#00ff6e",
        backgroundColor: "rgba(0,255,110,0.15)",
        fill: true,
        tension: 0.3,
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: "#00ff6e"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { color: "rgba(0,255,110,0.08)" },
          ticks: { color: "#7aad8c", maxRotation: 45, minRotation: 0 }
        },
        y: {
          grid: { color: "rgba(0,255,110,0.1)" },
          ticks: { color: "#7aad8c", precision: 0 },
          beginAtZero: true
        }
      }
    }
  });
}

/* ── Heatmap ─────────────────────────────────────────────────────── */
function renderHeatmap(heatmapData) {
  const container = $("heatmapContainer");
  container.innerHTML = "";
  
  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const hours = Array.from({ length: 24 }, (_, i) => i);
  
  // Find max count for intensity scaling
  let maxCount = 0;
  days.forEach(day => {
    hours.forEach(hour => {
      const count = heatmapData[day][hour];
      if (count > maxCount) maxCount = count;
    });
  });
  
  // Header row (hours)
  container.appendChild(createDiv("heatmap-label", ""));
  hours.forEach(hour => {
    const label = createDiv("heatmap-label", hour.toString().padStart(2, "0"));
    container.appendChild(label);
  });
  
  // Data rows
  days.forEach(day => {
    // Day label
    container.appendChild(createDiv("heatmap-label", day));
    
    // Hour cells
    hours.forEach(hour => {
      const count = heatmapData[day][hour];
      const intensity = maxCount > 0 ? Math.ceil((count / maxCount) * 5) : 0;
      
      const cell = createDiv("heatmap-cell", "");
      cell.dataset.count = count;
      cell.dataset.intensity = intensity;
      cell.title = `${day} ${hour.toString().padStart(2, "0")}:00 — ${count} detection${count !== 1 ? "s" : ""}`;
      
      container.appendChild(cell);
    });
  });
}

function createDiv(className, text) {
  const div = document.createElement("div");
  div.className = className;
  div.textContent = text;
  return div;
}

/* ── Confidence histogram ────────────────────────────────────────── */
function renderConfidenceChart(histogram) {
  const ctx = $("confidenceChart");
  
  if (charts.confidence) {
    charts.confidence.destroy();
  }
  
  const labels = histogram.map(h => h.bin);
  const counts = histogram.map(h => h.count);
  
  charts.confidence = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Detections",
        data: counts,
        backgroundColor: "#00cc55",
        borderWidth: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: "#7aad8c", maxRotation: 45 }
        },
        y: {
          grid: { color: "rgba(0,255,110,0.1)" },
          ticks: { color: "#7aad8c", precision: 0 },
          beginAtZero: true
        }
      }
    }
  });
}

/* ── Recent detections table ─────────────────────────────────────── */
function renderRecentTable(rows) {
  if (!rows || rows.length === 0) {
    recentTableBody.innerHTML = '<tr><td colspan="6" class="table-empty">No detections logged yet.</td></tr>';
    return;
  }
  
  recentTableBody.innerHTML = "";
  
  rows.forEach(row => {
    const tr = document.createElement("tr");
    
    const timestamp = row.timestamp ? row.timestamp.slice(0, 19) : "—";
    const image = row.image_filename || "—";
    const className = row.class_name || "—";
    const confidence = row.confidence ? (parseFloat(row.confidence) * 100).toFixed(1) + "%" : "—";
    const riskLevel = row.risk_level || "—";
    const threatLevel = row.threat_level || "—";
    
    tr.innerHTML = `
      <td>${escHtml(timestamp)}</td>
      <td>${escHtml(image)}</td>
      <td>${escHtml(className)}</td>
      <td>${confidence}</td>
      <td><span class="table-badge table-badge--${riskLevel}">${escHtml(riskLevel.toUpperCase())}</span></td>
      <td><span class="table-badge table-badge--${threatLevel}">${escHtml(threatLevel)}</span></td>
    `;
    
    recentTableBody.appendChild(tr);
  });
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/* ── Table sorting ───────────────────────────────────────────────── */
document.querySelectorAll(".dashboard-table th[data-sort]").forEach(th => {
  th.addEventListener("click", () => {
    const column = th.dataset.sort;
    
    if (sortColumn === column) {
      sortAscending = !sortAscending;
    } else {
      sortColumn = column;
      sortAscending = false;
    }
    
    sortTable(column, sortAscending);
    
    // Update sort indicators
    document.querySelectorAll(".dashboard-table th").forEach(h => {
      h.textContent = h.textContent.replace(" ▼", "").replace(" ▲", "");
    });
    th.textContent += sortAscending ? " ▲" : " ▼";
  });
});

function sortTable(column, ascending) {
  if (!currentData || !currentData.recent_rows) return;
  
  const rows = [...currentData.recent_rows];
  
  rows.sort((a, b) => {
    let valA = a[column];
    let valB = b[column];
    
    // Handle numeric columns
    if (column === "confidence") {
      valA = parseFloat(valA) || 0;
      valB = parseFloat(valB) || 0;
    }
    
    if (valA < valB) return ascending ? -1 : 1;
    if (valA > valB) return ascending ? 1 : -1;
    return 0;
  });
  
  currentData.recent_rows = rows;
  renderRecentTable(rows);
}

/* ── Export buttons ──────────────────────────────────────────────── */
exportCsvBtn.addEventListener("click", () => {
  window.location.href = "/api/export-csv";
});

exportJsonBtn.addEventListener("click", () => {
  if (!currentData) {
    alert("No data to export");
    return;
  }
  
  const dataStr = JSON.stringify(currentData, null, 2);
  const blob = new Blob([dataStr], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  
  const a = document.createElement("a");
  a.href = url;
  a.download = `aegis_dashboard_${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  
  URL.revokeObjectURL(url);
});

refreshBtn.addEventListener("click", fetchDashboardData);

/* ── Auto-refresh every 30 seconds ───────────────────────────────── */
setInterval(fetchDashboardData, 30000);

/* ── Initial load ────────────────────────────────────────────────── */
fetchDashboardData();
