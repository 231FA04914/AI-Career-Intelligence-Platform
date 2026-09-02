"""
Download Whisper Model Script
Downloads the faster-whisper model with SSL workarounds.
"""

import os
import ssl
import urllib3
from pathlib import Path

# Disable all SSL verification
os.environ['HF_HUB_DISABLE_SSL_VERIFY'] = '1'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['SSL_VERIFY'] = '0'
ssl._create_default_https_context = ssl._create_unverified_context

# Disable urllib3 warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    from huggingface_hub import snapshot_download
    
    print("Downloading Whisper base model...")
    print("This may take a few minutes depending on your internet connection.")
    
    # Create models directory
    models_dir = Path("models/whisper-base")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Download model
    snapshot_download(
        repo_id='guillaumekln/faster-whisper-base',
        local_dir='models/whisper-base',
        local_dir_use_symlinks=False
    )
    
    print(f"✅ Model downloaded successfully to: {models_dir.absolute()}")
    print("You can now run the application with: python -m streamlit run app.py")
    
except ImportError:
    print("❌ huggingface_hub not installed. Installing...")
    os.system("pip install huggingface_hub")
    print("Please run this script again after installation.")
except Exception as e:
    print(f"❌ Error downloading model: {str(e)}")
    print("\nAlternative: Download manually from:")
    print("https://huggingface.co/guillaumekln/faster-whisper-base/tree/main")
    print("And place files in: models/whisper-base/")
