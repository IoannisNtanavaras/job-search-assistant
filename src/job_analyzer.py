"""
job_analyzer.py - ΑΝΑΛΥΣΗ ΜΕ GROQ
==================================
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
import pandas as pd
import json
import os
import re
import time
from typing import List, Dict
from datetime import datetime
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import glob

load_dotenv()

class JobAnalyzer:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("❌ Δεν βρέθηκε GROQ_API_KEY")
        
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.2,
            groq_api_key=api_key
        )
        
        # Prompt για ανάλυση αγγελίας με βάση το περιεχόμενο
        self.analysis_template = PromptTemplate(
            input_variables=["content"],
            template="""
            Ανάλυσε την παρακάτω αγγελία εργασίας και εξαγές τα skills και πληροφορίες:
            
            ΠΕΡΙΕΧΟΜΕΝΟ ΑΓΓΕΛΙΑΣ:
            {content}
            
            Δώσε ΜΟΝΟ JSON (χωρίς άλλο κείμενο):
            {{
                "skills": ["skill1", "skill2", "skill3"],
                "experience": "entry/junior/mid/senior",
                "salary_min": 0,
                "salary_max": 0,
                "job_type": "full-time/part-time/remote/hybrid",
                "location": "τοποθεσία της θέσης"
            }}
            
            Αν κάποιο πεδίο δεν υπάρχει, βάλε κενό string ή 0.
            """
        )
        
        self.chain = self.analysis_template | self.llm
        print("✅ Analyzer έτοιμος")
    
    def analyze_job_content(self, content: str) -> Dict:
        """
        Αναλύει το πλήρες περιεχόμενο μιας αγγελίας με Groq
        """
        try:
            # Περιόρισε το περιεχόμενο για τα tokens
            if len(content) > 4000:
                content = content[:4000]
            
            response = self.chain.invoke({
                "content": content
            })
            
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                return analysis
            return {}
        except Exception as e:
            print(f"   ⚠️ Σφάλμα ανάλυσης: {e}")
            return {'skills': [], 'experience': 'unknown', 'salary_min': 0, 'salary_max': 0, 'job_type': '', 'location': ''}
    
    def take_content_from_links(self) -> List[Dict]:
        """
        Διαβάζει το πιο πρόσφατο JSON, πηγαίνει σε κάθε link και παίρνει το περιεχόμενο
        """
        contents_with_metadata = []
        
        # 1. Βρες το πιο πρόσφατο JSON αρχείο
        json_files = glob.glob(os.path.join("data/raw_jobs", "*.json"))
        
        if not json_files:
            raise FileNotFoundError(f"❌ Δεν βρέθηκαν JSON αρχεία στο data/raw_jobs")
        
        latest_file = max(json_files, key=os.path.getmtime)
        print(f"📁 Διάβασα το: {os.path.basename(latest_file)}")
        
        # 2. Διάβασε τα δεδομένα
        with open(latest_file, 'r', encoding='utf-8') as f:
            jobs_data = json.load(f)
        
        # 3. Scrape κάθε link
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            for idx, job in enumerate(jobs_data[:10]):  # Μέχρι 10 αγγελίες
                print(f"   📥 Λήψη {idx+1}/{len(jobs_data[:10])}: {job.get('title', 'Χωρίς τίτλο')}")
                
                try:
                    page.goto(job.get('link', ''), timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_timeout(3000)
                    content = page.inner_text("body")
                    
                    contents_with_metadata.append({
                        'title': job.get('title', ''),
                        'company': job.get('company', ''),
                        'link': job.get('link', ''),
                        'content': content
                    })
                except Exception as e:
                    print(f"      ⚠️ Σφάλμα στο {job.get('link', '')}: {e}")
            
            browser.close()
        
        return contents_with_metadata
    
    def analyze_batch_from_links(self) -> pd.DataFrame:
        """
        Παίρνει τα links από το τελευταίο JSON, scrape περιεχόμενο και αναλύει
        """
        # 1. Πάρε τα περιεχόμενα από τα links
        job_contents = self.take_content_from_links()
        
        if not job_contents:
            print("⚠️ Δεν βρέθηκαν περιεχόμενα για ανάλυση")
            return pd.DataFrame()
        
        # 2. Ανάλυση κάθε αγγελίας
        analyzed = []
        for i, job in enumerate(job_contents):
            print(f"   🤖 Αναλύω {i+1}/{len(job_contents)}: {job.get('title', 'Χωρίς τίτλο')}")
            
            analysis = self.analyze_job_content(job.get('content', ''))
            
            # Συγχώνευση metadata + analysis
            result = {
                'title': job.get('title', ''),
                'company': job.get('company', ''),
                'link': job.get('link', ''),
                'skills': analysis.get('skills', []),
                'experience': analysis.get('experience', 'unknown'),
                'salary_min': analysis.get('salary_min', 0),
                'salary_max': analysis.get('salary_max', 0),
                'job_type': analysis.get('job_type', ''),
                'location': analysis.get('location', '')
            }
            analyzed.append(result)
            time.sleep(1)  # Αποφυγή rate limits
        
        # 3. Δημιουργία DataFrame
        df = pd.DataFrame(analyzed)
        
        # 4. Αποθήκευση
        os.makedirs("data/processed", exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        df.to_csv(f"data/processed/analyzed_{timestamp}.csv", index=False)
        print(f"\n💾 Αποθηκεύτηκε ανάλυση στο data/processed/analyzed_{timestamp}.csv")
        
        return df
    
    def analyze_job(self, job: Dict) -> Dict:
        """
        Legacy method - για συμβατότητα με παλιό κώδικα
        """
        try:
            response = self.chain.invoke({
                "content": job.get('description', '')[:500]
            })
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                job.update(analysis)
        except:
            job.update({'skills': [], 'experience': 'unknown', 'salary_min': 0, 'salary_max': 0})
        return job
    
    def analyze_batch(self, jobs: List[Dict]) -> pd.DataFrame:
        """
        Legacy method - για συμβατότητα με παλιό κώδικα
        """
        analyzed = []
        for i, job in enumerate(jobs):
            print(f"   Αναλύω {i+1}/{len(jobs)}")
            analyzed.append(self.analyze_job(job))
            time.sleep(1)
        
        df = pd.DataFrame(analyzed)
        os.makedirs("data/processed", exist_ok=True)
        df.to_csv(f"data/processed/analyzed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)
        return df