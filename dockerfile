# 1. Χρησιμοποιούμε μια επίσημη εικόνα που έχει ήδη τον browser και ΔΕΝ χρειάζεται root
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

# 2. Ορίζουμε τον φάκελο εργασίας
WORKDIR /app

# 3. Αντιγράφουμε τα αρχεία που χρειάζονται για την εγκατάσταση
COPY requirements.txt .

# 4. Εγκαθιστούμε τις βιβλιοθήκες Python
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 5. Αντιγράφουμε τον υπόλοιπο κώδικα
COPY . .

# 6. Λέμε στο Playwright να μΗΝ κατεβάσει browser, χρησιμοποιεί αυτόν της εικόνας
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# 7. Η εντολή για να τρέξει η εφαρμογή
CMD ["streamlit", "run", "app.py", "--server.port", "10000", "--server.address", "0.0.0.0"]