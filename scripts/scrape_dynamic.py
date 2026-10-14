import sys, os
from playwright.sync_api import sync_playwright
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import SessionLocal
from db.models import Opportunity, Requirement

def scrape_dynamic_jobs():
    print("Launching headless browser for dynamic scraping...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        # Scraping a dynamic job board (Y Combinator jobs as a live example)
        page.goto("https://www.ycombinator.com/jobs", wait_until="networkidle")
        
        # Wait for the JS job cards to load
        page.wait_for_selector(".job-name", timeout=10000)
        
        job_elements = page.query_selector_all(".job-name")[:5]
        company_elements = page.query_selector_all(".company-name")[:5]
        
        db = SessionLocal()
        count = 0
        
        for job, company in zip(job_elements, company_elements):
            title = job.inner_text().strip()
            org = company.inner_text().strip()
            
            existing = db.query(Opportunity).filter(Opportunity.title == title).first()
            if not existing:
                new_opp = Opportunity(
                    title=title,
                    organization=org,
                    requirements=[
                        Requirement(field_name="degree", operator="==", target_value="B.Tech"),
                        Requirement(field_name="branch", operator="==", target_value="Computer Science")
                    ]
                )
                db.add(new_opp)
                count += 1
                
        db.commit()
        db.close()
        browser.close()
        print(f"Successfully scraped {count} dynamic jobs using Playwright!")

if __name__ == "__main__":
    scrape_dynamic_jobs()
