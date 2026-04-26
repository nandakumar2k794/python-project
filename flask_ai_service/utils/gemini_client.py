import base64
import requests
import json
import os
import logging
from typing import Dict, Any

# Load .env if present
from pathlib import Path
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Import Ollama client
from .ollama_client import analyze_image_with_ollama, check_ollama_health

logger = logging.getLogger(__name__)

def classify_description(description: str):
    txt=description.lower()
    category="Others"
    if "pothole" in txt or "road" in txt: category="Roads"
    elif "water" in txt or "leak" in txt: category="Water"
    priority=5 if any(k in txt for k in ["flood","accident","fire"]) else 3
    return {"category":category,"sub_category":"general","priority":priority,"confidence":0.82}

def analyze_image(image_data: str, category: str = "Others", address: str = "") -> Dict[str, Any]:
    """
    Analyze an image using the best available provider.
    Priority: 1. Ollama (free, local, no rate limits) -> 2. Gemini (paid, rate limited)
    
    Args:
        image_data: Base64 encoded image (with or without data: prefix)
        category: Category hint for the issue
        address: Location hint for the issue
        
    Returns:
        Dictionary with title, description, category, priority
    """
    
    # Priority: Use Ollama first (free, local, no rate limits)
    logger.info("Attempting Ollama LLaVA for image analysis (free, local, no rate limits)")
    ollama_healthy = check_ollama_health()
    
    if ollama_healthy:
        logger.info("Ollama is available, using it for analysis")
        result = analyze_image_with_ollama(image_data, category, address)
        # Check if analysis was successful using positive indicators
        ollama_summary = result.get("summary", "")
        ollama_success = "Image analyzed" in ollama_summary or "analyzed successfully" in ollama_summary.lower()
        if ollama_success:
            logger.info(f"Ollama analysis successful: {ollama_summary}")
            return result
        logger.warning(f"Ollama analysis failed: {ollama_summary}")
    else:
        logger.info("Ollama not available, trying Gemini API as fallback")
    
    # Fallback to Gemini if Ollama fails
    has_gemini = bool(os.getenv('GEMINI_API_KEY'))
    if has_gemini:
        logger.info("Gemini API key configured, attempting as fallback")
        return analyze_image_with_gemini(image_data, category, address)
    
    # No providers available - return error
    logger.warning("No AI providers available (Ollama down, no Gemini key)")
    return {
        "title": "Issue Report",
        "description": f"AI analysis services are currently unavailable. Please provide a manual description of the {category.lower()} issue at {address or 'the reported location'}.",
        "category": category,
        "priority": 3,
        "summary": "No AI provider available"
    }

def analyze_image_with_gemini(image_data: str, category: str = "Others", address: str = "") -> Dict[str, Any]:
    """
    Analyze an image using Gemini API (fallback provider when Ollama is unavailable).
    Note: Gemini free tier has rate limits. Use Ollama for unlimited analysis.
    """

    try:
        # Remove data URL prefix if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]

        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.error("GEMINI_API_KEY not configured")
            raise ValueError("GEMINI_API_KEY not configured")

        # Use the latest Gemini model with v1 endpoint
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"

        # Improved prompt that explicitly requests JSON response
        prompt = f"""Analyze this civic issue image and respond ONLY with valid JSON (no markdown, no code blocks).

Category hint: {category}
Location: {address}

Respond with ONLY this JSON structure:
{{
  "title": "Brief 3-5 word title for the issue",
  "description": "2-3 sentences describing the issue and its impact",
  "category": "Most appropriate category from [Roads, Water, Sanitation, Electricity, Parks, Street Lights, Encroachment, Others]",
  "priority": 3,
  "summary": "Issue analyzed successfully"
}}"""

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_data
                        }
                    }
                ]
            }]
        }

        logger.info(f"Sending request to Gemini API for category: {category}")
        response = requests.post(url, json=payload, timeout=30)
        
        logger.info(f"Gemini API response status: {response.status_code}")
        
        # Handle rate limiting gracefully
        if response.status_code == 429:
            logger.warning("Gemini API rate limit exceeded - free tier limit reached")
            raise ValueError("Gemini API rate limit exceeded. Please wait a moment and try again.")
        
        if response.status_code != 200:
            logger.error(f"Gemini API error status {response.status_code}: {response.text}")
            response.raise_for_status()
        
        result = response.json()
        logger.debug(f"Gemini API response: {json.dumps(result, indent=2)[:500]}")

        # Parse Gemini response
        if 'error' in result:
            error_msg = result.get('error', {}).get('message', 'Unknown error')
            logger.error(f"Gemini API error: {error_msg}")
            # Check for rate limit errors in the response
            if '429' in str(error_msg) or 'rate' in error_msg.lower():
                raise ValueError("API rate limit exceeded. Please wait before trying again.")
            raise ValueError(f"Gemini API error: {error_msg}")

        # Safely extract text from Gemini response
        candidates = result.get('candidates') or [{}]
        first_candidate = candidates[0] if candidates else {}
        content = first_candidate.get('content', {}) or {}
        parts = content.get('parts') or []
        text = parts[0].get('text', '') if parts else ''

        if not text:
            logger.error("No response text from Gemini API")
            raise ValueError("No response from Gemini API")

        logger.info(f"Gemini response text (first 200 chars): {text[:200]}")

        # Clean up markdown code blocks if present
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        text = text.strip()

        # Parse JSON response
        try:
            parsed = json.loads(text)
            logger.info(f"Successfully parsed Gemini JSON response")
        except json.JSONDecodeError as json_err:
            logger.warning(f"JSON parsing failed: {json_err}, attempting regex extraction")
            # If JSON parsing fails, create a basic response
            import re
            title_match = re.search(r'"title"\s*:\s*"([^"]*)"', text)
            desc_match = re.search(r'"description"\s*:\s*"([^"]*)"', text)
            cat_match = re.search(r'"category"\s*:\s*"([^"]*)"', text)
            
            parsed = {
                "title": title_match.group(1) if title_match else text[:100],
                "description": desc_match.group(1) if desc_match else text,
                "category": cat_match.group(1) if cat_match else category,
            }
            logger.info(f"Extracted data via regex: title={parsed.get('title')[:50]}")

        result_data = {
            "title": parsed.get("title", f"Potential {category} Issue"),
            "description": parsed.get("description", f"Image analysis detected a potential {category.lower()} issue at {address or 'the reported location'}."),
            "category": parsed.get("category", category),
            "priority": parsed.get("priority", 3),
            "summary": "Image analyzed successfully"
        }
        
        logger.info(f"Gemini analysis completed successfully: {result_data['title']}")
        return result_data

    except requests.exceptions.Timeout:
        logger.error("Gemini API request timed out")
        return {
            "title": "Issue Report",
            "description": f"Image analysis took too long. Please provide a manual description.",
            "category": category,
            "priority": 3,
            "summary": "Gemini API timeout"
        }
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Connection error to Gemini API: {conn_err}")
        return {
            "title": "Issue Report",
            "description": f"Unable to connect to AI service. Please provide a manual description.",
            "category": category,
            "priority": 3,
            "summary": f"Connection error: {str(conn_err)}"
        }
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error: {req_err}")
        return {
            "title": "Issue Report",
            "description": f"Unable to analyze image - network error. Please provide a manual description.",
            "category": category,
            "priority": 3,
            "summary": f"Network error: {str(req_err)}"
        }
    except Exception as e:
        logger.exception(f"Unexpected error in Gemini analysis: {str(e)}")
        # Fallback analysis
        return {
            "title": "Issue Report",
            "description": f"Unable to analyze image automatically. Please provide a manual description of the issue at {address or 'the reported location'}.",
            "category": category,
            "priority": 3,
            "summary": f"Image analysis failed: {str(e)}"
        }
