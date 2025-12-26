import os
import json
import re
import requests
import time
import warnings
from typing import List, Set
from pydantic import BaseModel
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

# --- SETTINGS FOR FREE TIER SAFETY ---
MAX_PAGES_TO_CRAWL = 5  # Stop after 5 pages (Save quota!)
REQUEST_DELAY = 4       # Wait 4 seconds between requests (15 requests/min limit)

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
    source_url: str
    depth: int
    modules: List[ProductModule]

# --- 1. THE SMART CRAWLER ---
def crawl_and_analyze(start_url: str, max_depth: int):
    print(f"🚀 Starting Smart Crawl on: {start_url}")
    print(f"🛑 Safety Limit: Max {MAX_PAGES_TO_CRAWL} pages total.")
    
    visited_urls: Set[str] = set()
    queue = [(start_url, 0)]  # (url, current_depth)
    results = []
    
    pages_crawled = 0

    while queue and pages_crawled < MAX_PAGES_TO_CRAWL:
        current_url, current_depth = queue.pop(0)
        
        if current_url in visited_urls:
            continue
            
        visited_urls.add(current_url)
        pages_crawled += 1
        
        print(f"\n🕷️ Crawling Page {pages_crawled}/{MAX_PAGES_TO_CRAWL}: {current_url} (Depth {current_depth})")
        
        # 1. Fetch Page Content (Mocking simple HTML fetch for demo)
        # In a real scraper, you'd use BeautifulSoup to get links here.
        # For this demo, we analyze the URL as if it were the page text.
        
        # 2. Analyze with AI
        ai_result = analyze_single_page(current_url)
        if ai_result:
            # Add to final results
            results.extend(ai_result.modules)
            
            # 3. If we haven't hit max depth, pretend we found links
            # (In reality, you would extract real hrefs here)
            if current_depth < max_depth:
                # SIMULATION: adding fake 'child' links to prove depth works
                fake_child_1 = current_url + "/feature-a"
                fake_child_2 = current_url + "/feature-b"
                if fake_child_1 not in visited_urls:
                    queue.append((fake_child_1, current_depth + 1))
                if fake_child_2 not in visited_urls:
                    queue.append((fake_child_2, current_depth + 1))

    return {"modules": results}

# --- 2. THE ANALYZER (With Safety Brake) ---
def analyze_single_page(url):
    # SAFETY BRAKE: Sleep to respect Google's "15 RPM" limit
    print(f"⏳ Waiting {REQUEST_DELAY}s to respect API limits...")
    time.sleep(REQUEST_DELAY)

    if not API_KEY:
        print("❌ API Key Missing")
        return None

    model_name = "gemini-flash-latest" 
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [{"text": f"""
                Analyze this URL as if it were a documentation page: {url}
                Return valid JSON with 1 module related to the URL path.
                Schema: {{ "modules": [ {{ "module_name": "...", "description": "...", "confidence_score": 90, "submodules": [ {{ "name": "...", "description": "..." }} ] }} ] }}
            """}]
        }]
    }

    try:
        response = requests.post(api_url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
        if response.status_code == 200:
            clean_json = re.sub(r"```json|```", "", response.json()['candidates'][0]['content']['parts'][0]['text']).strip()
            return ExtractionResult(source_url=url, depth=0, modules=json.loads(clean_json)['modules'])
        elif response.status_code == 429:
            print("⚠️ Quota Hit. Skipping this page.")
            return None
        else:
            print(f"❌ Error {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

# --- MAIN ENTRY POINT ---
def analyze_docs(start_url):
    # We ignore the text passed from app.py and use the URL directly for the crawl
    # Hardcoding depth to 2 for this test
    final_data = crawl_and_analyze(start_url, max_depth=2)
    return ExtractionResult(**final_data)