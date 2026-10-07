import os
import json
import feedparser
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
HISTORY_FILE = "data/processed_ids.json"

# Источники: бесплатные раздачи игр и скидки для студентов
FEEDS = [
    {
        "url": "https://www.reddit.com/r/FreeGameFindings/new/.rss",
        "category": "Игры (Бесплатно)",
        "default_region": "🌍 Global",
    },
    {
        "url": "https://www.reddit.com/r/studentdeals/new/.rss",
        "category": "Студенческие скидки",
        "default_region": "🇺🇸 US / 🌍 Global",
    },
]

def load_processed_ids():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def save_processed_ids(ids):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    recent_ids = list(ids)[-1000:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(recent_ids, f, indent=2)

def detect_region(text):
    text_lower = text.lower()
    if any(k in text_lower for k in ["us only", "usa", "united states"]):
        return "🇺🇸 Только США"
    if any(k in text_lower for k in ["uk only", "united kingdom"]):
        return "🇬🇧 Только Великобритания"
    if any(k in text_lower for k in ["eu only", "europe"]):
        return "🇪🇺 Европа"
    if any(k in text_lower for k in ["ukraine", "украина", "україна"]):
        return "🇺🇦 Украина"
    return "🌍 Global / Онлайн"

def send_telegram_message(title, link, category, region):
    text = (
        f"🎓 **[{category}]**\n\n"
        f"📢 **{title}**\n\n"
        f"📍 **Регион:** {region}\n"
        f"🔗 [Перейти к акции]({link})"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    response = requests.post(url, json=payload, timeout=15)
    return response.status_code == 200

def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Ошибка: переменные окружения не заданы.")
        return

    processed_ids = load_processed_ids()
    new_processed = set(processed_ids)

    for feed_info in FEEDS:
        feed = feedparser.parse(feed_info["url"], agent="Mozilla/5.0")
        for entry in feed.entries[:5]:
            post_id = entry.get("id") or entry.get("link")
            if not post_id or post_id in processed_ids:
                continue

            title = entry.title
            link = entry.link
            region = detect_region(title + " " + entry.get("summary", ""))

            if region == "🌍 Global / Онлайн":
                region = feed_info["default_region"]

            success = send_telegram_message(
                title=title,
                link=link,
                category=feed_info["category"],
                region=region
            )
            if success:
                new_processed.add(post_id)

    save_processed_ids(new_processed)

if __name__ == "__main__":
    main()
