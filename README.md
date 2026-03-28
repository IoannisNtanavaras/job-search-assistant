# 🔥 Job Search Assistant

Ένα έξυπνο εργαλείο αναζήτησης εργασίας που χρησιμοποιεί **Playwright** για αυτοματοποιημένη πλοήγηση και **Groq AI** για εξαγωγή δομημένων δεδομένων από αγγελίες εργασίας.

## ✨ Χαρακτηριστικά

- 🔍 **Αυτόματη αναζήτηση** αγγελιών σε δημοφιλείς ιστοσελίδες (Kariera.gr, Skywalker.gr, LinkedIn, Indeed)
- 🤖 **AI εξαγωγή δεδομένων** με Groq (τίτλος, εταιρεία, τοποθεσία, τύπος απασχόλησης, link)
- 📊 **Ανάλυση αγγελιών** και εξαγωγή skills
- 🎯 **Matching βιογραφικού** με AI (βρίσκει τις καλύτερες θέσεις για εσένα)
- 🖥️ **Streamlit UI** για εύκολη χρήση

## 🛠️ Τεχνολογίες

| Εργαλείο | Χρήση |
|----------|-------|
| **Playwright** | Αυτοματοποιημένη πλοήγηση σε ιστοσελίδες |
| **Groq AI** | Εξαγωγή δομημένων δεδομένων από κείμενο |
| **LangChain** | Διαχείριση prompts και chains |
| **Streamlit** | Γραφικό περιβάλλον χρήστη |
| **Pandas** | Διαχείριση δεδομένων |

## 📦 Εγκατάσταση

### 1. Δημιουργία virtual environment
bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

### 2.Εγκατάσταση βιβλιοθηκών
bash
pip install -r requirements.txt

### 3.Εγκατάσταση browsers για Playwright
bash
playwright install chromium

### 4.Δημιουργία αρχείου .env με API keys
env
GROQ_API_KEY=gsk_το-groq-key-σου

### 5.🚀 Εκτέλεση
bash
streamlit run app.py
