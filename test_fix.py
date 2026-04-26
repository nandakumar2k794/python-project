import requests, json, time, sys

url = 'http://localhost:5001/ai/describe-issue'
payload = {
    'image': 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD',
    'category': 'Roads',
    'address': 'Main Street'
}

print("Testing AI describe endpoint...")
start = time.time()
try:
    r = requests.post(url, json=payload, timeout=15)
    elapsed = time.time() - start
    print(f"Status: {r.status_code}")
    print(f"Time: {elapsed:.2f}s")
    data = r.json()
    print(f"Title: {data.get('title')}")
    print(f"Description: {data.get('description', '')[:80]}...")
    print(f"Summary: {data.get('summary')}")
    if elapsed < 2.0:
        print("SUCCESS: Fast response achieved!")
    else:
        print("WARNING: Response was slow")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
