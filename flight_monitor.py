import os
from datetime import datetime, timezone
import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

SOURCES = {
    "DP6863": "https://ru.trip.com/flights/status-dp6863/",
    "DP6864": "https://ru.trip.com/flights/status-dp6864/",
    "ROSAVIATION": "https://t.me/s/favt_info",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.7",
}

KEYWORDS = (
    "DP6863", "DP6864", "Саратов", "Гагарин", "Шереметьево",
    "задерж", "отмен", "вылет", "прилет", "ожида", "огранич"
)


def fetch_text(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text


def compact(html, limit=1200):
    import re
    text = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.I)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if not line:
            continue
        low = line.lower()
        if any(k.lower() in low for k in KEYWORDS):
            if line not in lines:
                lines.append(line)
    if not lines:
        return "Статус не удалось выделить из страницы источника."
    return "\n".join(lines[:18])[:limit]


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": message,
        "disable_web_page_preview": True,
    }, timeout=20)
    r.raise_for_status()


def main():
    now = datetime.now(timezone.utc).astimezone().strftime("%d.%m.%Y %H:%M:%S %Z")
    chunks = [f"✈️ DP6863 / DP6864 — проверка\n{now}"]

    for name, url in SOURCES.items():
        try:
            html = fetch_text(url)
            chunks.append(f"\n{name}\n{compact(html)}")
        except Exception as exc:
            chunks.append(f"\n{name}\n⚠️ Ошибка источника: {type(exc).__name__}: {exc}")

    message = "\n".join(chunks)
    send_telegram(message[:3900])


if __name__ == "__main__":
    main()
