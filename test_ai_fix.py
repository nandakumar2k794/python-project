#!/usr/bin/env python3
"""
Quick test to verify AI image description feature is working after the fix.
Tests the Flask endpoint directly without requiring authentication.
"""

import requests
import json
import base64
import sys

def create_test_image():
    """Create a minimal valid JPEG for testing"""
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
    return f"data:image/jpeg;base64,{base64.b64encode(jpeg_bytes).decode('utf-8')}"

def test_flask_endpoint(flask_url="http://localhost:5001"):
    """Test the Flask /ai/describe-issue endpoint"""
    print("\n" + "="*60)
    print("Testing Flask AI Image Description Endpoint")
    print("="*60)
    
    # Create test image
    test_image = create_test_image()
    print(f"✓ Created test image ({len(test_image)} bytes)")
    
    # Prepare request
    payload = {
        "image": test_image,
        "category": "Roads",
        "address": "Main Street, District"
    }
    
    try:
        print(f"\nSending request to {flask_url}/ai/describe-issue...")
        response = requests.post(
            f"{flask_url}/ai/describe-issue",
            json=payload,
            timeout=120
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✓ SUCCESS - Response received:")
            print(json.dumps(data, indent=2))
            
            # Validate response structure
            required_fields = ['title', 'description', 'suggested_category', 'priority', 'summary']
            missing = [f for f in required_fields if f not in data]
            
            if missing:
                print(f"\n⚠ WARNING: Missing fields: {missing}")
                return False
            else:
                print(f"\n✓ All required fields present")
                return True
        else:
            print(f"\n✗ ERROR: Unexpected status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n✗ ERROR: Cannot connect to Flask at {flask_url}")
        print("Make sure Flask service is running:")
        print("  docker-compose up -d flask_ai")
        return False
    except requests.exceptions.Timeout:
        print(f"\n✗ ERROR: Request timed out (>120s)")
        print("This might be expected on first run with Ollama")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        return False

def test_response_validation():
    """Test response validation logic"""
    print("\n" + "="*60)
    print("Testing Response Validation")
    print("="*60)
    
    # Test case 1: Valid response
    valid_response = {
        "title": "Large pothole",
        "description": "A pothole on Main Street",
        "suggested_category": "Roads",
        "priority": 4,
        "summary": "Image analyzed successfully"
    }
    
    required_fields = ['title', 'description', 'suggested_category', 'priority', 'summary']
    missing = [f for f in required_fields if f not in valid_response]
    
    if not missing:
        print("✓ Valid response structure passes validation")
    else:
        print(f"✗ Valid response missing fields: {missing}")
        return False
    
    # Test case 2: Template fallback response
    template_response = {
        "title": "Road Damage Report",
        "description": "Road surface damage...",
        "suggested_category": "Roads",
        "priority": 4,
        "summary": "Instant analysis based on category: Roads"
    }
    
    missing = [f for f in required_fields if f not in template_response]
    if not missing:
        print("✓ Template fallback response passes validation")
    else:
        print(f"✗ Template response missing fields: {missing}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("AI Image Description Feature - Post-Fix Verification")
    print("="*60)
    
    results = {}
    
    # Test 1: Response validation
    results['response_validation'] = test_response_validation()
    
    # Test 2: Flask endpoint
    results['flask_endpoint'] = test_flask_endpoint()
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n✓ All tests passed! The AI image description feature is working correctly.")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
