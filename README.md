# CareerMark (Mark 2)

A production-ready platform that automates career discovery and eligibility tracking using deterministic mathematics, live web scraping, and Google Gemini AI.

## Core Features
*   **Live Web Scraping:** Pulls real job postings into a normalized database using BeautifulSoup.
*   **AI Integration (Track 1):** Google Gemini parses resumes and generates dynamic, plain-English eligibility explanations.
*   **Deterministic Engine:** A strict mathematical engine evaluates candidate profiles against exact job requirements.
*   **Durable Background Queues:** Tracks application deadlines and processes automated tasks safely.
*   **Live Notifications (Track 2):** Sends real-time deadline warnings via SMTP directly to the user's inbox.

## Tech Stack
*   **Backend:** FastAPI, Python 3.9
*   **Database:** SQLAlchemy (SQLite default)
*   **Scraping:** BeautifulSoup
*   **AI:** Google Generative AI (Gemini)
*   **Email:** smtplib

## Setup Instructions

1.  **Clone & Install**
    ```bash
    git clone [https://github.com/yourusername/careermark.git](https://github.com/yourusername/careermark.git)
    cd careermark
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Environment Variables**
    Create a `.env` file in the root directory with the following:
    ```
    SECRET_KEY=your_secure_random_string
    ALLOWED_ORIGINS=http://localhost,[http://127.0.0.1:8000](http://127.0.0.1:8000)
    DATABASE_URL=sqlite:///./careermark.db
    GEMINI_API_KEY=your_gemini_api_key
    SMTP_USERNAME=your.email@gmail.com
    SMTP_PASSWORD=your_16_letter_app_password
    ```

3.  **Run Migrations & Seed Database**
    ```bash
    python3 scripts/reset_db.py
    ```

4.  **Start the Server**
    ```bash
    python3 -m uvicorn main:app --reload --port 8000
    ```
