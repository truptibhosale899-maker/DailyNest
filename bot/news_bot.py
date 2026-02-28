"""
DailyNest – Telegram Bot (PostgreSQL Version)
"""

import os
import asyncio
import requests
import psycopg2
import psycopg2.extras
from telegram import Bot
from telegram.error import TelegramError

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8528462918:AAE3K7HfmMgW7q28DAKPN83r9P0lVjWcz7I")
NEWS_API_KEY        = os.environ.get("NEWS_API_KEY", "4d785e694a43460c8b5acbd9e538ce2e")
DATABASE_URL        = os.environ.get("DATABASE_URL", "postgresql://dailynest_user:iQYbbTddM6bBY4KfLy1tDW5296PZi5k2@dpg-d6h9ee450q8c73af3jsg-a.oregon-postgres.render.com/dailynest")
NEWS_API_URL        = "https://newsapi.org/v2/top-headlines"
ARTICLES_PER_CATEGORY = 3


def get_users_with_telegram():
    conn = psycopg2.connect(DATABASE_URL)
    conn.cursor_factory = psycopg2.extras.RealDictCursor
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT username, preferences, telegram_id FROM users WHERE telegram_id != '' AND telegram_id IS NOT NULL")
    users = cursor.fetchall()
    conn.close()
    return [dict(u) for u in users]


def fetch_top_headlines(category="general", count=3):
    try:
        params = {"category": category, "apiKey": NEWS_API_KEY, "pageSize": count, "language": "en", "country": "us"}
        response = requests.get(NEWS_API_URL, params=params, timeout=10)
        data = response.json()
        if data.get("status") == "ok":
            return [a for a in data.get("articles", []) if a.get("title") and a["title"] != "[Removed]"][:count]
        return []
    except Exception as e:
        print(f"Failed to fetch news: {e}")
        return []


def format_article(article):
    title  = article.get("title", "No title")
    source = article.get("source", {}).get("name", "Unknown")
    desc   = article.get("description", "")
    url    = article.get("url", "")
    text = f"📰 *{title}*\n"
    if desc:
        text += f"_{desc[:120]}{'…' if len(desc) > 120 else ''}_\n"
    text += f"🔗 [Read more]({url})\n"
    text += f"🏷️ Source: {source}"
    return text


async def send_news_to_user(bot, user):
    chat_id     = user["telegram_id"]
    username    = user["username"]
    preferences = [p.strip() for p in user["preferences"].split(",") if p.strip()]

    print(f"  → Sending to {username} (chat_id: {chat_id})")

    header = f"🪺 *DailyNest – Daily Digest for {username}*\nHere's your personalised news roundup!\n\n"
    try:
        await bot.send_message(chat_id=chat_id, text=header, parse_mode="Markdown")
    except TelegramError as e:
        print(f"    ✗ Could not send to {username}: {e}")
        return

    for category in preferences:
        articles = fetch_top_headlines(category=category, count=ARTICLES_PER_CATEGORY)
        if not articles:
            continue

        cat_header = f"━━━━━━━━━━━━━━━━━\n📂 *{category.upper()}*\n"
        try:
            await bot.send_message(chat_id=chat_id, text=cat_header, parse_mode="Markdown")
        except TelegramError:
            continue

        for article in articles:
            try:
                await bot.send_message(chat_id=chat_id, text=format_article(article), parse_mode="Markdown", disable_web_page_preview=False)
                await asyncio.sleep(0.5)
            except TelegramError as e:
                print(f"    ✗ Article failed: {e}")

    try:
        await bot.send_message(chat_id=chat_id, text="━━━━━━━━━━━━━━━━━\n📲 Visit DailyNest for more news!", parse_mode="Markdown")
    except TelegramError:
        pass

    print(f"    ✓ Done for {username}")


async def broadcast_news():
    print("🚀 DailyNest Bot Starting…")

    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("⚠️  Please set your TELEGRAM_BOT_TOKEN")
        return

    bot   = Bot(token=TELEGRAM_BOT_TOKEN)
    users = get_users_with_telegram()

    if not users:
        print("ℹ️  No users with Telegram IDs found.")
        return

    print(f"📋 Found {len(users)} user(s) with Telegram IDs.\n")

    for user in users:
        await send_news_to_user(bot, user)
        await asyncio.sleep(1)

    print("\n✅ Broadcast complete!")


if __name__ == "__main__":
    asyncio.run(broadcast_news())
