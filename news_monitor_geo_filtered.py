
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
    "https://www.datacenterdynamics.com",
    "https://cloudscene.com",
    "https://www.datacentermap.com",
    "https://www.dcbyte.com",
    "https://dcm-alliance.de",
    "https://www.energate-messenger.de",
    "https://www.baunetz.de",
    "https://www.linkedin.com",
    "https://www.businesspost.ie",
    "https://irishbuildingmagazine.ie",
    "https://www.planningalerts.ie",
    "https://byggfakta.se",
    "https://www.digiinfra.com",
    "https://www.tendersnordic.com",
    "https://www.propertynews.pl",
    "https://www.propertydesign.pl",
    "https://www.rynekinfrastruktury.pl",
    "https://ted.europa.eu"
    "https://www.constructionenquirer.com",
    "https://www.datacentermap.com",
]

MANDATORY_KEYWORDS = ["data center", "data centre", "datacenter"]
REGIONS = [
    "Sweden", "Norway", "Denmark", "Finland",
    "Germany", "Frankfurt", "Berlin", "Munich",
    "Ireland", "Dublin", "Poland", "Warsaw"
]

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")

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
            if any(base in content for base in MANDATORY_KEYWORDS):
                if any(region.lower() in content for region in REGIONS):
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
    msg["Subject"] = "🚨 New Data Center News Alert (Geo Filtered)"
    msg["From"] = GMAIL_USER
    msg["To"] = EMAIL_RECIPIENT

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)

if __name__ == "__main__":
    found = check_feeds()
    if found:
        if DISCORD_WEBHOOK_URL:
            send_discord_alert(found)
        if EMAIL_RECIPIENT and GMAIL_USER and GMAIL_PASSWORD:
            send_email_alert(found)
        for match in found:
            print("🚨 MATCH FOUND 🚨")
            print("Title:", match["title"])
            print("Link:", match["link"])
            print("Published:", match["published"])
            print("-" * 60)
    else:
        print("No relevant news found.")
