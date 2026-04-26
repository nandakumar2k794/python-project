import requests
import json
import time

url = 'http://localhost:5001/ai/describe-issue'
payload = {
    'image': 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD',
    'category': 'Roads',
    'address': 'Main Street'
}

print('Testing AI describe endpoint...')
start = time.time()
try:
    r = requests.post(url, json=payload, timeout=15)
    elapsed = time.time() - start
    print('Status:', r.status_code)
    print('Time: %.2fs' % elapsed)
    data = r.json()
    print('Title:', data.get('title'))
    print('Description:', (data.get('description', '')[:80] + '...') if data.get('description') else 'None')
    print('Summary:', data.get('summary'))
    if elapsed < 2.0:
        print('SUCCESS: Fast response achieved!')
    else:
        print('WARNING: Response was slow')
except Exception as e:
    print('Error:', e)
