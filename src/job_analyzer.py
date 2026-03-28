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
from dotenv import load_dotenv

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
        
        self.analysis_template = PromptTemplate(
            input_variables=["title", "description"],
            template="""
            Ανάλυσε αυτή την αγγελία εργασίας και εξαγές τα skills:
            
            Τίτλος: {title}
            Περιγραφή: {description}
            
            Δώσε ΜΟΝΟ JSON:
            {{
                "skills": ["skill1", "skill2"],
                "experience": "entry/junior/mid/senior",
                "salary_min": 0,
                "salary_max": 0
            }}
            """
        )
        
        self.chain = self.analysis_template | self.llm
        print("✅ Analyzer έτοιμος")
    
    def analyze_job(self, job: Dict) -> Dict:
        try:
            response = self.chain.invoke({
                "title": job.get('title', '')[:100],
                "description": job.get('description', '')[:500]
            })
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                job.update(analysis)
        except:
            job.update({'skills': [], 'experience': 'unknown', 'salary_min': 0, 'salary_max': 0})
        return job
    
    def analyze_batch(self, jobs: List[Dict]) -> pd.DataFrame:
        analyzed = []
        for i, job in enumerate(jobs):
            print(f"   Αναλύω {i+1}/{len(jobs)}")
            analyzed.append(self.analyze_job(job))
            time.sleep(1)
        
        df = pd.DataFrame(analyzed)
        os.makedirs("data/processed", exist_ok=True)
        df.to_csv(f"data/processed/analyzed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)
        return df