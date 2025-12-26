import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

print(f"🔑 Testing Key: {api_key[:5]}...{api_key[-5:]}")

# URL to list available models
url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"

try:
    response = requests.get(url)
    data = response.json()
    
    if "error" in data:
        print("\n❌ API ERROR:")
        print(data)
    else:
        print("\n✅ SUCCESS! Here are your available models:")
        # Print only the names so we know what to put in the code
        for model in data.get('models', []):
            if 'generateContent' in model['supportedGenerationMethods']:
                print(f" - {model['name']}")

except Exception as e:
    print(f"❌ CONNECTION ERROR: {e}")