
from pathlib import Path
import re
import sqlite3
from datetime import datetime
from collections import defaultdict

from flask import Flask, render_template, request, redirect, url_for, flash
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem import PorterStemmer

# ---------------- CONFIGURATION ----------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "documents"
DB_PATH = BASE_DIR / "findfitz.db"

ALLOWED_EXTENSIONS = {".txt", ".md"}

app = Flask(__name__)
app.secret_key = "findfitz-project-secret-key"

stemmer = PorterStemmer()


# ---------------- DATABASE ----------------

def connect_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_db():
    DATA_DIR.mkdir(exist_ok=True)

    with connect_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                indexed_at TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                result_count INTEGER NOT NULL,
                searched_at TEXT NOT NULL
            )
        """)

        db.commit()


# ---------------- TEXT PROCESSING ----------------

def tokenize(text):
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())

    return [
        stemmer.stem(word)
        for word in words
        if len(word) > 1
    ]


def load_documents():
    with connect_db() as db:
        return db.execute("""
            SELECT id, filename, content
            FROM documents
            ORDER BY filename
        """).fetchall()


# ---------------- DOCUMENT INDEXING ----------------

def index_file(path):
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return False

    try:
        content = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )
    except OSError:
        return False

    with connect_db() as db:
        db.execute("""
            INSERT INTO documents(filename, content, indexed_at)
            VALUES (?, ?, ?)

            ON CONFLICT(filename) DO UPDATE SET
                content=excluded.content,
                indexed_at=excluded.indexed_at
        """, (
            path.name,
            content,
            datetime.now().isoformat(timespec="seconds")
        ))

        db.commit()

    return True


def index_all_files():
    DATA_DIR.mkdir(exist_ok=True)

    count = 0

    for path in DATA_DIR.iterdir():
        if path.is_file() and index_file(path):
            count += 1

    return count


# ---------------- SEARCH SNIPPETS ----------------

def make_snippet(content, query, width=220):
    clean = re.sub(r"\s+", " ", content).strip()

    terms = re.findall(r"[a-zA-Z0-9]+", query)
    lower = clean.lower()

    positions = [
        lower.find(term.lower())
        for term in terms
        if lower.find(term.lower()) >= 0
    ]

    start = max(0, min(positions) - 70) if positions else 0

    snippet = clean[start:start + width]

    if start:
        snippet = "..." + snippet

    if start + width < len(clean):
        snippet += "..."

    return snippet or "No preview available."


# ---------------- INFORMATION RETRIEVAL ----------------

def search_documents(query):

    docs = load_documents()

    if not docs or not query.strip():
        return []

    corpus = [doc["content"] for doc in docs]

    vectorizer = TfidfVectorizer(
        tokenizer=tokenize,
        token_pattern=None,
        lowercase=False,
        ngram_range=(1, 2),
        sublinear_tf=True
    )

    try:
        matrix = vectorizer.fit_transform(corpus + [query])

    except ValueError:
        return []

    scores = cosine_similarity(
        matrix[-1],
        matrix[:-1]
    ).flatten()

    results = []

    for doc, score in zip(docs, scores):

        if score > 0:

            results.append({
                "id": doc["id"],
                "filename": doc["filename"],
                "score": float(score),
                "snippet": make_snippet(
                    doc["content"],
                    query
                )
            })

    return sorted(
        results,
        key=lambda item: item["score"],
        reverse=True
    )


# ---------------- INVERTED INDEX ----------------

def build_inverted_index():

    index = defaultdict(list)

    for doc in load_documents():

        seen = set(tokenize(doc["content"]))

        for term in seen:
            index[term].append(doc["filename"])

    return {
        term: sorted(names)
        for term, names in sorted(index.items())
    }


# ---------------- HOME / SEARCH PAGE ----------------

@app.route("/")
def home():

    query = request.args.get("q", "").strip()

    results = search_documents(query) if query else []

    if query:

        with connect_db() as db:

            db.execute("""
                INSERT INTO searches(
                    query,
                    result_count,
                    searched_at
                )
                VALUES (?, ?, ?)
            """, (
                query,
                len(results),
                datetime.now().isoformat(timespec="seconds")
            ))

            db.commit()

    with connect_db() as db:

        document_count = db.execute(
            "SELECT COUNT(*) FROM documents"
        ).fetchone()[0]

        search_count = db.execute(
            "SELECT COUNT(*) FROM searches"
        ).fetchone()[0]

    return render_template(
        "index.html",
        query=query,
        results=results,
        document_count=document_count,
        search_count=search_count
    )


# ---------------- DOCUMENT MANAGEMENT ----------------

@app.route("/documents", methods=["GET", "POST"])
def documents():

    if request.method == "POST":

        uploaded = request.files.getlist("files")

        saved = 0

        for file in uploaded:

            if not file or not file.filename:
                continue

            filename = Path(file.filename).name
            suffix = Path(filename).suffix.lower()

            if suffix not in ALLOWED_EXTENSIONS:

                flash(
                    f"Skipped {filename}: only TXT and MD files are supported.",
                    "error"
                )

                continue

            destination = DATA_DIR / filename

            file.save(destination)

            if index_file(destination):
                saved += 1

        if saved:
            flash(
                f"Successfully indexed {saved} document(s).",
                "success"
            )

        return redirect(url_for("documents"))

    docs = load_documents()

    return render_template(
        "documents.html",
        documents=docs
    )


# ---------------- DELETE DOCUMENT ----------------
@app.route("/documents/preview/<int:document_id>")
def preview_document(document_id):

    with connect_db() as db:
        doc = db.execute(
            "SELECT filename, content FROM documents WHERE id=?",
            (document_id,)
        ).fetchone()

    if not doc:
        flash("Document not found.", "error")
        return redirect(url_for("documents"))

    return render_template(
        "preview.html",
        document=doc
    )
@app.route("/documents/delete/<int:document_id>", methods=["POST"])
def delete_document(document_id):

    with connect_db() as db:

        doc = db.execute(
            "SELECT filename FROM documents WHERE id=?",
            (document_id,)
        ).fetchone()

        if doc:

            (DATA_DIR / doc["filename"]).unlink(missing_ok=True)

            db.execute(
                "DELETE FROM documents WHERE id=?",
                (document_id,)
            )

            db.commit()

            flash("Document deleted.", "success")

    return redirect(url_for("documents"))


# ---------------- REFRESH INDEX ----------------

@app.route("/index")
def rebuild_index():

    count = index_all_files()

    flash(
        f"Index refreshed. Processed {count} file(s).",
        "success"
    )

    return redirect(url_for("documents"))


# ---------------- SEARCH HISTORY ----------------

@app.route("/history")
def history():

    with connect_db() as db:

        searches = db.execute("""
            SELECT query, result_count, searched_at
            FROM searches
            ORDER BY id DESC
            LIMIT 50
        """).fetchall()

    return render_template(
        "history.html",
        searches=searches
    )


# ---------------- INVERTED INDEX PAGE ----------------

@app.route("/inverted-index")
def inverted_index():

    index = build_inverted_index()

    return render_template(
        "inverted_index.html",
        index=index
    )


# ---------------- ABOUT PAGE ----------------

@app.route("/about")
def about():

    return render_template("about.html")


# ---------------- APPLICATION START ----------------

initialize_db()
index_all_files()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=True
    )
