import sys, os
import requests
from bs4 import BeautifulSoup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.database import SessionLocal
from db.models import Opportunity, Requirement

def scrape_and_load():
    print("Fetching live job data...")
    url = "https://realpython.github.io/fake-jobs/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    
    db = SessionLocal()
    jobs = soup.find_all("div", class_="card-content")
    count = 0
    
    for job in jobs[:5]:
        title = job.find("h2", class_="title").text.strip()
        company = job.find("h3", class_="company").text.strip()
        
        existing = db.query(Opportunity).filter(Opportunity.title == title).first()
        if not existing:
            new_opp = Opportunity(
                title=title,
                organization=company,
                requirements=[
                    Requirement(field_name="degree", operator="==", target_value="B.Tech"),
                    Requirement(field_name="branch", operator="==", target_value="Computer Science")
                ]
            )
            db.add(new_opp)
            count += 1
            
    db.commit()
    print(f"Successfully scraped and added {count} new live jobs to the database!")
    db.close()

if __name__ == "__main__":
    scrape_and_load()
