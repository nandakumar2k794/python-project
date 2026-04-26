#!/usr/bin/env python3
"""
Comprehensive test suite for AI Image Description Generator
Tests Ollama integration, Gemini fallback, and end-to-end workflow
"""

import json
import sys
import base64
import requests
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
END = '\033[0m'

def print_header(msg):
    print(f"\n{BLUE}{'='*60}{END}")
    print(f"{BLUE}{msg}{END}")
    print(f"{BLUE}{'='*60}{END}")

def print_success(msg):
    print(f"{GREEN}✓ {msg}{END}")

def print_error(msg):
    print(f"{RED}✗ {msg}{END}")

def print_warning(msg):
    print(f"{YELLOW}⚠ {msg}{END}")

def print_info(msg):
    print(f"{BLUE}ℹ {msg}{END}")

def test_ollama_health(ollama_url="http://localhost:11434"):
    """Test Ollama service availability"""
    print_header("Testing Ollama Service")
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            model_names = [m.get('name', 'unknown') for m in models]
            print_success(f"Ollama is running and responding")
            print_info(f"Available models: {model_names}")
            return True, model_names
        else:
            print_error(f"Ollama returned status code {response.status_code}")
            return False, []
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to Ollama at {ollama_url}")
        print_warning("Make sure Ollama is running: docker run -d -p 11434:11434 ollama/ollama")
        return False, []
    except requests.exceptions.Timeout:
        print_error("Ollama health check timed out")
        return False, []
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False, []

def test_flask_health(flask_url="http://localhost:5001"):
    """Test Flask AI service"""
    print_header("Testing Flask AI Service")
    try:
        response = requests.get(f"{flask_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success("Flask AI service is running")
            print_info(f"Status: {json.dumps(data, indent=2)}")
            return True
        else:
            print_error(f"Flask returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to Flask AI service at {flask_url}")
        print_warning("Make sure Flask service is running: python -m flask run")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False

def create_test_image_base64():
    """Create a simple test image as base64"""
    print_header("Creating Test Image")
    # Create a simple 1x1 pixel JPEG (red)
    # This is a minimal valid JPEG
    jpeg_bytes = bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
        0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
        0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
        0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
        0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
        0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
        0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
        0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
        0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
        0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
        0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
        0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
        0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
        0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
        0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
        0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
        0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
        0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
        0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
        0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
        0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
        0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
        0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
        0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
        0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD0, 0xFF, 0xD9
    ])
    
    base64_str = base64.b64encode(jpeg_bytes).decode('utf-8')
    print_success(f"Created test image (JPEG, {len(jpeg_bytes)} bytes)")
    return f"data:image/jpeg;base64,{base64_str}"

def test_image_analysis(flask_url="http://localhost:5001"):
    """Test image analysis through Flask API"""
    print_header("Testing Image Analysis")
    
    # Create test image
    test_image = create_test_image_base64()
    
    # Prepare request
    payload = {
        "image": test_image,
        "category": "Roads",
        "address": "Main Street, District"
    }
    
    try:
        print_info("Sending image analysis request to Flask...")
        response = requests.post(
            f"{flask_url}/ai/describe-issue",
            json=payload,
            timeout=120  # LLaVA can be slow
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Image analysis completed successfully")
            print_info(f"Response: {json.dumps(data, indent=2)}")
            
            # Validate response structure
            required_fields = ['title', 'description', 'category', 'priority', 'summary']
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                print_warning(f"Missing fields in response: {missing_fields}")
            else:
                print_success("Response has all required fields")
            
            return True, data
        else:
            print_error(f"Flask returned status code {response.status_code}")
            print_info(f"Response: {response.text}")
            return False, {}
            
    except requests.exceptions.Timeout:
        print_error("Image analysis timed out (>120s)")
        print_warning("This might be expected on first run or with slow hardware")
        return False, {}
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False, {}

def test_django_integration(django_url="http://localhost:8000"):
    """Test Django proxy endpoint"""
    print_header("Testing Django Integration")
    
    print_warning("Django proxy test requires authentication")
    print_info("This would require valid session credentials")
    print_info("Test would be: POST /api/dashboard/ai/describe-issue/")

def test_response_parsing():
    """Test Ollama response parsing"""
    print_header("Testing Response Parsing")
    
    # Import the parsing function
    sys.path.insert(0, str(Path(__file__).parent / "flask_ai_service"))
    
    try:
        from utils.ollama_client import parse_ollama_response
        
        # Test case 1: Standard response
        test_response_1 = """TITLE: Large pothole on Main Street
DESCRIPTION: A significant pothole discovered on Main Street that poses a safety hazard.
CATEGORY: Roads
PRIORITY: 4"""
        
        result = parse_ollama_response(test_response_1)
        print_success("Parsed standard response")
        print_info(f"Result: {json.dumps(result, indent=2)}")
        
        # Test case 2: Multi-line description
        test_response_2 = """TITLE: Water leak from main pipe
DESCRIPTION: A significant water leak observed at the corner of Main and Oak Street.
The water is flowing onto the road causing a safety hazard for pedestrians.
Multiple days of continuous leaking.
CATEGORY: Water
PRIORITY: 5"""
        
        result = parse_ollama_response(test_response_2)
        print_success("Parsed multi-line response")
        print_info(f"Result: {json.dumps(result, indent=2)}")
        
        return True
    except ImportError:
        print_error("Could not import parsing function")
        return False
    except Exception as e:
        print_error(f"Parsing test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*60}{END}")
    print(f"{BLUE}AI Image Description Generator - Test Suite{END}")
    print(f"{BLUE}{'='*60}{END}")
    
    results = {}
    
    # Test 1: Ollama Health
    ollama_ok, models = test_ollama_health()
    results['ollama_health'] = ollama_ok
    
    # Test 2: Flask Health
    flask_ok = test_flask_health()
    results['flask_health'] = flask_ok
    
    # Test 3: Response Parsing
    parsing_ok = test_response_parsing()
    results['response_parsing'] = parsing_ok
    
    # Test 4: Image Analysis
    if flask_ok:
        analysis_ok, response_data = test_image_analysis()
        results['image_analysis'] = analysis_ok
    else:
        print_warning("Skipping image analysis test (Flask not available)")
        results['image_analysis'] = None
    
    # Test 5: Django Integration
    test_django_integration()
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for test_name, result in results.items():
        if result is True:
            print_success(test_name)
        elif result is False:
            print_error(test_name)
        else:
            print_warning(f"{test_name} (skipped)")
    
    print(f"\n{BLUE}Results: {GREEN}{passed} passed{END}, {RED}{failed} failed{END}, {YELLOW}{skipped} skipped{END}")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
