"""
Simple FastAPI web interface for ClipScribe
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import os
from pathlib import Path

app = FastAPI(title="ClipScribe Web", description="Video Intelligence Extraction Web Interface")

# Get API URL from environment or default
API_URL = os.getenv("CLIPSCRIBE_API_URL", "http://localhost:8000")

# Templates directory
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Main web interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "web"}

@app.get("/api/health")
async def api_health():
    """Check API health"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_URL}/")
            if response.status_code == 200:
                return {"status": "healthy", "api_url": API_URL}
            else:
                return {"status": "unhealthy", "api_url": API_URL, "error": f"Status {response.status_code}"}
    except Exception as e:
        return {"status": "unhealthy", "api_url": API_URL, "error": str(e)}

@app.get("/docs")
async def api_docs():
    """Redirect to API documentation"""
    return {"message": "API docs available at /api/docs", "api_url": f"{API_URL}/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
