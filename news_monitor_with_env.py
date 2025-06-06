
import feedparser
import datetime
import requests
import smtplib
import os
from email.mime.text import MIMEText

RSS_FEEDS = [
    "https://feeds.reuters.com/reuters/technologyNews",
    "https://www.capacitymedia.com/rss",
    "https://www.datacenterdynamics.com/en/rss/",
    "https://www.baxtel.com/news/rss",
    "https://www.infradata.com/en/news/rss/",
    "https://data-economy.com/feed/",
    "https://techmonitor.ai/feed",
    "https://www.theregister.com/data_centre/headlines.atom",
    "https://feeds.arstechnica.com/arstechnica/index",
    "https://www.techrepublic.com/rssfeeds/articles/"
]

FILTERS = [
    "data center", "colocation", "hyperscale", "AI",
    "investment", "expansion", "construction", "MEP", "CSA",
    "Sweden", "Norway", "Denmark", "Finland",
    "Germany", "Frankfurt", "Berlin", "Munich",
    "Ireland", "Dublin", "Poland", "Warsaw",
    "Vantage", "Brookfield", "Echelon", "Mercury", "Winthrop",
    "Dornan", "Green Mountain", "Interxion", "NTT", "Data4", "Equinix", "Atman"
]

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")

def check_feeds():
    matches = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.get("title", "").lower()
            summary = entry.get("summary", "").lower()
            link = entry.get("link", "")
            published = entry.get("published", str(datetime.datetime.utcnow()))
            content = f"{title} {summary}"
            if any(word.lower() in content for word in FILTERS):
                matches.append({
                    "title": entry.title,
                    "link": link,
                    "published": published
                })
    return matches

def send_discord_alert(matches):
    for match in matches:
        message = f"🚨 **{match['title']}**\n🔗 {match['link']}\n🗓 {match['published']}"
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message})

def send_email_alert(matches):
    msg_content = "\n\n".join([
        f"Title: {m['title']}\nLink: {m['link']}\nPublished: {m['published']}"
        for m in matches
    ])
    msg = MIMEText(msg_content)
    msg["Subject"] = "🚨 New Data Center News Alert"
    msg["From"] = "alerts@yourdomain.com"
    msg["To"] = EMAIL_RECIPIENT

    with smtplib.SMTP("localhost") as server:
        server.send_message(msg)

if __name__ == "__main__":
    found = check_feeds()
    if found:
        if DISCORD_WEBHOOK_URL:
            send_discord_alert(found)
        if EMAIL_RECIPIENT:
            send_email_alert(found)
        for match in found:
            print("🚨 MATCH FOUND 🚨")
            print("Title:", match["title"])
            print("Link:", match["link"])
            print("Published:", match["published"])
            print("-" * 60)
    else:
        print("No relevant news found.")
