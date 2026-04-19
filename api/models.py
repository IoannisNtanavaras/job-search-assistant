"""
api/models.py - Pydantic models για το FastAPI
"""

from pydantic import BaseModel
from typing import List, Optional

class SearchRequest(BaseModel):
    """Τι στέλνει ο χρήστης για αναζήτηση"""
    search_term: str
    max_results: Optional[int] = 10

class JobResponse(BaseModel):
    """Τι επιστρέφει το API για κάθε αγγελία"""
    title: str
    company: str
    location: str
    job_type: str
    link: str
    description: str
    salary: Optional[str] = None
    match_score: Optional[float] = None

class AnalyzeRequest(BaseModel):
    """Τι στέλνει ο χρήστης για ανάλυση"""
    jobs: List[dict]

class MatchRequest(BaseModel):
    """Τι στέλνει ο χρήστης για matching"""
    cv_text: str
    jobs: List[dict]

class HealthResponse(BaseModel):
    """Απάντηση για health check"""
    status: str
    version: str