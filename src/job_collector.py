"""
job_collector.py - ΣΥΛΛΕΚΤΗΣ ΜΕ FIRECRAWL SEARCH + GROQ
=========================================================
1. Firecrawl.search() βρίσκει πραγματικές αγγελίες από το διαδίκτυο
2. Scrape κάθε αποτελέσματος
3. Groq εξαγωγή δομημένων δεδομένων
"""

import os
import json
import sys
import time
import re
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from playwright.sync_api import Playwright
import pandas as pd

load_dotenv()

# Streamlit Cloud: Βρες τον σωστό browser
if sys.platform == "linux":
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/home/appuser/.cache/ms-playwright"
    os.environ["PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD"] = "1"

class JobCollector:
    """
    Συλλέκτης  για εύρεση αγγελιών
    """
    
    def __init__(self, playwright: Playwright):
        self.playwright = playwright

        # Για Streamlit Cloud: chrome/chromium path
        import sys
        if sys.platform == "linux":
            self.browser = self.playwright.chromium.launch(
                headless=True,
                executable_path="/usr/bin/chromium"  # ← Πρόσθεσε αυτό
            )
        else:
            self.browser = self.playwright.chromium.launch(headless=False)

        
        self.context = self.broswer.new_context()
        self.page = self.context.new_page()
        
        
        # Groq initialization
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("❌ Δεν βρέθηκε GROQ_API_KEY στο .env")
        
        self.groq = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.1,
            groq_api_key=groq_api_key
        )
        
        self.all_jobs = []
        print("✅ Job Collector Έτοιμος!")

    def search_jobs(self, search_term: str) -> List:
        """
        Αναζήτηση αγγελιών με Firecrawl search
        """
        
        all_jobs=[]
          
        try:
             
            self.page.goto("https://www.kariera.gr")
            self.page.locator("input[placeholder='e.g. Sales Assistant']").fill(search_term)
            self.page.locator("input[placeholder='e.g. Sales Assistant']").press("Enter")
            time.sleep(5)
            link_search = self.page.url
            all_buttons =  self.page.get_by_role('button').all()

            
            for button in all_buttons:
                soup = BeautifulSoup(button.inner_html(), 'html.parser')
                links = soup.find_all('a')
                for link in links:
                    href = link.get('href')
                    if href and href.startswith("/jobs/"):
                        print(href)
                        all_jobs.append(button.all_text_contents()[0]+ link_search+ href)
                     
                

            

        except Exception as e:
                print(f"   ⚠️ Σφάλμα κατά το scraping: {e} ")
        
        return all_jobs
            
        

    def _extract_with_groq(self, content: str, search_term: str) -> List[Dict]:
        """
        Εξαγωγή δομημένων δεδομένων από περιεχόμενο με Groq
        """
        prompt = PromptTemplate(
            template="""Από τα παρακάτω περιεχομενο  θα  εξάγεις  πληροφορίες για {search_term}.
            Το περιοχομενο ειναι λιστα με αγγελιες .
Περιεχομενο:
{content}

ΕΠΙΣΤΡΕΨΕ ΜΟΝΟ JSON με αυτή τη μορφή:
{{
    "title": "ο τίτλος της θέσης",
    "company": "το όνομα της εταιρείας",
    "location": "η τοποθεσία",
    "job_type": "ο τύπος απασχόλησης (πλήρης, μερική, remote κλπ)",
    "description": "σύντομη περιγραφή",
    "salary": "ο μισθός αν αναφέρεται, αλλιώς κενό",
    "link":"το link της δουλειας αν υπαρχει"
}}

Αν δεν μπορείς να εξαγάγεις κάποιο πεδίο, βάλε κενό string.
Μην ξεχνάς, ΕΠΙΣΤΡΕΨΕ ΜΟΝΟ JSON, χωρίς εξηγήσεις ή σχόλια.
""",
            input_variables=["content", "search_term"]
        )

        chain = prompt | self.groq
        job=[]
        
        try:
            # Περιόρισε content
            if len(content) > 4000:
                content = content[:4000]

            response = chain.invoke({
                "content": content,
                "search_term" : search_term
            })

            print(response.text)
           

            # Εξαγωγή JSON από την απάντηση
            json_match = re.findall(r'\{[^{}]*\}', response.text, re.DOTALL)
            
            
            
            if json_match:
                for match in json_match :
                    job_data = json.loads(match)
                # Δημιουργία εμπλουτισμένου job
                    job_match = {
                        'title': job_data["title"],
                        'company': job_data["company"],
                        'location': job_data["location"],
                        'job_type': job_data["job_type"],
                        'description': job_data["description"],
                        'salary': job_data["salary"],
                        'link': job_data["link"],
                        'collected_at': datetime.now().isoformat()
                    }
                    job.append(job_match)
                return job
            else:
                return []
                
        except Exception as e:
            print(f"      ⚠️ Groq error: {e}")
            return []

    

    def search_all_sites(self, search_term: str) -> List[Dict]:
        """
        Κύρια μέθοδος αναζήτησης
        """
        print(f"\n🔥 Αναζήτηση για: '{search_term}'")
        
        jobs_content = self.search_jobs(search_term)
        
        content = ""
        for cont in jobs_content :
            content+=cont +"\n"
        print(content+"AYTO EINAI TO CONTENT")

        
        
        jobs = self._extract_with_groq(content, search_term)
        print(jobs)
        self.all_jobs.extend(jobs)

       
        
        print(f"\n📊 Σύνολο: {len(self.all_jobs)} αγγελίες")
        return self.all_jobs

    def save_jobs(self) -> str:
        """Αποθήκευση αγγελιών"""
        filename = f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("data/raw_jobs", exist_ok=True)
        filepath = os.path.join("data/raw_jobs", filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.all_jobs, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Αποθηκεύτηκαν {len(self.all_jobs)} αγγελίες στο {filepath}")
        return filepath