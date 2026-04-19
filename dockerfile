# 1. Ξεκινάμε από μία εικόνα που περιέχει ήδη τον browser.
# Αυτή η εικόνα ΔΕΝ θα επιχειρήσει να γίνει root.
FROM python:3.12-slim

# 2. Εγκαθιστούμε τον Chromium browser (σαν κανονικό πακέτο Linux)
RUN apt-get update && apt-get install -y chromium && rm -rf /var/lib/apt/lists/*

# 3. Ορίζουμε τον φάκελο εργασίας
WORKDIR /app

# 4. Αντιγράφουμε και εγκαθιστούμε τις βιβλιοθήκες Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 5. Αντιγράφουμε τον υπόλοιπο κώδικα
COPY . .

# 6. Λέμε στο Playwright να ΜΗΝ κατεβάσει browser, αλλά να χρησιμοποιήσει τον ήδη εγκατεστημένο
ENV PLAYWRIGHT_BROWSERS_PATH=/usr/bin
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# 7. Λέμε στο Playwright πού να βρει τον Chromium
ENV PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium

# 8. Η εντολή για να τρέξει η εφαρμογή
CMD ["streamlit", "run", "app.py", "--server.port", "10000", "--server.address", "0.0.0.0"]