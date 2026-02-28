"""
DailyNest – Public News Aggregator Bot
Main Flask Application - PostgreSQL Version
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import hashlib
import requests
import os
from datetime import datetime
from functools import wraps
import psycopg2
import psycopg2.extras

app = Flask(__name__)
app.secret_key = "dailynest_secret_key_change_in_production"

NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "4d785e694a43460c8b5acbd9e538ce2e")
NEWS_API_URL = "https://newsapi.org/v2/"
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://dailynest_user:iQYbbTddM6bBY4KfLy1tDW5296PZi5k2@dpg-d6h9ee450q8c73af3jsg-a.oregon-postgres.render.com/dailynest")

CATEGORIES = ["technology", "sports", "business", "entertainment", "health", "science", "general"]


def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          SERIAL PRIMARY KEY,
            username    TEXT UNIQUE NOT NULL,
            password    TEXT NOT NULL,
            preferences TEXT DEFAULT 'general',
            telegram_id TEXT DEFAULT '',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Database initialised.")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def fetch_news(category="general", query=None, page_size=12):
    try:
        if query:
            endpoint = f"{NEWS_API_URL}everything"
            params = {"q": query, "apiKey": NEWS_API_KEY, "pageSize": page_size, "language": "en", "sortBy": "publishedAt"}
        else:
            endpoint = f"{NEWS_API_URL}top-headlines"
            params = {"category": category, "apiKey": NEWS_API_KEY, "pageSize": page_size, "language": "en", "country": "us"}

        response = requests.get(endpoint, params=params, timeout=10)
        data = response.json()

        if data.get("status") == "ok":
            return [a for a in data.get("articles", []) if a.get("title") and a.get("title") != "[Removed]"]
        else:
            return get_fallback_news()
    except Exception as e:
        print(f"NewsAPI error: {e}")
        return get_fallback_news()


def get_fallback_news():
    return [
        {"title": "DailyNest is Ready!", "description": "Add your NewsAPI key to see live news.", "urlToImage": "https://placehold.co/600x400/7c3aed/ffffff?text=DailyNest", "url": "#", "source": {"name": "DailyNest"}, "publishedAt": datetime.now().isoformat()},
        {"title": "Technology is Changing the World", "description": "From AI to quantum computing.", "urlToImage": "https://placehold.co/600x400/6d28d9/ffffff?text=Technology", "url": "#", "source": {"name": "Demo"}, "publishedAt": datetime.now().isoformat()},
        {"title": "Business Markets See New Highs", "description": "Global markets continue upward.", "urlToImage": "https://placehold.co/600x400/5b21b6/ffffff?text=Business", "url": "#", "source": {"name": "Demo"}, "publishedAt": datetime.now().isoformat()},
    ]


@app.context_processor
def inject_globals():
    return dict(categories=CATEGORIES)


@app.route("/")
def home():
    trending = fetch_news(category="general", page_size=9)
    tech = fetch_news(category="technology", page_size=3)
    return render_template("home.html", trending=trending, tech=tech)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm = request.form.get("confirm_password", "").strip()

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
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hash_password(password)))
            conn.commit()
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))
        except psycopg2.IntegrityError:
            conn.rollback()
            flash("Username already taken. Try another.", "danger")
        finally:
            conn.close()

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, hash_password(password)))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {username}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
    user = cursor.fetchone()
    conn.close()

    prefs = [p.strip() for p in user["preferences"].split(",") if p.strip()]
    if not prefs:
        prefs = ["general"]

    news_by_category = {}
    for cat in prefs:
        news_by_category[cat] = fetch_news(category=cat, page_size=6)

    return render_template("dashboard.html", user=user, news_by_category=news_by_category)


@app.route("/preferences", methods=["GET", "POST"])
@login_required
def preferences():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
    user = cursor.fetchone()

    if request.method == "POST":
        selected = request.form.getlist("categories")
        telegram_id = request.form.get("telegram_id", "").strip()

        if not selected:
            selected = ["general"]

        prefs_str = ",".join(selected)
        cursor2 = conn.cursor()
        cursor2.execute("UPDATE users SET preferences = %s, telegram_id = %s WHERE id = %s", (prefs_str, telegram_id, session["user_id"]))
        conn.commit()
        conn.close()

        flash("Preferences saved successfully!", "success")
        return redirect(url_for("dashboard"))

    conn.close()
    current_prefs = [p.strip() for p in user["preferences"].split(",")]
    return render_template("preferences.html", categories=CATEGORIES, current_prefs=current_prefs, user=user)


@app.route("/category/<cat>")
def category(cat):
    if cat not in CATEGORIES:
        flash("Invalid category.", "danger")
        return redirect(url_for("home"))
    articles = fetch_news(category=cat, page_size=12)
    return render_template("category.html", articles=articles, category=cat)


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    articles = []
    if query:
        articles = fetch_news(query=query, page_size=12)
    return render_template("search.html", articles=articles, query=query)


@app.route("/api/news/<category>")
def api_news(category):
    articles = fetch_news(category=category, page_size=5)
    safe = [{"title": a.get("title", ""), "description": a.get("description", ""), "url": a.get("url", ""), "source": a.get("source", {}).get("name", "")} for a in articles]
    return jsonify(safe)


if __name__ == "__main__":
    init_db()
    app.run(host='0.0.0.0', port=10000)
