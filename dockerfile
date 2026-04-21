# 1. Ξεκινάμε από μια βασική εικόνα Python
FROM python:3.12-slim

# 2. Εγκαθιστούμε τον Chromium browser σαν κανονικό πακέτο Linux
RUN apt-get update && apt-get install -y chromium && rm -rf /var/lib/apt/lists/*

# 3. Ορίζουμε τον φάκελο εργασίας
WORKDIR /app

# 4. Αντιγράφουμε το requirements.txt (ΧΩΡΙΣ το playwright)
COPY requirements.txt .

# 5. Αφαιρούμε το playwright από το requirements.txt (αν υπάρχει)
RUN sed -i '/playwright/d' requirements.txt

# 6. Εγκαθιστούμε τις υπόλοιπες βιβλιοθήκες
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# 7. Εγκαθιστούμε το playwright ΜΟΝΟ του, χωρίς dependencies
RUN pip install --no-cache-dir --no-deps playwright

# 8. (ΚΛΕΙΔΙ) Λέμε στο Playwright να ΜΗΝ κατεβάσει browser
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# 9. Αντιγράφουμε τον υπόλοιπο κώδικα
COPY . .

# 10. Λέμε στο Playwright πού να βρει τον Chromium
ENV PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium

# 11. Η εντολή για να τρέξει η εφαρμογή
CMD ["streamlit", "run", "app.py", "--server.port", "10000", "--server.address", "0.0.0.0"]