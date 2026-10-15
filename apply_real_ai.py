import os

FILES = {}

FILES["core/ai_service.py"] = '''import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class AIService:
    @staticmethod
    def explain_eligibility(status: str, steps: list) -> str:
        if not GEMINI_API_KEY:
            return "Simulated AI: Add your Gemini API key to the .env file to see live, dynamic explanations."
            
        prompt = f"A candidate's eligibility was evaluated as: '{status}'. The step-by-step engine evaluation is: {json.dumps(steps)}. Write a 2-3 sentence warm, professional explanation to the candidate. Tell them exactly what is missing or failing, or congratulate them if they pass. Do not invent requirements."
        
        try:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"AI explanation temporarily unavailable: {e}"

    @staticmethod
    def extract_profile_from_resume(text: str) -> dict:
        if not GEMINI_API_KEY:
            return {"degree": "B.Tech", "branch": "Computer Science", "graduation_year": 2026, "age": 22}
            
        prompt = f"Extract the candidate's academic details from the provided resume text. Return ONLY a valid JSON object using exactly these keys: 'degree' (string), 'branch' (string), 'graduation_year' (integer), 'age' (integer). If a piece of information is missing, use null.\\n\\nResume Text:\\n{text[:5000]}"
        
        try:
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            return json.loads(response.text)
        except Exception as e:
            print(f"AI parsing error: {e}")
            return {}
'''

for path, content in FILES.items():
    with open(path, "w") as f:
        f.write(content)
