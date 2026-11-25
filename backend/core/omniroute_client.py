import base64
import json
import httpx
import logging
from pathlib import Path
from backend.core.omniroute_config import load_settings

logger = logging.getLogger(__name__)

def verify_watermark_with_ai(image_path: Path) -> dict:
    """
    Sends the image to an OmniRoute provider for vision verification.
    Expects a structured JSON response.
    Returns dict: {"found": bool, "confidence": float, "bbox": [x, y, w, h]}
    """
    settings = load_settings()
    if not settings.get("OMNIROUTE_ENABLED"):
        return {"found": False, "confidence": 0.0, "bbox": None, "error": "OmniRoute AI fallback is disabled."}

    url = settings.get("OMNIROUTE_BASE_URL", "")
    key = settings.get("OMNIROUTE_API_KEY", "")
    model = settings.get("OMNIROUTE_VISION_MODEL", "auto/vision:free")
    timeout = settings.get("OMNIROUTE_TIMEOUT_MS", 30000) / 1000.0

    if not key or not url:
        return {"found": False, "confidence": 0.0, "bbox": None, "error": "OmniRoute API configuration is missing."}

    # Ensure URL points to chat completions endpoint
    if not url.endswith("/chat/completions"):
        url = url.rstrip("/") + "/chat/completions"

    try:
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}"
        }
        
        prompt = (
            "You are an expert image forensic AI. Your task is to detect the presence of a watermark, logo, or text overlay on this image. "
            "Respond ONLY with a valid JSON object matching this schema: "
            "{\"found\": bool, \"confidence\": float (0.0 to 1.0), \"bbox\": [x, y, width, height] or null}. "
            "The bbox coordinates should be normalized (0.0 to 1.0). "
            "Do not include any markdown formatting, backticks, or other text."
        )

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 150,
            "temperature": 0.0
        }

        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            
            # Clean up potential markdown formatting
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
                
            result = json.loads(content)
            
            # Strict validation
            found = bool(result.get("found", False))
            confidence = float(result.get("confidence", 0.0))
            bbox = result.get("bbox")
            
            if bbox is not None:
                if not isinstance(bbox, list) or len(bbox) != 4:
                    raise ValueError("Invalid bbox format. Expected [x, y, w, h].")
                for v in bbox:
                    if not isinstance(v, (int, float)) or v < 0.0 or v > 1.0:
                        raise ValueError(f"Invalid bbox value {v}. Expected normalized 0.0 to 1.0.")
            
            return {
                "found": found,
                "confidence": max(0.0, min(1.0, confidence)),
                "bbox": bbox
            }
            
    except Exception as e:
        logger.error(f"[OmniRoute] Error verifying with AI model '{model}': {type(e).__name__} - {str(e)}")
        # Note: Do not log the payload, key, or image contents
        return {"found": False, "confidence": 0.0, "bbox": None, "error": f"AI Verification failed: {type(e).__name__}"}
