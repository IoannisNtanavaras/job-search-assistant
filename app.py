"""
app.py - JOB SEARCH ASSISTANT ME FIRECRAWL SEARCH
===================================================
Χρήση Firecrawl search για εύρεση πραγματικών αγγελιών
"""

from playwright.sync_api import sync_playwright
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path
import os
import asyncio

sys.path.append(str(Path(__file__).parent))

from src.job_collector import JobCollector
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Ρύθμιση σελίδας
st.set_page_config(
    page_title="Job Search AI - Firecrawl Search",
    page_icon="🔥",
    layout="wide"
)

# Αρχικοποίηση session state
if 'jobs_df' not in st.session_state:
    st.session_state.jobs_df = None
if 'page' not in st.session_state:
    st.session_state.page = "main"
if 'searching' not in st.session_state:
    st.session_state.searching = False
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'last_search' not in st.session_state:
    st.session_state.last_search = ""

# CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .job-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        margin-bottom: 1rem;
    }
    .stButton button {
        width: 100%;
    }
    .footer {
        text-align: center;
        padding: 2rem;
        color: #6c757d;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🔥 Firecrawl Search")
    st.markdown("**Αναζήτηση σε όλο το διαδίκτυο**")
    st.markdown("---")

    if st.button("🏠 Αρχική", use_container_width=True):
        st.session_state.page = "main"
        st.rerun()

    if st.button("🔍 Αναζήτηση", use_container_width=True):
        st.session_state.page = "search"
        st.rerun()

    if st.session_state.jobs_df is not None:
        st.metric("📊 Αγγελίες", len(st.session_state.jobs_df))

    st.markdown("---")
    st.markdown("Made with ❤️ in Greece")

# ΑΡΧΙΚΗ ΣΕΛΙΔΑ
if st.session_state.page == "main":
    st.markdown("""
    <div class="main-header">
        <h1>🔥 Job Search Assistant - Firecrawl Search</h1>
        <p>Αναζήτηση εργασίας σε όλο το διαδίκτυο</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📌 Πώς λειτουργεί:")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 1. 🔍 Αναζήτηση")
        st.markdown("Γράφεις τι ψάχνεις (π.χ. Python Developer)")
    with col2:
        st.markdown("### 2. 🤖 Firecrawl Search")
        st.markdown("Ψάχνει στο διαδίκτυο για πραγματικές αγγελίες")
    with col3:
        st.markdown("### 3. 📊 Αποτελέσματα")
        st.markdown("Βλέπεις τις αγγελίες με όλες τις λεπτομέρειες")

    st.divider()
    
    if st.button("🚀 Ξεκίνα Αναζήτηση", use_container_width=True):
        st.session_state.page = "search"
        st.rerun()

# ΣΕΛΙΔΑ ΑΝΑΖΗΤΗΣΗΣ
elif st.session_state.page == "search":
    st.title("🔍 Αναζήτηση Εργασίας")
    st.markdown("Γράψε **τι ψάχνεις** και το Firecrawl search βρίσκει αγγελίες από όλο το διαδίκτυο!")

    job = st.text_input("Τι ψάχνεις;", placeholder="π.χ. Python Developer, Java Engineer, Data Scientist",
                        key="search_input", value=st.session_state.last_search)

    col1, col2 = st.columns(2)
    with col1:
        search_button = st.button("🚀 Αναζήτηση", type="primary",
                                 use_container_width=True,
                                 disabled=st.session_state.searching)
    with col2:
        if st.button("🏠 Πίσω στην Αρχική", use_container_width=True):
            st.session_state.page = "main"
            st.rerun()

    # Εμφάνιση προηγούμενων αποτελεσμάτων
    if st.session_state.search_results and not st.session_state.searching:
        st.success(f"✅ Βρέθηκαν {len(st.session_state.search_results)} αγγελίες για '{st.session_state.last_search}'!")
        
        for idx, job in enumerate(st.session_state.search_results):
            with st.container():
                st.markdown(f"### {idx+1}. {job.get('title', 'Χωρίς τίτλο')}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**🏢 Εταιρεία:** {job.get('company', 'Άγνωστη')}")
                with col2:
                    st.markdown(f"**📍 Τοποθεσία:** {job.get('location', 'Άγνωστη')}")
                with col3:
                    st.markdown(f"**💼 Τύπος:** {job.get('job_type', 'Άγνωστος')}")
                
                if job.get('link'):
                    st.markdown(f"🔗 [Πάτα εδώ για την αγγελία]({job['link']})")
                
                if job.get('description'):
                    st.markdown(f"**📝 {job['description']}**")
                
                if job.get('salary'):
                    st.markdown(f"**💰 Μισθός:** {job['salary']}")
                
                st.divider()

    # Νέα αναζήτηση
    if search_button and not st.session_state.searching:
        if not job or job.strip() == "":
            st.warning("Γράψε τι ψάχνεις!")
        else:
            st.session_state.searching = True
            st.session_state.last_search = job.strip()
            st.rerun()

    # Εκτέλεση αναζήτησης
    if st.session_state.searching and st.session_state.last_search:
        with st.spinner(f"🔍 Το Firecrawl ψάχνει για '{st.session_state.last_search}'..."):
            try:
                with sync_playwright() as play:
                    collector = JobCollector(play)
                    jobs = collector.search_all_sites(st.session_state.last_search)

                if jobs:
                    collector.save_jobs()
                    st.session_state.search_results = jobs
                    st.session_state.jobs_df = pd.DataFrame(jobs)
                else:
                    st.warning("⚠️ Δεν βρέθηκαν αγγελίες. Δοκίμασε άλλη λέξη!")
                    st.session_state.search_results = None

            except Exception as e:
                st.error(f"❌ Σφάλμα: {e}")

            st.session_state.searching = False
            st.rerun()

st.markdown("""
<div class="footer">
    <p>🔥 Job Search Assistant - Firecrawl Search v2.0 | Made with ❤️ in Greece</p>
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    pass