"""
Test Gemini API Connection - List available models
"""

import os
from dotenv import load_dotenv
from pathlib import Path
import requests

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

api_key = os.getenv('LLM_API_KEY')

print("Listing available Gemini models...")

try:
    # List available models
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Available models:")
        if 'models' in result:
            for model in result['models']:
                model_name = model.get('name', '').replace('models/', '')
                print(f"  - {model_name}")
                
                # Try to find a suitable flash model
                if 'flash' in model_name.lower() and 'generateContent' in model.get('supportedGenerationMethods', []):
                    print(f"    (Suitable for generateContent)")
        else:
            print(f"Response: {result}")
    else:
        print(f"ERROR: Failed to list models: {response.status_code}")
        print(f"Response: {response.text}")
        
except Exception as e:
    print(f"ERROR: {str(e)}")
