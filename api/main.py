"""
api/main.py - FastAPI endpoints
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import sys
import tempfile

# Προσθήκη του parent directory στο path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import SearchRequest, JobResponse, HealthResponse
from src.job_collector import JobCollector
from src.job_analyzer import JobAnalyzer
from src.cv_matcher import CVMatcher

# Δημιουργία FastAPI app
app = FastAPI(
    title="Job Search Assistant API",
    description="AI-powered job search and CV matching API",
    version="1.0.0"
)

# CORS - επιτρέπει σε άλλες εφαρμογές (π.χ. Streamlit) να καλούν το API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Για ανάπτυξη - σε production βάλε συγκεκριμένα domains
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ ENDPOINTS ============

@app.get("/", response_model=HealthResponse)
async def root():
    """Έλεγχος ότι το API τρέχει"""
    return {"status": "running", "version": "1.0.0"}

@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check για το Render"""
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/search", response_model=List[JobResponse])
async def search_jobs(request: SearchRequest):
    """
    Αναζήτηση αγγελιών
    
    - **search_term**: Η λέξη που ψάχνεις (π.χ. "Python Developer")
    - **max_results**: Πόσα αποτελέσματα θέλεις (default: 10)
    """
    try:
        from playwright.sync_api import sync_playwright
        import threading
        import time
        
        result = []
        
        def run_search():
            nonlocal result
            with sync_playwright() as p:
                collector = JobCollector(p)
                result = collector.search_all_sites(request.search_term)
            if result :
                collector.save_jobs()
        
        thread = threading.Thread(target=run_search)
        thread.start()
        thread.join(timeout=60)
        
        if not result:
            raise HTTPException(status_code=404, detail="No jobs found")
        
        
        return result[:request.max_results]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_jobs():
    """
    Ανάλυση αγγελιών με Groq AI
    
    Διαβάζει το πιο πρόσφατο JSON από data/raw_jobs/
    και αναλύει όλες τις αγγελίες
    """
    try:
        import threading
        import time
        
        result = None
        
        def run_analysis():
            nonlocal result
            analyzer = JobAnalyzer()
            result = analyzer.analyze_batch_from_links()
        
        thread = threading.Thread(target=run_analysis)
        thread.start()
        thread.join(timeout=120)  # 2 λεπτά timeout (ανάλυση θέλει χρόνο)
        
        if result is None:
            raise HTTPException(status_code=408, detail="Analysis timeout")
        
        if result.empty:
            raise HTTPException(status_code=404, detail="No jobs found or analysis failed")
        
        return result.to_dict('records')
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/match")
async def match_cv(cv: UploadFile = File(...)):
    """
    Matching βιογραφικού με αποθηκευμένες αγγελίες
    """
    try:
        import threading
        import tempfile
        import glob
        import json
        import pandas as pd
        import os
        
        result = None
        temp_path = None
        
        def run_match():
            nonlocal result, temp_path
            # Αποθήκευση βιογραφικού
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(cv.file.read())
                temp_path = tmp.name
            
            # Διάβασε το πιο πρόσφατο JSON
            json_files = glob.glob("data/raw_jobs/*.json")
            if not json_files:
                return
            
            latest_file = max(json_files, key=os.path.getmtime)
            with open(latest_file, 'r', encoding='utf-8') as f:
                jobs = json.load(f)
            
            # Matching
            matcher = CVMatcher()
            matches = matcher.find_best_matches(temp_path, pd.DataFrame(jobs))
            result = matches.to_dict('records')
        
        thread = threading.Thread(target=run_match)
        thread.start()
        thread.join(timeout=60)
        
        # Καθαρισμός
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        
        if result is None:
            raise HTTPException(status_code=408, detail="Matching timeout")
        
        if not result:
            raise HTTPException(status_code=404, detail="No matches found")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))