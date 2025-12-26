from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from core.crawler import crawl_website
from core.agent1 import analyze_docs
from core.database import init_db, save_result

# Initialize the API app
app = FastAPI(title="Pulse API", description="Headless Module Extraction Engine")

# Ensure DB is ready
init_db()

class ExtractionRequest(BaseModel):
    url: str
    depth: int = 2

@app.get("/")
def health_check():
    return {"status": "online", "service": "Pulse Agent"}

@app.post("/extract")
async def extract_modules(payload: ExtractionRequest):
    """
    Trigger the crawler and AI agent via API instead of UI.
    Returns the strict JSON format required by the assignment.
    """
    try:
        print(f"API Request received for: {payload.url}")
        
        # 1. Reuse the exact same crawler logic
        raw_data = crawl_website(payload.url, payload.depth)
        
        if not raw_data:
            raise HTTPException(status_code=400, detail="Crawler found no content. Check URL.")
            
        # 2. Reuse the exact same AI logic
        combined_text = "\n".join(raw_data)
        result = analyze_docs(combined_text)
        
        if not result:
            raise HTTPException(status_code=500, detail="AI Analysis failed.")
            
        # 3. Save to DB (Persistence)
        save_result(payload.url, result.modules)
        
        # 4. Format for Assignment (Strict JSON)
        # We replicate the helper logic here for consistency
        final_output = []
        for m in result.modules:
            subs = {sub.name: sub.description for sub in m.submodules}
            final_output.append({
                "module": m.module_name,
                "Description": m.description,
                "Submodules": subs,
                "Confidence": f"{m.confidence_score}%"
            })
            
        return {
            "status": "success", 
            "target": payload.url,
            "data": final_output
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))