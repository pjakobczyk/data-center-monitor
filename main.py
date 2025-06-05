import feedparser
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import os

EMAIL = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASS")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

KEYWORDS = [
    "data center", "datacenter", "campus", "tender", "project", "CSA",
    "Wicklow", "Frankfurt", "Warsaw", "Wrocław", "Kraków", "Poznan", "Gdańsk",
    "Norway", "Sweden", "Finland", "Denmark", "Ireland", "Germany", "Poland",
    "Echelon", "Equinix", "Interxion", "Vantage",
    "Winthrop", "Mercury", "Dornan", "Flynn", "TTK",
    "general contractor", "EPC", "MEP"
]

FEEDS = {
    "TED Tenders (EU)": "https://ted.europa.eu/TED/rss/en/RSS_ALL.xml",
    "DataCenterDynamics": "https://www.datacenterdynamics.com/en/rss/",
    "The Local – Sweden": "https://www.thelocal.se/tag/data-centre/rss",
    "Nordic DCD": "https://www.datacenterdynamics.com/en/news/?region=nordics"
}

country_keywords = {
    "Ireland": ["ireland", "dublin", "wicklow", "eirgrid"],
    "Germany": ["germany", "frankfurt", "berlin", "munich"],
    "Poland": ["poland", "warsaw", "wroclaw", "krakow", "poznan", "gdansk"],
    "Sweden": ["sweden", "stockholm"],
    "Norway": ["norway", "oslo"],
    "Finland": ["finland", "helsinki"],
    "Denmark": ["denmark", "copenhagen"]
}

def detect_country(text):
    for country, keywords in country_keywords.items():
        if any(word in text for word in keywords):
            return country
    return None

try:
    df_old = pd.read_excel("data_center_monitoring.xlsx")
except:
    df_old = pd.DataFrame(columns=["Data pozyskania", "Kraj", "Miasto / Lokalizacja", "Firma / Projekt", "Typ", "Status", "Opis", "Link źródłowy"])

new_records = []

for source, url in FEEDS.items():
    feed = feedparser.parse(url)
    for entry in feed.entries:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        link = entry.get("link", "")
        content = f"{title} {summary}".lower()

        if any(k.lower() in content for k in KEYWORDS):
            country = detect_country(content)
            if not country:
                continue  # pomiń nieobsługiwane kraje

            new_records.append({
                "Data pozyskania": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Kraj": country,
                "Miasto / Lokalizacja": "(do uzupełnienia)",
                "Firma / Projekt": title[:60],
                "Typ": "(do uzupełnienia)",
                "Status": "Nowy",
                "Opis": summary[:200],
                "Link źródłowy": link
            })

df_new = pd.DataFrame(new_records)
df_combined = pd.concat([df_old, df_new]).drop_duplicates(subset=["Link źródłowy"])
df_combined.to_excel("data_center_monitoring.xlsx", index=False)

# Email alert
if len(df_new) > 0 and EMAIL and PASSWORD:
    body = "<h3>New Data Center Alerts:</h3><ul>"
    for _, row in df_new.iterrows():
        body += f"<li><a href='{row['Link źródłowy']}'>{row['Firma / Projekt']}</a> – {row['Opis'][:100]}...</li>"
    body += "</ul>"

    msg = MIMEMultipart()
    msg['From'] = EMAIL
    msg['To'] = EMAIL
    msg['Subject'] = "📡 New Data Center Projects"
    msg.attach(MIMEText(body, 'html'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(EMAIL, PASSWORD)
    server.send_message(msg)
    server.quit()

# Webhook alert
if len(df_new) > 0 and WEBHOOK_URL:
    message = "📢 New Data Center Alerts:\n"
    for _, row in df_new.iterrows():
        message += f"🔹 {row['Firma / Projekt']} → {row['Link źródłowy']}\n"
    requests.post(WEBHOOK_URL, json={"content": message})
