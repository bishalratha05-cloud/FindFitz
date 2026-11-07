# FindFitz — Information Retrieval System

A basic web-based information retrieval system built with Flask and Python. FindFitz indexes text documents, searches them using TF-IDF, and ranks results by cosine similarity.

## Features

- Upload and index `.txt` and `.md` documents
- Search indexed documents
- TF-IDF document representation and cosine-similarity ranking
- Tokenization and Porter stemming
- Inverted index viewer
- Search history
- Delete documents and rebuild the index
- Responsive interface

## Requirements

- Python 3.10+
- pip

## Setup

```bash
git clone https://github.com/bishalratha05-cloud/findfitzz.git
cd findfitzz

python -m venv .venv
```

Activate the environment:

**Windows PowerShell**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows Command Prompt**
```cmd
.venv\Scripts\activate
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

Install dependencies and run:

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:8000 in your browser.

## Add documents

Open **Documents** in the navigation bar and upload `.txt` or `.md` files. The files are indexed automatically. Search from the home page.

## How retrieval works

1. Documents are stored in SQLite.
2. Text is tokenized and normalized using lowercase conversion and Porter stemming.
3. Scikit-learn converts the document collection and query into TF-IDF vectors.
4. Cosine similarity measures the relevance of each document to the query.
5. Results with a positive score are sorted from highest to lowest similarity.

## Project structure

```text
findfitzz/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── documents/
│   ├── information_retrieval.txt
│   ├── search_engines.txt
│   └── tfidf.txt
├── static/
│   └── style.css
└── templates/
    ├── base.html
    ├── index.html
    ├── documents.html
    ├── history.html
    ├── inverted_index.html
    └── about.html
```

## GitHub

Create a new public repository named `findfitz` under `bishalratha05-cloud`, then run:

```bash
git init
git add .
git commit -m "Initial commit: FindFitz information retrieval system"
git branch -M main
git remote add origin https://github.com/bishalratha05-cloud/findfitzz.git
git push -u origin main
```

## Developer

**Bishal Ratha**  
Email: bishalratha05@gmail.com  
GitHub: https://github.com/bishalratha05-cloud

## Academic note

This is an educational, baseline information retrieval system. TF-IDF and cosine similarity are used for ranked retrieval; it is not a production web crawler or internet-wide search engine.


## Render deployment

Build command: `pip install -r requirements.txt`  
Start command: `gunicorn app:app`
