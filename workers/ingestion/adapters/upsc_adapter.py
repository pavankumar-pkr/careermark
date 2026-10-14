import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List

class UPSCAdapter:
    """
    Live scraping adapter for Union Public Service Commission (UPSC).
    Targets official active exams endpoint.
    """
    def __init__(self):
        self.source_id = "UPSC_1"
        self.official_domain = "upsc.gov.in"
        self.active_exams_url = "https://www.upsc.gov.in/examinations/active-exams"

    def fetch(self) -> Dict[str, Any]:
        """Attempts live fetch, falls back to secure fixtures if firewalled."""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (CareerMark/1.0 Trust Engine)"}
            res = requests.get(self.active_exams_url, headers=headers, timeout=8)
            res.raise_for_status()
            return {"content": res.content, "status": "LIVE_SUCCESS"}
        except Exception as e:
            return {"content": self._get_fallback_fixture(), "status": f"FALLBACK_TRIGGERED: {str(e)}"}

    def parse_table(self, html_content: bytes) -> List[Dict[str, str]]:
        """Parses the UPSC active examinations HTML tables."""
        soup = BeautifulSoup(html_content, 'html.parser')
        opportunities = []
        # Extraction logic targeting UPSC's specific table structure
        for row in soup.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) > 3:
                opportunities.append({
                    "title": cols[0].text.strip(),
                    "closing_date": cols[3].text.strip()
                })
        return opportunities

    def _get_fallback_fixture(self) -> bytes:
        return b"<html><table><tr><td>Engineering Services (Preliminary) Examination, 2027</td><td></td><td></td><td>06/10/2026 - 6:00pm</td></tr></table></html>"
