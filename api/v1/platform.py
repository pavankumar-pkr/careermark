from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
import subprocess

router = APIRouter()

class ScraperStatus(BaseModel):
    message: str
    status: str

@router.post("/scrape", response_model=ScraperStatus)
def trigger_scraper(background_tasks: BackgroundTasks):
    """
    Triggers the Playwright scraper in the background.
    """
    def run_scraper_script():
        try:
            # Executes your existing Playwright script
            subprocess.run(["python", "scripts/scrape_dynamic.py"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Scraping failed: {e}")

    # We run this in the background so the API doesn't time out while Playwright works
    background_tasks.add_task(run_scraper_script)
    
    return {"message": "Dynamic web scraper initiated.", "status": "running"}

# Keep your existing pipeline endpoints here as well
@router.get("/pipeline")
def get_pipeline():
    return {"status": "success"}

@router.put("/pipeline/{app_id}")
def update_pipeline(app_id: int):
    return {"status": "success", "app_id": app_id}
