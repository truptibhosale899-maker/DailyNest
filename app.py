"""
DailyNest – Public News Aggregator Bot
Main Flask Application
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import hashlib
import requests
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "dailynest_secret_key_change_in_production"


@app.context_processor
def inject_globals():
    """Inject common variables into all templates automatically."""
    return dict(categories=CATEGORIES)

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
NEWS_API_KEY = "4d785e694a43460c8b5acbd9e538ce2e"          # ← Replace with your NewsAPI key
NEWS_API_URL = "https://newsapi.org/v2/"
DATABASE = "database.db"

CATEGORIES = ["technology", "sports", "business", "entertainment", "health", "science", "general"]


# ─────────────────────────────────────────────
# DATABASE HELPERS
# ─────────────────────────────────────────────
def get_db():
    """Open a database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row          # Allows dict-like access
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            preferences TEXT    DEFAULT 'general',
            telegram_id TEXT    DEFAULT '',
            created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialised.")


# ─────────────────────────────────────────────
# UTILITY FUNCTIONS
# ─────────────────────────────────────────────
def hash_password(password):
    """SHA-256 hash a password."""
    return hashlib.sha256(password.encode()).hexdigest()


def login_required(f):
    """Decorator – redirects to login if user not in session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def fetch_news(category="general", query=None, page_size=12):
    """
    Fetch news from NewsAPI.
    Returns a list of article dicts, or a fallback list on error.
    """
    try:
        if query:
            endpoint = f"{NEWS_API_URL}everything"
            params = {
                "q": query,
                "apiKey": NEWS_API_KEY,
                "pageSize": page_size,
                "language": "en",
                "sortBy": "publishedAt",
            }
        else:
            endpoint = f"{NEWS_API_URL}top-headlines"
            params = {
                "category": category,
                "apiKey": NEWS_API_KEY,
                "pageSize": page_size,
                "language": "en",
                "country": "us",
            }

        response = requests.get(endpoint, params=params, timeout=10)
        data = response.json()

        if data.get("status") == "ok":
            # Filter out articles without images or titles
            articles = [
                a for a in data.get("articles", [])
                if a.get("title") and a.get("title") != "[Removed]"
            ]
            return articles
        else:
            return get_fallback_news()

    except Exception as e:
        print(f"NewsAPI error: {e}")
        return get_fallback_news()


def get_fallback_news():
    """Return placeholder news when API is unavailable."""
    return [
        {
            "title": "DailyNest is Ready – Add Your NewsAPI Key!",
            "description": "Replace YOUR_NEWSAPI_KEY_HERE in app.py with a free key from newsapi.org to see live news.",
            "urlToImage": "https://placehold.co/600x400/7c3aed/ffffff?text=DailyNest",
            "url": "https://newsapi.org/register",
            "source": {"name": "DailyNest"},
            "publishedAt": datetime.now().isoformat(),
        },
        {
            "title": "Technology is Changing the World Fast",
            "description": "From AI to quantum computing, the pace of technological change is accelerating. Get real articles by adding your API key.",
            "urlToImage": "https://placehold.co/600x400/6d28d9/ffffff?text=Technology",
            "url": "#",
            "source": {"name": "Demo"},
            "publishedAt": datetime.now().isoformat(),
        },
        {
            "title": "Business Markets See New Highs",
            "description": "Global markets continue their upward trend as investors remain optimistic. Add NewsAPI key for live data.",
            "urlToImage": "https://placehold.co/600x400/5b21b6/ffffff?text=Business",
            "url": "#",
            "source": {"name": "Demo"},
            "publishedAt": datetime.now().isoformat(),
        },
    ]


# ─────────────────────────────────────────────
# ROUTES – PUBLIC
# ─────────────────────────────────────────────
@app.route("/")
def home():
    """Home page – trending news visible to everyone."""
    trending = fetch_news(category="general", page_size=9)
    tech     = fetch_news(category="technology", page_size=3)
    return render_template("home.html", trending=trending, tech=tech, categories=CATEGORIES)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """User registration."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm  = request.form.get("confirm_password", "").strip()

        # Basic validation
        if not username or not password:
            flash("Username and password are required.", "danger")
            return render_template("signup.html")
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("signup.html")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("signup.html")

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hash_password(password))
            )
            conn.commit()
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already taken. Try another.", "danger")
        finally:
            conn.close()

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """User login."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, hash_password(password))
        ).fetchone()
        conn.close()

        if user:
            session["user_id"]  = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {username}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    """Clear session and redirect home."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


# ─────────────────────────────────────────────
# ROUTES – PROTECTED
# ─────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    """Personalised news dashboard."""
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()

    # Parse saved preferences
    prefs = [p.strip() for p in user["preferences"].split(",") if p.strip()]
    if not prefs:
        prefs = ["general"]

    # Fetch news for each preferred category
    news_by_category = {}
    for cat in prefs:
        news_by_category[cat] = fetch_news(category=cat, page_size=6)

    return render_template(
        "dashboard.html",
        user=user,
        news_by_category=news_by_category,
        categories=CATEGORIES,
    )


@app.route("/preferences", methods=["GET", "POST"])
@login_required
def preferences():
    """Let user select news categories."""
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    if request.method == "POST":
        selected    = request.form.getlist("categories")   # Multi-select checkboxes
        telegram_id = request.form.get("telegram_id", "").strip()

        if not selected:
            selected = ["general"]

        prefs_str = ",".join(selected)
        conn.execute(
            "UPDATE users SET preferences = ?, telegram_id = ? WHERE id = ?",
            (prefs_str, telegram_id, session["user_id"])
        )
        conn.commit()
        conn.close()

        flash("Preferences saved successfully!", "success")
        return redirect(url_for("dashboard"))

    conn.close()
    current_prefs = [p.strip() for p in user["preferences"].split(",")]
    return render_template(
        "preferences.html",
        categories=CATEGORIES,
        current_prefs=current_prefs,
        user=user,
    )


@app.route("/category/<cat>")
def category(cat):
    """Browse a specific news category."""
    if cat not in CATEGORIES:
        flash("Invalid category.", "danger")
        return redirect(url_for("home"))

    articles = fetch_news(category=cat, page_size=12)
    return render_template("category.html", articles=articles, category=cat, categories=CATEGORIES)


@app.route("/search")
def search():
    """Search news by keyword."""
    query = request.args.get("q", "").strip()
    articles = []
    if query:
        articles = fetch_news(query=query, page_size=12)
    return render_template("search.html", articles=articles, query=query, categories=CATEGORIES)


# ─────────────────────────────────────────────
# API ENDPOINT (for AJAX / bot use)
# ─────────────────────────────────────────────
@app.route("/api/news/<category>")
def api_news(category):
    """JSON endpoint – used by the Telegram bot."""
    articles = fetch_news(category=category, page_size=5)
    safe = [
        {
            "title":       a.get("title", ""),
            "description": a.get("description", ""),
            "url":         a.get("url", ""),
            "source":      a.get("source", {}).get("name", ""),
        }
        for a in articles
    ]
    return jsonify(safe)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=10000)
