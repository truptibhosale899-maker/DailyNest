"""
DailyNest – Telegram Bot
────────────────────────
This bot:
  1. Fetches users from SQLite database
  2. Reads their news preferences
  3. Sends personalised news headlines to each user's Telegram chat

Run: python bot/news_bot.py

Dependencies:
  pip install python-telegram-bot requests

Replace TELEGRAM_BOT_TOKEN with your token from @BotFather on Telegram.
"""
from datetime import datetime

with open("bot_run.log", "a") as f:
    f.write(f"Bot ran at {datetime.now()}\n")
import sqlite3
import asyncio
import requests
from telegram import Bot
from telegram.error import TelegramError

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = "8528462918:AAE3K7HfmMgW7q28DAKPN83r9P0lVjWcz7I"   # ← Replace with your BotFather token
NEWS_API_KEY        = "4d785e694a43460c8b5acbd9e538ce2e"           # ← Same key as in app.py
DATABASE            = "database.db"                  # Relative path from bot/ directory
NEWS_API_URL        = "https://newsapi.org/v2/top-headlines"

# How many articles to send per category
ARTICLES_PER_CATEGORY = 3


# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────
def get_users_with_telegram():
    """
    Fetch all users who have a Telegram ID set.
    Returns a list of dicts: {username, preferences, telegram_id}
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    users = conn.execute(
        "SELECT username, preferences, telegram_id FROM users WHERE telegram_id != '' AND telegram_id IS NOT NULL"
    ).fetchall()
    conn.close()
    return [dict(u) for u in users]


# ─────────────────────────────────────────────
# NEWS FETCHING
# ─────────────────────────────────────────────
def fetch_top_headlines(category="general", count=3):
    """
    Fetch top headlines from NewsAPI for a given category.
    Returns a list of article dicts.
    """
    try:
        params = {
            "category": category,
            "apiKey":   NEWS_API_KEY,
            "pageSize": count,
            "language": "en",
            "country":  "us",
        }
        response = requests.get(NEWS_API_URL, params=params, timeout=10)
        data = response.json()

        if data.get("status") == "ok":
            return [
                a for a in data.get("articles", [])
                if a.get("title") and a["title"] != "[Removed]"
            ][:count]
        else:
            print(f"NewsAPI error: {data.get('message', 'Unknown error')}")
            return []
    except Exception as e:
        print(f"Failed to fetch news for '{category}': {e}")
        return []


def format_article(article):
    """Format a single article into a Telegram message string."""
    title  = article.get("title", "No title")
    source = article.get("source", {}).get("name", "Unknown")
    desc   = article.get("description", "")
    url    = article.get("url", "")

    text = f"📰 *{title}*\n"
    if desc:
        # Truncate description to 120 chars
        text += f"_{desc[:120]}{'…' if len(desc) > 120 else ''}_\n"
    text += f"🔗 [Read more]({url})\n"
    text += f"🏷️ Source: {source}"
    return text


# ─────────────────────────────────────────────
# SEND NEWS TO USERS
# ─────────────────────────────────────────────
async def send_news_to_user(bot: Bot, user: dict):
    """
    Send personalised news to a single user on Telegram.
    """
    chat_id     = user["telegram_id"]
    username    = user["username"]
    preferences = [p.strip() for p in user["preferences"].split(",") if p.strip()]

    print(f"  → Sending to {username} (chat_id: {chat_id}) | Categories: {preferences}")

    # Welcome header
    header = (
        f"🪺 *DailyNest – Daily Digest for {username}*\n"
        f"Here's your personalised news roundup!\n\n"
    )
    try:
        await bot.send_message(chat_id=chat_id, text=header, parse_mode="Markdown")
    except TelegramError as e:
        print(f"    ✗ Could not send header to {username}: {e}")
        return

    # Send articles for each category
    for category in preferences:
        articles = fetch_top_headlines(category=category, count=ARTICLES_PER_CATEGORY)

        if not articles:
            continue

        # Category header
        cat_header = f"━━━━━━━━━━━━━━━━━\n📂 *{category.upper()}*\n"
        try:
            await bot.send_message(chat_id=chat_id, text=cat_header, parse_mode="Markdown")
        except TelegramError as e:
            print(f"    ✗ Category header failed: {e}")
            continue

        # Individual articles
        for article in articles:
            msg = format_article(article)
            try:
                await bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown",
                                       disable_web_page_preview=False)
                await asyncio.sleep(0.5)   # Small delay to avoid Telegram rate limits
            except TelegramError as e:
                print(f"    ✗ Article send failed: {e}")

    # Footer
    footer = "━━━━━━━━━━━━━━━━━\n📲 Update your preferences at DailyNest website."
    try:
        await bot.send_message(chat_id=chat_id, text=footer, parse_mode="Markdown")
    except TelegramError as e:
        print(f"    ✗ Footer failed: {e}")

    print(f"    ✓ Done for {username}")


async def broadcast_news():
    """Main coroutine – send news to all eligible users."""
    print("🚀 DailyNest Bot Starting…")

    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("⚠️  Please set your TELEGRAM_BOT_TOKEN in bot/news_bot.py")
        return

    bot   = Bot(token=TELEGRAM_BOT_TOKEN)
    users = get_users_with_telegram()

    if not users:
        print("ℹ️  No users with Telegram IDs found in database.")
        print("   Users need to set their Telegram ID in the website preferences.")
        return

    print(f"📋 Found {len(users)} user(s) with Telegram IDs.\n")

    for user in users:
        await send_news_to_user(bot, user)
        await asyncio.sleep(1)   # Small pause between users

    print("\n✅ Broadcast complete!")


# ─────────────────────────────────────────────
# INTERACTIVE BOT MODE (optional)
# ─────────────────────────────────────────────
async def interactive_bot():
    """
    Optional: Run an interactive bot that responds to commands.
    Commands:
        /start  – Welcome message
        /news   – Send news based on stored preferences
        /help   – Show help
    """
    from telegram.ext import Application, CommandHandler

    async def start(update, context):
        chat_id = update.effective_chat.id
        await update.message.reply_text(
            f"🪺 Welcome to *DailyNest Bot*!\n\n"
            f"Your Telegram Chat ID is: `{chat_id}`\n\n"
            f"Add this ID to your preferences on the DailyNest website to receive personalised news alerts.\n\n"
            f"Use /news to get your latest headlines.",
            parse_mode="Markdown"
        )

    async def news_command(update, context):
        chat_id = str(update.effective_chat.id)
        # Find user with this telegram_id
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        user = conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (chat_id,)
        ).fetchone()
        conn.close()

        if not user:
            await update.message.reply_text(
                "⚠️ Your Telegram ID is not linked to any DailyNest account.\n"
                "Please set your Telegram ID in the website preferences.",
                parse_mode="Markdown"
            )
            return

        await update.message.reply_text("📡 Fetching your personalised news…")
        user_dict = dict(user)
        await send_news_to_user(context.bot, user_dict)

    async def help_command(update, context):
        await update.message.reply_text(
            "🪺 *DailyNest Bot Commands*\n\n"
            "/start – Get your Chat ID\n"
            "/news  – Get your personalised news\n"
            "/help  – Show this message",
            parse_mode="Markdown"
        )

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news",  news_command))
    app.add_handler(CommandHandler("help",  help_command))

    print("🤖 Interactive bot running… Press Ctrl+C to stop.")
    await app.run_polling()


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "broadcast"

    if mode == "interactive":
        # Run interactive bot: python bot/news_bot.py interactive
        asyncio.run(interactive_bot())
    else:
        # Broadcast mode (default): send news to all users
        # Run this on a schedule (cron, APScheduler, etc.)
        asyncio.run(broadcast_news())
