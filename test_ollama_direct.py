#!/usr/bin/env python3
"""Test Ollama API directly"""

import requests
import json

url = 'http://localhost:11434/api/generate'
payload = {
    'model': 'mistral:latest',
    'prompt': 'Who created Python?',
    'stream': True,
    'options': {
        'num_predict': 512,
        'temperature': 0.3
    }
}

print("Testing Ollama API...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print()

try:
    response = requests.post(url, json=payload, stream=True, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print()
    
    if response.status_code != 200:
        print(f"ERROR: {response.text}")
    else:
        print("Streaming response:")
        line_count = 0
        for line in response.iter_lines():
            line_count += 1
            if line:
                print(f"Line {line_count}: {repr(line[:100])}")
                try:
                    data = json.loads(line)
                    print(f"  Parsed: model={data.get('model')}, done={data.get('done')}, response_len={len(data.get('response', ''))}")
                except:
                    pass
            if line_count >= 10:
                print("... (stopping after 10 lines)")
                break
                
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
