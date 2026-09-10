"""
Check API key format and validity
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

api_key = os.getenv('LLM_API_KEY')

print("API Key Analysis:")
print(f"API Key exists: {bool(api_key)}")
if api_key:
    print(f"API Key length: {len(api_key)}")
    print(f"API Key starts with: {api_key[:10]}...")
    print(f"API Key ends with: ...{api_key[-10:]}")
    print(f"API Key contains spaces: {' ' in api_key}")
    print(f"API Key contains special chars: {any(not c.isalnum() and c not in '-._' for c in api_key)}")
