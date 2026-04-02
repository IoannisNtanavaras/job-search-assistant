"""
cv_matcher.py - MATCHING ME ΒΙΟΓΡΑΦΙΚΟ
=======================================
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
import PyPDF2
import pandas as pd
import json
import os
import re
import time
from typing import Dict, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class CVMatcher:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("❌ Δεν βρέθηκε GROQ_API_KEY")
        
        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0.2,
            groq_api_key=api_key
        )
        
        self.match_template = PromptTemplate(
            input_variables=["cv", "job_title", "job_desc"],
            template="""
            Σύγκρινε το βιογραφικό με την αγγελία:
            
            ΒΙΟΓΡΑΦΙΚΟ: {cv}
            
            ΘΕΣΗ ΕΡΓΑΣΙΑΣ: {job_title}
            ΠΕΡΙΓΡΑΦΗ: {job_desc}
            
            Δώσε ΜΟΝΟ JSON:
            {{
                "match": 0-100,
                "good_skills": ["skill1"],
                "missing_skills": ["skill2"],
                "advice": "σύντομη συμβουλή στα ελληνικά"
            }}
            """
        )
        
        self.chain = self.match_template | self.llm
        print("✅ Matcher έτοιμος")
    
    def read_cv(self, pdf_path: str) -> str:
        text = ""
        try:
            with open(pdf_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                for page in pdf.pages[:3]:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"❌ Σφάλμα PDF: {e}")
        return text[:1500]
    
    def match_job(self, cv_text: str, job: Dict) -> Dict:
        try:
            response = self.chain.invoke({
                "cv": cv_text,
                "job_title": job.get('title', '')[:100],
                "job_desc": job.get('description', '')[:500]
            })
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return {"match": 0, "good_skills": [], "missing_skills": [], "advice": "Σφάλμα ανάλυσης"}
    
    def find_best_matches(self, cv_path: str, jobs_df: pd.DataFrame) -> pd.DataFrame:
        cv_text = self.read_cv(cv_path)
        results = []
        for _, job in jobs_df.iterrows():
            match = self.match_job(cv_text, job.to_dict())
            result_row = job.to_dict()
            result_row.update(match)
            results.append(result_row)
            time.sleep(1)
        
        df = pd.DataFrame(results)
        if 'match' in df.columns:
            df = df.sort_values('match', ascending=False)
        return df.head(10)