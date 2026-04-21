# 1. Ξεκινάμε από μια βασική εικόνα Python
FROM python:3.12-slim

# 2. Εγκαθιστούμε τον Chromium browser σαν κανονικό πακέτο Linux
RUN apt-get update && apt-get install -y chromium && rm -rf /var/lib/apt/lists/*

# 3. Ορίζουμε τον φάκελο εργασίας
WORKDIR /app

# 4. Αντιγράφουμε το requirements.txt
COPY requirements.txt .

# 5. (ΚΛΕΙΔΙ) Λέμε στο Playwright να ΜΗΝ κατεβάσει browser, ΠΡΙΝ καν εγκατασταθεί
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# 6. Εγκαθιστούμε τις βιβλιοθήκες Python
#    Το Playwright θα δει τη μεταβλητή και θα προσπεράσει την εγκατάσταση
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 7. Αντιγράφουμε τον υπόλοιπο κώδικα
COPY . .

# 8. Λέμε στο Playwright πού να βρει τον Chromium
ENV PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium

# 9. Η εντολή για να τρέξει η εφαρμογή
CMD ["streamlit", "run", "app.py", "--server.port", "10000", "--server.address", "0.0.0.0"]