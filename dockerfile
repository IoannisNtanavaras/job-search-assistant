# 1. Ξεκινάμε από μια εικόνα που έχει ήδη τα πάντα για το Playwright
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

# 2. Ορίζουμε τον φάκελο εργασίας μας
WORKDIR /app

# 3. Αντιγράφουμε τα αρχεία του project μας
COPY ./requirements.txt /app/requirements.txt

# 4. Εγκαθιστούμε τις βιβλιοθήκες Python
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 5. Αντιγράφουμε τον υπόλοιπο κώδικα
COPY . /app

# 6. Η εντολή για να τρέξει η εφαρμογή μας
CMD ["streamlit", "run", "app.py", "--server.port", "10000", "--server.address", "0.0.0.0"]