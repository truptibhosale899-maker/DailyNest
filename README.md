# 🪺 DailyNest – Public News Aggregator Bot

> A full-stack news aggregation web app with personalised feeds, user authentication, and Telegram bot alerts.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0-green)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightblue)
![Telegram](https://img.shields.io/badge/Bot-Telegram-blue)

---

## 📂 Project Structure

```
dailynest/
│
├── app.py                  ← Main Flask application
├── database.db             ← SQLite database (auto-created on run)
├── requirements.txt        ← Python dependencies
├── README.md               ← This file
│
├── templates/
│   ├── base.html           ← Base layout (navbar, footer)
│   ├── home.html           ← Landing page with trending news
│   ├── login.html          ← Login page
│   ├── signup.html         ← Registration page
│   ├── dashboard.html      ← Personalised news dashboard
│   ├── preferences.html    ← Category & Telegram preferences
│   ├── category.html       ← Category news page
│   ├── search.html         ← Search results page
│   └── _article_card.html  ← Reusable article card partial
│
├── static/
│   └── css/
│       └── style.css       ← Purple-themed stylesheet
│
├── bot/
│   └── news_bot.py         ← Telegram bot script
│
└── models/
    └── db_models.py        ← Database helper functions
```

---

## ⚙️ Setup Instructions

### 1. Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### 2. Clone / Download the Project

```bash
cd dailynest
```

### 3. Create a Virtual Environment (Recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Where to Add API Keys

### A) NewsAPI Key

1. Go to [https://newsapi.org/register](https://newsapi.org/register) and sign up for free
2. Copy your API key
3. Open `app.py` and replace:
   ```python
   NEWS_API_KEY = "YOUR_NEWSAPI_KEY_HERE"
   ```
   With:
   ```python
   NEWS_API_KEY = "abc123youractualkey"
   ```
4. Also open `bot/news_bot.py` and replace the same placeholder there.

### B) Telegram Bot Token

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts
3. Copy the token you receive
4. Open `bot/news_bot.py` and replace:
   ```python
   TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
   ```

### C) User Telegram Chat ID

Each user can find their personal Telegram Chat ID by:
1. Messaging `@userinfobot` on Telegram → it replies with their ID
2. Logging into DailyNest website → going to **Preferences**
3. Entering the Chat ID in the Telegram ID field

---

## 🚀 How to Run the Website

```bash
python app.py
```

Then open your browser at: **http://127.0.0.1:5000**

The SQLite database (`database.db`) is created automatically on first run.

---

## 🤖 How to Run the Telegram Bot

The bot has two modes:

### Broadcast Mode (sends news to all registered users once)

```bash
cd bot
python news_bot.py
# or
python news_bot.py broadcast
```

Schedule this with **cron** (Linux/Mac) or **Task Scheduler** (Windows) to run daily.

**Example cron job (every morning at 8 AM):**
```
0 8 * * * cd /path/to/dailynest && python bot/news_bot.py >> bot/bot.log 2>&1
```

### Interactive Mode (bot stays running and responds to commands)

```bash
python bot/news_bot.py interactive
```

Bot commands:
- `/start` – Get your Telegram Chat ID
- `/news`  – Fetch your personalised news on demand
- `/help`  – Show available commands

---

## 🌐 Website Pages

| URL | Description |
|-----|-------------|
| `/` | Home – Trending news (public) |
| `/signup` | Create an account |
| `/login` | Sign in |
| `/dashboard` | Personalised news feed (login required) |
| `/preferences` | Select categories + Telegram ID (login required) |
| `/category/<name>` | Browse by category (e.g. `/category/technology`) |
| `/search?q=...` | Search articles by keyword |
| `/api/news/<category>` | JSON API endpoint |

---

## ✨ Features

- ✅ User registration & login with hashed passwords
- ✅ SQLite database for user data
- ✅ Live news from NewsAPI (7 categories)
- ✅ Personalised dashboard based on user preferences
- ✅ Category browsing
- ✅ Keyword search
- ✅ Telegram bot – broadcast & interactive modes
- ✅ Mobile-responsive purple UI

---

## 🛠️ Technologies Used

| Component | Technology |
|-----------|------------|
| Backend   | Python 3, Flask |
| Database  | SQLite3 |
| Frontend  | HTML5, CSS3 (custom purple theme) |
| News Data | NewsAPI.org |
| Bot       | python-telegram-bot v21 |

---

## 📚 BSc IT Final Year Project

**Project:** DailyNest – Public News Aggregator Bot  
**Tech Stack:** Flask · SQLite · NewsAPI · Telegram Bot  
**Year:** 2024–25

---

## 🔒 Security Notes

- Passwords are hashed with SHA-256 before storage
- Session-based authentication using Flask's secure sessions
- Secret key should be changed to a random string in production
- For production, use environment variables for all API keys:
  ```python
  import os
  NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
  ```

---

*Built with ❤️ using Flask and NewsAPI*
