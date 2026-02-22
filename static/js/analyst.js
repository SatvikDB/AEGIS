/**
 * analyst.js
 * ----------
 * AI Tactical Analyst frontend controller for AEGIS.
 *
 * Responsibilities:
 *  - Fetch and display SITREP with typewriter effect
 *  - Handle chat interactions with the analyst
 *  - Maintain conversation context per scan
 */

"use strict";

/* ── DOM references ──────────────────────────────────────────────── */
const analystPanel = document.getElementById("analystPanel");
const analystSitrep = document.getElementById("analystSitrep");
const chatMessages = document.getElementById("chatMessages");
const chatInput = document.getElementById("chatInput");
const sendChatBtn = document.getElementById("sendChatBtn");
const clearChatBtn = document.getElementById("clearChatBtn");

/* ── State ───────────────────────────────────────────────────────── */
let currentScanId = null;
let isTyping = false;
let isChatting = false;

/* ── Main entry point ────────────────────────────────────────────── */
/**
 * Called from main.js after detection completes
 * @param {Object} data - Detection response data
 */
function renderAnalyst(data) {
  if (!data.scan_id) {
    console.warn("No scan_id in detection response");
    return;
  }

  currentScanId = data.scan_id;
  
  // Show analyst panel
  analystPanel.classList.remove("hidden");
  
  // Reset state
  analystSitrep.innerHTML = `
    <div class="analyst-sitrep__loading">
      <div class="loading-spinner"></div>
      <span>Generating tactical assessment...</span>
    </div>
  `;
  chatMessages.innerHTML = "";
  chatInput.value = "";
  chatInput.disabled = true;
  sendChatBtn.disabled = true;
  
  // Fetch SITREP
  fetchSitrep(currentScanId);
}

/* ── Fetch SITREP ────────────────────────────────────────────────── */
async function fetchSitrep(scanId) {
  try {
    const response = await fetch(`/api/sitrep/${scanId}`);
    const data = await response.json();
    
    if (!response.ok || !data.success) {
      throw new Error(data.error || "Failed to fetch SITREP");
    }
    
    displaySitrep(data.sitrep);
    
  } catch (err) {
    console.error("SITREP fetch error:", err);
    analystSitrep.innerHTML = `
      <div class="analyst-empty">
        <div class="analyst-empty__icon">⚠</div>
        <div>Failed to generate tactical assessment</div>
        <div style="font-size: 0.7rem; opacity: 0.7;">${escapeHtml(err.message)}</div>
      </div>
    `;
  }
}

/* ── Display SITREP with typewriter effect ──────────────────────── */
function displaySitrep(text) {
  if (!text) {
    analystSitrep.innerHTML = `
      <div class="analyst-empty">
        <div class="analyst-empty__icon">◈</div>
        <div>No assessment available</div>
      </div>
    `;
    return;
  }
  
  // Create content container
  const contentDiv = document.createElement("div");
  contentDiv.className = "analyst-sitrep__content";
  analystSitrep.innerHTML = "";
  analystSitrep.appendChild(contentDiv);
  
  // Typewriter effect
  isTyping = true;
  let index = 0;
  const speed = 8; // milliseconds per character
  
  function typeChar() {
    if (index < text.length) {
      contentDiv.textContent = text.substring(0, index + 1);
      index++;
      setTimeout(typeChar, speed);
    } else {
      // Typing complete
      isTyping = false;
      contentDiv.classList.add("typing-complete");
      
      // Enable chat
      chatInput.disabled = false;
      sendChatBtn.disabled = false;
      chatInput.focus();
    }
  }
  
  typeChar();
}

/* ── Chat functionality ──────────────────────────────────────────── */
sendChatBtn.addEventListener("click", sendMessage);
chatInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

clearChatBtn.addEventListener("click", () => {
  chatMessages.innerHTML = "";
  chatInput.value = "";
});

async function sendMessage() {
  const message = chatInput.value.trim();
  if (!message || isChatting || !currentScanId) return;
  
  // Add user message to chat
  addChatMessage(message, "user");
  chatInput.value = "";
  
  // Show loading indicator
  const loadingId = addChatMessage("Analyzing...", "loading");
  
  isChatting = true;
  chatInput.disabled = true;
  sendChatBtn.disabled = true;
  
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scan_id: currentScanId,
        message: message
      })
    });
    
    const data = await response.json();
    
    // Remove loading indicator
    removeChatMessage(loadingId);
    
    if (!response.ok || !data.success) {
      throw new Error(data.error || "Chat request failed");
    }
    
    // Add analyst response (backend returns "answer" not "response")
    addChatMessage(data.answer, "analyst");
    
  } catch (err) {
    console.error("Chat error:", err);
    removeChatMessage(loadingId);
    addChatMessage(`Error: ${err.message}`, "error");
  } finally {
    isChatting = false;
    chatInput.disabled = false;
    sendChatBtn.disabled = false;
    chatInput.focus();
  }
}

/* ── Chat message helpers ────────────────────────────────────────── */
function addChatMessage(text, type) {
  const messageDiv = document.createElement("div");
  const messageId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  messageDiv.id = messageId;
  messageDiv.className = `chat-message chat-message--${type}`;
  messageDiv.textContent = text;
  
  chatMessages.appendChild(messageDiv);
  
  // Scroll to bottom
  chatMessages.scrollTop = chatMessages.scrollHeight;
  
  return messageId;
}

function removeChatMessage(messageId) {
  const messageDiv = document.getElementById(messageId);
  if (messageDiv) {
    messageDiv.remove();
  }
}

/* ── Utils ───────────────────────────────────────────────────────── */
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/* ── Export for main.js ──────────────────────────────────────────── */
window.renderAnalyst = renderAnalyst;
