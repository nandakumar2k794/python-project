#!/usr/bin/env python3
"""
Test Gemini API key and endpoint
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv('flask_ai_service/.env')

api_key = os.getenv('GEMINI_API_KEY')
print(f"API Key: {api_key}")
print(f"Key format: Starts with 'AQ.' - This looks like a Google Cloud API key")

# Test 1: Simple text request (no image)
print("\n" + "="*60)
print("TEST: Simple Gemini API Request (Text Only)")
print("="*60)

url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"

payload = {
    "contents": [{
        "parts": [
            {"text": "Say 'Hello' in JSON format"}
        ]
    }]
}

try:
    print(f"URL: {url[:80]}...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, json=payload, timeout=10)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body:\n{response.text}")
    
    if response.status_code == 200:
        print("\n✓ API Key is valid and endpoint is working!")
    elif response.status_code == 400:
        print("\n✗ Bad request - check payload format")
    elif response.status_code == 401:
        print("\n✗ Unauthorized - API key is invalid")
    elif response.status_code == 403:
        print("\n✗ Forbidden - API key doesn't have permission")
    else:
        print(f"\n✗ Unexpected status code: {response.status_code}")
        
except requests.exceptions.Timeout:
    print("✗ Request timed out")
except requests.exceptions.ConnectionError as e:
    print(f"✗ Connection error: {e}")
except Exception as e:
    print(f"✗ Error: {e}")
