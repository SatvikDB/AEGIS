"""
services/analyst.py
-------------------
AI Tactical Analyst powered by multiple LLM providers.

Generates plain-English situational reports (SITREPs) from detection data
and provides interactive chat for follow-up questions.

Supports: OpenRouter, Groq, Gemini, Anthropic, OpenAI
"""

import logging
from typing import Dict, List, Optional

import config
from services.llm_client import get_llm_client

logger = logging.getLogger(__name__)

# ── System Prompt — The Analyst Persona ──────────────────────────────────────

SYSTEM_PROMPT = """You are an AI Tactical Analyst embedded in AEGIS, a military target detection and surveillance system. Your role is to read raw detection data from YOLO11 object detection scans and translate it into actionable intelligence for human operators.

**Your responsibilities:**
1. Read detection JSON (class names, confidence scores, bounding boxes, risk levels, threat assessments)
2. Write concise, professional situational reports (SITREPs) in plain English
3. Answer follow-up questions about detections with precision and clarity
4. Never speculate beyond the data provided
5. Use military terminology appropriately but remain accessible

**SITREP format guidelines:**
- Start with a one-sentence executive summary
- List detected objects by risk level (HIGH → MEDIUM → LOW)
- Include confidence scores and approximate positions when relevant
- End with a tactical recommendation if threat level is ELEVATED or higher
- Keep total length under 200 words
- Use present tense, active voice
- Be direct and factual

**Tone:**
- Professional and authoritative
- Calm and objective
- Action-oriented
- No unnecessary jargon

**When answering follow-up questions:**
- Reference specific detections from the scan data
- Provide tactical context when asked
- Admit uncertainty if data is insufficient
- Suggest additional scans if needed

**Example SITREP structure:**
"SITREP: [Executive summary]. DETECTED: [High-risk items with details]. [Medium/low-risk items if significant]. ASSESSMENT: [Threat level interpretation]. RECOMMENDATION: [Action if needed]."

Remember: You are analyzing a single image scan. You do not have historical context unless explicitly provided. Focus on what is visible in THIS scan."""


# ── Helper Functions ──────────────────────────────────────────────────────────

def build_detection_context(detection_data: Dict) -> str:
    """
    Convert detection JSON into a compact, LLM-readable string.
    
    Args:
        detection_data: Full detection response from /detect endpoint
        
    Returns:
        Formatted string with all relevant detection information
    """
    detections = detection_data.get("detections", [])
    threat = detection_data.get("threat", {})
    image_size = detection_data.get("image_size", {})
    inference_ms = detection_data.get("inference_ms", 0)
    
    # Build context string
    lines = []
    lines.append(f"IMAGE SCAN ANALYSIS")
    lines.append(f"Resolution: {image_size.get('width', 0)}×{image_size.get('height', 0)} pixels")
    lines.append(f"Inference time: {inference_ms}ms")
    lines.append(f"")
    
    # Threat assessment
    lines.append(f"THREAT ASSESSMENT:")
    lines.append(f"  Level: {threat.get('threat_level', 'UNKNOWN')}")
    lines.append(f"  Label: {threat.get('label', 'N/A')}")
    lines.append(f"  Description: {threat.get('description', 'N/A')}")
    
    stats = threat.get('stats', {})
    lines.append(f"  Total detections: {stats.get('total', 0)}")
    lines.append(f"  High-risk: {stats.get('high_risk', 0)}")
    lines.append(f"  Medium-risk: {stats.get('medium_risk', 0)}")
    lines.append(f"  Low-risk: {stats.get('low_risk', 0)}")
    lines.append(f"")
    
    # Individual detections
    if detections:
        lines.append(f"DETECTED OBJECTS ({len(detections)} total):")
        for i, det in enumerate(detections, 1):
            class_name = det.get('class_name', 'unknown')
            confidence = det.get('confidence', 0) * 100
            risk = det.get('risk_level', 'unknown').upper()
            box = det.get('box', {})
            
            # Approximate position description
            cx = box.get('cx', 0)
            cy = box.get('cy', 0)
            img_w = image_size.get('width', 1)
            img_h = image_size.get('height', 1)
            
            # Determine position (left/center/right, top/center/bottom)
            h_pos = "left" if cx < img_w * 0.33 else "right" if cx > img_w * 0.67 else "center"
            v_pos = "top" if cy < img_h * 0.33 else "bottom" if cy > img_h * 0.67 else "middle"
            position = f"{v_pos}-{h_pos}" if v_pos != "middle" or h_pos != "center" else "center"
            
            lines.append(f"  {i}. {class_name.upper()} [{risk} RISK]")
            lines.append(f"     Confidence: {confidence:.1f}%")
            lines.append(f"     Position: {position} of frame")
            lines.append(f"     Size: {box.get('width', 0)}×{box.get('height', 0)} pixels")
    else:
        lines.append(f"DETECTED OBJECTS: None")
    
    return "\n".join(lines)


def generate_sitrep(detection_data: Dict) -> Dict:
    """
    Generate a situational report (SITREP) from detection data using LLM.
    
    Args:
        detection_data: Full detection response from /detect endpoint
        
    Returns:
        Dict with keys:
            - success: bool
            - sitrep: str (the generated report)
            - model: str (model used)
            - tokens: int (tokens used)
            - error: str (if success=False)
    """
    if not config.ANALYST_ENABLED:
        return {
            "success": False,
            "error": f"AI Analyst disabled - {config.LLM_PROVIDER.upper()} API key not configured",
            "sitrep": "",
            "model": "",
            "tokens": 0
        }
    
    try:
        # Build detection context
        context = build_detection_context(detection_data)
        
        # Get LLM client
        client = get_llm_client()
        
        # Generate SITREP
        logger.info(f"Generating SITREP with {config.LLM_PROVIDER} ({config.LLM_MODEL})...")
        
        response = client.generate(
            system_prompt=SYSTEM_PROMPT,
            user_message=f"Generate a tactical SITREP for this detection scan:\n\n{context}"
        )
        
        logger.info(f"SITREP generated successfully ({response['tokens_used']} tokens)")
        
        return {
            "success": True,
            "sitrep": response["text"],
            "model": response["model"],
            "tokens": response["tokens_used"],
            "error": ""
        }
        
    except Exception as e:
        logger.error(f"LLM error: {e}")
        return {
            "success": False,
            "error": f"LLM error: {str(e)}",
            "sitrep": "",
            "model": "",
            "tokens": 0
        }


def analyst_chat(scan_id: str, user_message: str, detection_context: str, 
                 sitrep: str, chat_history: List[Dict]) -> Dict:
    """
    Handle follow-up questions about a detection scan.
    
    Args:
        scan_id: Unique scan identifier
        user_message: Operator's question
        detection_context: Full detection context string
        sitrep: Previously generated SITREP
        chat_history: List of previous messages [{"role": "user"|"assistant", "content": str}]
        
    Returns:
        Dict with keys:
            - success: bool
            - answer: str (LLM's response)
            - tokens: int (tokens used)
            - error: str (if success=False)
    """
    if not config.ANALYST_ENABLED:
        return {
            "success": False,
            "error": f"AI Analyst disabled - {config.LLM_PROVIDER.upper()} API key not configured",
            "answer": "",
            "tokens": 0
        }
    
    try:
        # Get LLM client
        client = get_llm_client()
        
        # Build enhanced system prompt with scan context
        enhanced_system = f"""{SYSTEM_PROMPT}

**CURRENT SCAN CONTEXT (Scan ID: {scan_id}):**

{detection_context}

**PREVIOUSLY GENERATED SITREP:**
{sitrep}

The operator is now asking follow-up questions about this specific scan. Answer based on the detection data above. Be concise and tactical."""
        
        logger.info(f"Processing chat question for scan {scan_id}...")
        
        # Generate response
        response = client.generate(
            system_prompt=enhanced_system,
            user_message=user_message,
            messages=chat_history
        )
        
        logger.info(f"Chat response generated ({response['tokens_used']} tokens)")
        
        return {
            "success": True,
            "answer": response["text"],
            "tokens": response["tokens_used"],
            "error": ""
        }
        
    except Exception as e:
        logger.error(f"LLM error in chat: {e}")
        return {
            "success": False,
            "error": f"LLM error: {str(e)}",
            "answer": "",
            "tokens": 0
        }
