FROM python:3.11-slim

WORKDIR /app

# System dependencies for lxml / BeautifulSoup
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download NLTK data
RUN python -c "import nltk; \
    [nltk.download(r, quiet=True) for r in \
     ['stopwords','wordnet','omw-1.4','punkt','punkt_tab']]"

COPY . .

# models/ dir may be empty; create it so the app doesn't crash on startup
RUN mkdir -p models

EXPOSE 8000

CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"
