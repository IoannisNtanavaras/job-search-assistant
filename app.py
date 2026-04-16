"""
app.py - JOB SEARCH ASSISTANT - ΠΛΗΡΗΣ ΕΚΔΟΣΗ
===============================================
Αναζήτηση + Ανάλυση + Matching με CV
"""

import sys
import asyncio
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from pathlib import Path
import os
import re
import time

# Fix για Windows + Python 3.12
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from playwright.sync_api import sync_playwright

sys.path.append(str(Path(__file__).parent))

from src.job_collector import JobCollector
from src.job_analyzer import JobAnalyzer
from src.cv_matcher import CVMatcher

# Ρύθμιση σελίδας
st.set_page_config(
    page_title="Job Search AI",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Αρχικοποίηση session state
if 'jobs_df' not in st.session_state:
    st.session_state.jobs_df = None
if 'page' not in st.session_state:
    st.session_state.page = "main"
if 'searching' not in st.session_state:
    st.session_state.searching = False
if 'analyzing' not in st.session_state:
    st.session_state.analyzing = False
if 'matching' not in st.session_state:
    st.session_state.matching = False
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'analyzed_results' not in st.session_state:
    st.session_state.analyzed_results = None
if 'match_results' not in st.session_state:
    st.session_state.match_results = None
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
    .match-high {
        background-color: #d4edda;
        border-left-color: #28a745;
    }
    .match-medium {
        background-color: #fff3cd;
        border-left-color: #ffc107;
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
    st.title("🔥 Job Search AI")
    st.markdown("**Η έξυπνη αναζήτηση εργασίας**")
    st.markdown("---")

    if st.button("🏠 Αρχική", use_container_width=True):
        st.session_state.page = "main"
        st.rerun()

    if st.button("🔍 Αναζήτηση", use_container_width=True):
        st.session_state.page = "search"
        st.rerun()

    if st.session_state.jobs_df is not None:
        if st.button("📊 Ανάλυση Δεδομένων", use_container_width=True):
            st.session_state.page = "analyze"
            st.rerun()
        if st.button("🎯 Matching με CV", use_container_width=True):
            st.session_state.page = "match"
            st.rerun()
        st.metric("📊 Αγγελίες", len(st.session_state.jobs_df))

    st.markdown("---")
    st.markdown("Made with ❤️ in Greece")

# ==================== ΑΡΧΙΚΗ ΣΕΛΙΔΑ ====================
if st.session_state.page == "main":
    st.markdown("""
    <div class="main-header">
        <h1>🔥 Job Search Assistant</h1>
        <p>Αναζήτηση Εργασίας με Τεχνητή Νοημοσύνη</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🔍 Αναζήτηση")
        st.markdown("Ψάξε για αγγελίες σε δημοφιλείς ιστοσελίδες")
        if st.button("🚀 Πήγαινε στην Αναζήτηση", key="go_search"):
            st.session_state.page = "search"
            st.rerun()

    with col2:
        st.markdown("### 📊 Ανάλυση")
        st.markdown("Ανάλυσε τις αγγελίες με Groq AI")
        if st.session_state.jobs_df is not None:
            if st.button("📈 Πήγαινε στην Ανάλυση", key="go_analyze"):
                st.session_state.page = "analyze"
                st.rerun()
        else:
            st.info("⚠️ Πρώτα κάνε αναζήτηση")

    with col3:
        st.markdown("### 🎯 Matching")
        st.markdown("Σύγκρινε με το βιογραφικό σου")
        if st.session_state.jobs_df is not None:
            if st.button("💼 Πήγαινε στο Matching", key="go_match"):
                st.session_state.page = "match"
                st.rerun()
        else:
            st.info("⚠️ Πρώτα κάνε αναζήτηση")

    # Αν υπάρχουν ήδη δεδομένα
    if st.session_state.jobs_df is not None:
        st.divider()
        st.subheader(f"📋 Τελευταία Αναζήτηση ({len(st.session_state.jobs_df)} αγγελίες)")
        display_df = st.session_state.jobs_df[['title', 'company', 'location']].head(5)
        st.dataframe(display_df, use_container_width=True)

# ==================== ΣΕΛΙΔΑ ΑΝΑΖΗΤΗΣΗΣ ====================
elif st.session_state.page == "search":
    st.title("🔍 Αναζήτηση Εργασίας")
    st.markdown("Γράψε **τι ψάχνεις** και ψάχνουμε σε όλα τα sites!")

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
                title = job.get('title', 'Χωρίς τίτλο')
                link = job.get('link', '')
                
                if link:
                    st.markdown(f"### {idx+1}. [{title}]({link})")
                else:
                    st.markdown(f"### {idx+1}. {title}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**🏢 Εταιρεία:** {job.get('company', 'Άγνωστη')}")
                with col2:
                    st.markdown(f"**📍 Τοποθεσία:** {job.get('location', 'Άγνωστη')}")
                
                if job.get('description'):
                    st.markdown(f"**📝 {job.get('description', '')[:200]}...**")
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
        with st.spinner(f"🔍 Αναζήτηση για '{st.session_state.last_search}'..."):
            try:
                with sync_playwright() as play:
                    collector = JobCollector(play)
                    jobs = collector.search_all_sites(st.session_state.last_search)

                if jobs:
                    collector.save_jobs()
                    st.session_state.search_results = jobs
                    st.session_state.jobs_df = pd.DataFrame(jobs)
                    st.success(f"✅ Βρέθηκαν {len(jobs)} αγγελίες!")
                else:
                    st.warning("⚠️ Δεν βρέθηκαν αγγελίες. Δοκίμασε άλλη λέξη!")
                    st.session_state.search_results = None

            except Exception as e:
                st.error(f"❌ Σφάλμα: {e}")

            st.session_state.searching = False
            st.rerun()

# ==================== ΣΕΛΙΔΑ ΑΝΑΛΥΣΗΣ ====================
elif st.session_state.page == "analyze" and st.session_state.jobs_df is not None:
    st.title("📊 Ανάλυση Αγγελιών")
    st.markdown("Η ανάλυση γίνεται με Groq AI")

    col1, col2 = st.columns(2)
    with col1:
        analyze_button = st.button("🤖 Εκτέλεση Ανάλυσης", type="primary",
                                  use_container_width=True,
                                  disabled=st.session_state.analyzing)
    with col2:
        if st.button("🏠 Πίσω στην Αρχική", use_container_width=True):
            st.session_state.page = "main"
            st.rerun()

    # Ανάλυση
    if analyze_button and not st.session_state.analyzing:
        st.session_state.analyzing = True
        st.rerun()

    if st.session_state.analyzing:
        with st.spinner("Αναλύω αγγελίες με Groq AI..."):
            try:
                analyzer = JobAnalyzer()
                analyzed_df = analyzer.analyze_batch_from_links()
                st.session_state.jobs_df = analyzed_df
                # st.session_state.analyzed_results = analyzed_df
                st.success("✅ Ανάλυση ολοκληρώθηκε!")
            except Exception as e:
                st.error(f"❌ Σφάλμα ανάλυσης: {e}")
            
            st.session_state.analyzing = False
            st.rerun()

    # ΕΜΦΑΝΙΣΗ ΑΠΟΤΕΛΕΣΜΑΤΩΝ
    st.subheader("📋 Αποτελέσματα Ανάλυσης")
    
    # Επιλογή στηλών για εμφάνιση
    columns_to_show = ['title', 'company', 'skills', 'experience', 'salary_min', 'salary_max', 'job_type', 'location']
    available_columns = [col for col in columns_to_show if col in st.session_state.jobs_df.columns]
    
    # Μορφοποίηση για καλύτερη εμφάνιση
    display_df = st.session_state.jobs_df[available_columns].copy()
    
    # Μορφοποίηση skills (από string list σε readable)
    if 'skills' in display_df.columns:
        display_df['skills'] = display_df['skills'].apply(
            lambda x: ', '.join(eval(x)) if isinstance(x, str) and x.startswith('[') else str(x)
        )
    
    # Μορφοποίηση μισθών
    if 'salary_min' in display_df.columns and 'salary_max' in display_df.columns:
        display_df['salary'] = display_df.apply(
            lambda x: f"{x['salary_min']} - {x['salary_max']} €" if x['salary_min'] > 0 else "Δεν αναφέρεται",
            axis=1
        )
    
    st.dataframe(display_df, use_container_width=True)
    
    # ============ ΓΡΑΦΗΜΑΤΑ ============
    st.subheader("📈 Οπτικοποίηση Δεδομένων")
    
    # 1. Γράφημα Skills (πιο περιζήτητα)
    if 'skills' in st.session_state.jobs_df.columns:
        all_skills = []
        for skills in st.session_state.jobs_df['skills'].dropna():
            if isinstance(skills, str):
                try:
                    skills_list = eval(skills)
                    if isinstance(skills_list, list):
                        all_skills.extend(skills_list)
                except:
                    pass
            elif isinstance(skills, list):
                all_skills.extend(skills)
        
        if all_skills:
            from collections import Counter
            skill_counts = Counter(all_skills)
            skills_df = pd.DataFrame(skill_counts.most_common(15), columns=['skill', 'count'])
            
            fig = px.bar(skills_df, x='count', y='skill', orientation='h',
                        title='🔥 Top 15 Skills που ζητούνται',
                        labels={'count': 'Εμφανίσεις', 'skill': 'Skill'},
                        height=500)
            st.plotly_chart(fig, use_container_width=True)
    
    # 2. Γράφημα Εμπειρίας
    if 'experience' in st.session_state.jobs_df.columns:
        exp_counts = st.session_state.jobs_df['experience'].value_counts()
        fig2 = px.pie(values=exp_counts.values, names=exp_counts.index,
                     title='📊 Κατανομή Επιπέδων Εμπειρίας',
                     color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig2, use_container_width=True)
    
    # 3. Γράφημα Μισθών (αν υπάρχουν)
    if 'salary_min' in st.session_state.jobs_df.columns and 'salary_max' in st.session_state.jobs_df.columns:
        salary_data = st.session_state.jobs_df[
            (st.session_state.jobs_df['salary_min'] > 0) | (st.session_state.jobs_df['salary_max'] > 0)
        ]
        if not salary_data.empty:
            fig3 = px.bar(salary_data, x='title', y=['salary_min', 'salary_max'],
                         title='💰 Μισθολογικά Ranges',
                         labels={'value': 'Μισθός (€)', 'variable': 'Τύπος', 'title': 'Θέση'},
                         barmode='group')
            st.plotly_chart(fig3, use_container_width=True)
    
    # 4. Γράφημα Τύπου Απασχόλησης
    if 'job_type' in st.session_state.jobs_df.columns:
        job_type_counts = st.session_state.jobs_df['job_type'].value_counts()
        if not job_type_counts.empty:
            fig4 = px.bar(x=job_type_counts.values, y=job_type_counts.index, orientation='h',
                         title='💼 Τύποι Απασχόλησης',
                         labels={'x': 'Αριθμός Αγγελιών', 'y': 'Τύπος'})
            st.plotly_chart(fig4, use_container_width=True)

# ==================== ΣΕΛΙΔΑ MATCHING ====================
elif st.session_state.page == "match" and st.session_state.jobs_df is not None:
    st.title("🎯 Matching με Βιογραφικό")
    st.markdown("Ανέβασε το βιογραφικό σου και βρες τις καλύτερες θέσεις!")

    cv = st.file_uploader("Ανέβασε βιογραφικό (PDF)", type=['pdf'], key="cv_uploader")

    col1, col2 = st.columns(2)
    with col1:
        match_button = st.button("🔍 Βρες Matches", type="primary",
                                use_container_width=True,
                                disabled=st.session_state.matching or cv is None)
    with col2:
        if st.button("🏠 Πίσω στην Αρχική", use_container_width=True):
            st.session_state.match_results = None
            st.session_state.page = "main"
            st.rerun()

    # Εμφάνιση προηγούμενων matches
    if st.session_state.match_results is not None and not st.session_state.matching:
        st.success(f"✅ Βρέθηκαν {len(st.session_state.match_results)} matches!")
        st.subheader("📊 Αποτελέσματα Matching")
        
        for idx, (_, job) in enumerate(st.session_state.match_results.iterrows()):
            match_score = job.get('match', 0)
            card_class = "match-high" if match_score >= 70 else "match-medium" if match_score >= 40 else "job-card"
            
            with st.container():
                st.markdown(f"### {idx+1}. {job.get('title', 'Χωρίς τίτλο')}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**🏢 Εταιρεία:** {job.get('company', 'Άγνωστη')}")
                    st.markdown(f"**🎯 Ταύτιση:** {match_score}%")
                with col2:
                    st.markdown(f"**📍 Τοποθεσία:** {job.get('location', 'Άγνωστη')}")
                    st.markdown(f"**💼 Τύπος:** {job.get('job_type', 'Άγνωστος')}")
                with col3:
                    st.markdown(f"**📌 Πηγή:** {job.get('source', 'Άγνωστη')}")
                
                if job.get('advice'):
                    st.info(f"💡 **Συμβουλή:** {job.get('advice', '')}")
                
                if job.get('link'):
                    st.markdown(f"🔗 [Πάτα εδώ για την αγγελία]({job['link']})")
                
                st.divider()

    # Νέο matching
    if match_button and not st.session_state.matching and cv is not None:
        st.session_state.matching = True
        st.session_state.match_results = None
        st.rerun()

    if st.session_state.matching and cv is not None:
        temp_path = "temp_cv.pdf"
        with open(temp_path, "wb") as f:
            f.write(cv.getbuffer())
        
        with st.spinner("Αναλύω βιογραφικό και συγκρίνω με αγγελίες..."):
            try:
                matcher = CVMatcher()
                matches = matcher.find_best_matches(temp_path, st.session_state.jobs_df)
                
                if not matches.empty:
                    st.session_state.match_results = matches
                else:
                    st.warning("⚠️ Δεν βρέθηκαν matches")
                    st.session_state.match_results = None
            except Exception as e:
                st.error(f"❌ Σφάλμα: {e}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        st.session_state.matching = False
        st.rerun()

# Footer
st.markdown("""
<div class="footer">
    <p>🔥 Job Search Assistant v3.0 | Made with ❤️ in Greece | 2026</p>
</div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    pass