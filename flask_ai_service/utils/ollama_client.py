"""
Ollama LLaVA client for local image analysis.
Uses the open-source LLaVA model running in Ollama for free image description.
No API key, no rate limits, completely free!
"""

import base64
import requests
import json
import os
import io
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# Configuration
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://ollama:11434')
OLLAMA_MODEL = 'llava:7b'  # Lightweight, fast model (1.4GB)
# Alternative: 'llava:13b' for better accuracy but slower (7.9GB)

# Image compression settings
MAX_IMAGE_SIZE = 512  # Resize to max 512px on longest side
JPEG_QUALITY = 75  # Compress JPEG to 75% quality

def pull_model():
    """Pull the LLaVA model if not already available."""
    try:
        url = f"{OLLAMA_HOST}/api/pull"
        payload = {"name": OLLAMA_MODEL, "stream": False}
        
        logger.info(f"Pulling model {OLLAMA_MODEL}...")
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        
        logger.info(f"Model {OLLAMA_MODEL} ready")
        return True
    except Exception as e:
        logger.error(f"Failed to pull model: {str(e)}")
        return False

def check_ollama_health():
    """Check if Ollama service is running and LLaVA model is available."""
    try:
        # Check if Ollama is responding
        response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code != 200:
            logger.warning("Ollama service not responding with 200")
            return False
        
        # Check if LLaVA model is available
        result = response.json()
        models = result.get('models', [])
        model_names = [m.get('name', '') for m in models]
        
        # Check if any LLaVA variant is available
        has_llava = any(OLLAMA_MODEL in name or 'llava' in name.lower() for name in model_names)
        
        if not has_llava:
            logger.info(f"LLaVA model not found. Available models: {model_names}")
            logger.info(f"Auto-pulling {OLLAMA_MODEL}...")
            # Try to auto-pull the model
            return pull_model()
        
        logger.debug(f"Ollama health check passed. Models available: {model_names}")
        return True
    except requests.exceptions.Timeout:
        logger.warning("Ollama health check timed out")
        return False
    except Exception as e:
        logger.warning(f"Ollama health check failed: {str(e)}")
        return False

def compress_image_base64(image_data: str, max_size: int = MAX_IMAGE_SIZE, quality: int = JPEG_QUALITY) -> str:
    """
    Compress a base64-encoded image by resizing and re-encoding as JPEG.
    Falls back to original if compression fails.
    """
    try:
        from PIL import Image
        
        # Remove data URL prefix if present
        if image_data.startswith('data:image'):
            prefix, b64 = image_data.split(',', 1)
        else:
            prefix = None
            b64 = image_data
        
        # Decode base64 to bytes
        img_bytes = base64.b64decode(b64)
        
        # Open image
        img = Image.open(io.BytesIO(img_bytes))
        
        # Convert to RGB if necessary (handles PNG with transparency, etc.)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Resize if larger than max_size on any dimension
        width, height = img.size
        if width > max_size or height > max_size:
            ratio = min(max_size / width, max_size / height)
            new_size = (int(width * ratio), int(height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save as JPEG with quality compression
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        compressed_bytes = output.getvalue()
        
        # Re-encode to base64
        compressed_b64 = base64.b64encode(compressed_bytes).decode('utf-8')
        
        original_kb = len(img_bytes) / 1024
        compressed_kb = len(compressed_bytes) / 1024
        logger.info(f"Image compressed: {original_kb:.1f}KB -> {compressed_kb:.1f}KB ({compressed_kb/original_kb*100:.0f}%)")
        
        # Return with prefix if original had one
        if prefix:
            return f"{prefix},{compressed_b64}"
        return compressed_b64
        
    except ImportError:
        logger.warning("Pillow not installed, skipping image compression")
        return image_data
    except Exception as e:
        logger.warning(f"Image compression failed: {str(e)}, using original")
        return image_data


def analyze_image_with_ollama(image_data: str, category: str = "Others", address: str = "") -> Dict[str, Any]:
    """
    Analyze an image using local Ollama LLaVA model.
    
    Args:
        image_data: Base64 encoded image (without data: prefix)
        category: Category hint for the issue
        address: Location hint for the issue
        
    Returns:
        Dictionary with title, description, category, priority
    """
    
    try:
        # Check if Ollama is running
        if not check_ollama_health():
            raise ValueError("Ollama service is not responding. Please ensure it's running.")
        
        # Compress image before sending to Ollama for faster processing
        image_data = compress_image_base64(image_data)
        
        # Remove data URL prefix if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        # Create a prompt specifically for civic issues
        prompt = f"""Analyze this image of a civic issue and provide:
1. A brief 3-5 word title
2. A 2-3 sentence description
3. The most appropriate category

Category context: {category}
Location: {address}

Respond in this exact format:
TITLE: [title here]
DESCRIPTION: [description here]
CATEGORY: [Roads/Water/Sanitation/Electricity/Parks/Street Lights/Encroachment/Others]
PRIORITY: [1-5]"""

        # Send image to Ollama for analysis
        url = f"{OLLAMA_HOST}/api/generate"
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "images": [image_data],
            "stream": False,
            "temperature": 0.5,
        }
        
        logger.info(f"Analyzing image with Ollama model {OLLAMA_MODEL}")
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        
        result = response.json()
        response_text = result.get('response', '').strip()
        
        if not response_text:
            raise ValueError("Empty response from Ollama")
        
        # Parse the response
        parsed = parse_ollama_response(response_text)
        
        logger.info(f"Analysis completed: {parsed.get('summary')}")
        
        return {
            "title": parsed.get("title", f"Potential {category} Issue"),
            "description": parsed.get("description", f"Image shows a {category.lower()} issue at {address or 'the reported location'}."),
            "category": parsed.get("category", category),
            "priority": parsed.get("priority", 3),
            "summary": parsed.get("summary", "Image analyzed with LLaVA")
        }
        
    except requests.exceptions.ConnectionError:
        logger.error("Cannot connect to Ollama service")
        return {
            "title": "Issue Report",
            "description": f"Local AI service not available. Please provide a manual description of the {category.lower()} issue at {address or 'the reported location'}.",
            "category": category,
            "priority": 3,
            "summary": "Ollama service not available"
        }
    except requests.exceptions.Timeout:
        logger.error("Ollama request timed out (120s limit)")
        return {
            "title": "Issue Report",
            "description": f"AI analysis took too long. Please provide a manual description of the {category.lower()} issue.",
            "category": category,
            "priority": 3,
            "summary": "Analysis timeout - using fallback"
        }
    except Exception as e:
        logger.exception(f"Error analyzing image: {str(e)}")
        return {
            "title": "Issue Report",
            "description": f"Unable to analyze image. Please provide a manual description of the {category.lower()} issue at {address or 'the reported location'}.",
            "category": category,
            "priority": 3,
            "summary": f"Analysis failed: {str(e)}"
        }

def parse_ollama_response(text: str) -> Dict[str, Any]:
    """
    Parse the structured response from Ollama.
    
    Expected format:
    TITLE: [title]
    DESCRIPTION: [description - can be multi-line]
    CATEGORY: [category]
    PRIORITY: [1-5]
    """
    
    parsed = {}
    lines = text.split('\n')
    
    current_key = None
    current_value = ""
    
    for line in lines:
        line = line.rstrip()  # Remove trailing whitespace
        
        # Check if this line starts a new field
        if line.startswith('TITLE:'):
            if current_key:
                parsed[current_key] = current_value.strip()
            current_key = 'title'
            current_value = line.replace('TITLE:', '').strip()
        elif line.startswith('DESCRIPTION:'):
            if current_key:
                parsed[current_key] = current_value.strip()
            current_key = 'description'
            current_value = line.replace('DESCRIPTION:', '').strip()
        elif line.startswith('CATEGORY:'):
            if current_key:
                parsed[current_key] = current_value.strip()
            current_key = 'category'
            current_value = line.replace('CATEGORY:', '').strip()
        elif line.startswith('PRIORITY:'):
            if current_key:
                parsed[current_key] = current_value.strip()
            current_key = 'priority'
            current_value = line.replace('PRIORITY:', '').strip()
        elif current_key and line.strip():
            # Continuation of multi-line value
            current_value += ' ' + line.strip()
    
    # Don't forget the last field
    if current_key and current_value:
        parsed[current_key] = current_value.strip()
    
    # Process and validate parsed values
    if 'title' in parsed:
        parsed['title'] = parsed['title'][:100]  # Limit title length
    
    if 'description' in parsed:
        parsed['description'] = parsed['description'][:500]  # Limit description length
    
    if 'category' in parsed:
        cat = parsed['category']
        valid_categories = ['Roads', 'Water', 'Sanitation', 'Electricity', 'Parks', 'Street Lights', 'Encroachment', 'Others']
        # Handle potential comma-separated or extra text
        cat_clean = cat.split(',')[0].strip() if ',' in cat else cat.strip()
        parsed['category'] = cat_clean if cat_clean in valid_categories else 'Others'
    
    if 'priority' in parsed:
        try:
            priority = int(parsed['priority'].split()[0])  # Handle "3" or "3 (high)" format
            parsed['priority'] = max(1, min(5, priority))  # Clamp between 1-5
        except (ValueError, IndexError):
            parsed['priority'] = 3
    
    parsed['summary'] = 'Image analyzed with LLaVA'
    
    return parsed
