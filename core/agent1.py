import os
import json
import re
import requests
import time
import warnings
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

# --- Data Models ---
class SubModule(BaseModel):
    name: str
    description: str

class ProductModule(BaseModel):
    module_name: str
    description: str
    submodules: List[SubModule]
    confidence_score: int

class ExtractionResult(BaseModel):
    modules: List[ProductModule]

def analyze_docs(context_text):
    print("🧠 AI Agent: Initializing...")

    if not API_KEY:
        print("❌ CRITICAL: API Key missing.")
        return None

    # --- STRATEGY: USE THE 'LATEST' ALIAS (Stable) ---
    # We try 'gemini-flash-latest' first. If that fails, we try 'gemini-pro-latest'.
    # These are the standard models from your list that usually have working Free Tier.
    
    models_to_try = [
        "gemini-flash-latest",  # Fast, usually free
        "gemini-pro-latest"     # Slower, but powerful backup
    ]
    
    headers = {"Content-Type": "application/json"}
    # Limit text to 5000 chars to stay safe
    safe_text = context_text[:5000]
    
    payload = {
        "contents": [{
            "parts": [{"text": f"""
                You are a technical analyst. Analyze this documentation text.
                Identify 3-5 distinct Modules. For each module, identify 2-3 Submodules.
                Return ONLY valid JSON.
                
                Schema:
                {{
                  "modules": [
                    {{
                      "module_name": "Name",
                      "description": "Description",
                      "confidence_score": 95,
                      "submodules": [
                        {{ "name": "Sub Name", "description": "Sub Description" }}
                      ]
                    }}
                  ]
                }}

                TEXT TO ANALYZE:
                {safe_text}
            """}]
        }]
    }

    # --- RETRY LOOP ACROSS MODELS ---
    for model_name in models_to_try:
        print(f"🔄 Trying model: {model_name}...")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
        
        try:
            # Add a small delay to be polite to the API
            time.sleep(2)
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            # SUCCESS
            if response.status_code == 200:
                result = response.json()
                try:
                    raw_text = result['candidates'][0]['content']['parts'][0]['text']
                    clean_json = re.sub(r"```json|```", "", raw_text).strip()
                    print(f"✅ SUCCESS: Real Data Extracted using {model_name}!")
                    return ExtractionResult(**json.loads(clean_json))
                except Exception as e:
                    print(f"⚠️ Error parsing response from {model_name}: {e}")
                    continue # Try next model
            
            # FAIL - PRINT ERROR
            else:
                print(f"⚠️ {model_name} Failed ({response.status_code})")
                if "429" in str(response.status_code):
                     print("   -> Quota Limit Hit.")
                else:
                     print(f"   -> Details: {response.text[:100]}...")
                
                continue # Try next model in list

        except Exception as e:
            print(f"❌ Connection Error with {model_name}: {e}")
            continue

    print("❌ All models failed. Your API Key has no free quota available.")
    return None