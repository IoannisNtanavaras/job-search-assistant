# Χρησιμοποιούμε την επίσημη εικόνα του Playwright που έχει ήδη τα πάντα
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

# Ορίζουμε τον φάκελο εργασίας
WORKDIR /app

# Αντιγράφουμε το requirements.txt
COPY requirements.txt .

# Εγκαθιστούμε τις βιβλιοθήκες Python
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Αντιγράφουμε τον υπόλοιπο κώδικα
COPY . .

# Αυτή η γραμμή είναι το "κλειδί": Λέει στο Playwright να ΜΗΝ κατεβάσει browser
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Η εντολή για να τρέξει η εφαρμογή
CMD ["streamlit", "run", "app.py", "--server.port", "10000", "--server.address", "0.0.0.0"]