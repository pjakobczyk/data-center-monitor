import feedparser
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import requests
import os

EMAIL = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASS")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

KEYWORDS = [
    "data center", "datacenter", "campus", "colocation", "hyperscale", "new site", "data hall",
    "project", "expansion", "construction", "tender", "contract", "EPC", "general contractor", "subcontractor",
    "planning approval", "land acquisition", "Wicklow", "Frankfurt", "Warsaw", "Wrocław", "Kraków",
    "Poznan", "Gdańsk", "Norway", "Sweden", "Finland", "Denmark", "Ireland", "Germany", "Poland",
    "Echelon", "Equinix", "Interxion", "Vantage", "Winthrop", "Mercury", "Dornan", "Flynn", "TTK",
    "MEP", "HVAC", "heat and air conditioning", "cooling system", "PUE", "power supply", "substation",
    "transformer", "renewable cooling", "renewable energy", "green data center", "PPA", "steel",
    "construction steel", "structural steel", "prefab", "modular", "rack", "fibre", "fiber optic",
    "cable tray", "CSA", "edge computing", "grid connection", "power upgrade", "HV", "LV", "power infrastructure"
]

FEEDS = {
    "TED Tenders (EU)": "https://ted.europa.eu/TED/rss/en/RSS_ALL.xml",
    "DataCenterDynamics": "https://www.datacenterdynamics.com/en/rss/",
    "DataCenterKnowledge": "https://www.datacenterknowledge.com/rss.xml",
    "BuildInDigital": "https://www.buildindigital.com/feed/",
    "ComputerWeekly": "https://www.computerweekly.com/rss/All-Computer-Weekly-content.xml",
    "The Local – Sweden": "https://www.thelocal.se/tag/data-centre/rss",
    "Energetyka24": "https://www.energetyka24.com/rss",
    "ITwiz (PL)": "https://itwiz.pl/feed/",
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
    df_old = pd.DataFrame(columns=[
        "Data pozyskania", "Kraj", "Miasto / Lokalizacja", "Firma / Projekt",
        "Typ", "Status", "Opis", "Link źródłowy"
    ])

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
                continue
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
df_combined.to_csv("data_center_monitoring.csv", index=False)

# 📊 Wykresy
if len(df_combined) > 0:
    df_combined['Data pozyskania'] = pd.to_datetime(df_combined['Data pozyskania'], errors='coerce')
    df_combined['Miesiąc'] = df_combined['Data pozyskania'].dt.to_period('M').astype(str)

    country_counts = df_combined['Kraj'].value_counts()
    plt.figure()
    country_counts.plot(kind='bar')
    plt.title("Projekty wg kraju")
    plt.ylabel("Liczba projektów")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("projekty_wg_kraju.png")

    month_counts = df_combined['Miesiąc'].value_counts().sort_index()
    plt.figure()
    month_counts.plot(kind='line', marker='o')
    plt.title("Projekty wg miesiąca")
    plt.ylabel("Liczba projektów")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("projekty_wg_miesiaca.png")

# 📧 Email
if len(df_new) > 0 and EMAIL and PASSWORD:
    msg = MIMEMultipart()
    msg['From'] = EMAIL
    msg['To'] = EMAIL
    msg['Subject'] = "📡 New Data Center Projects"

    body = "<h3>New Data Center Alerts:</h3><ul>"
    for _, row in df_new.iterrows():
        body += f"<li><a href='{row['Link źródłowy']}'>{row['Firma / Projekt']}</a> – {row['Opis'][:100]}...</li>"
    body += "</ul>"
    msg.attach(MIMEText(body, 'html'))

    for file in ["projekty_wg_kraju.png", "projekty_wg_miesiaca.png"]:
        try:
            with open(file, "rb") as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename= {file}')
                msg.attach(part)
        except Exception as e:
            print(f"Could not attach {file}: {e}")

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(EMAIL, PASSWORD)
    server.send_message(msg)
    server.quit()

# 📣 Discord
if len(df_new) > 0 and WEBHOOK_URL:
    message = "📢 New Data Center Alerts:\n"
    for _, row in df_new.iterrows():
        message += f"🔹 {row['Firma / Projekt']} → {row['Link źródłowy']}\n"
    requests.post(WEBHOOK_URL, json={"content": message})

    for file in ["projekty_wg_kraju.png", "projekty_wg_miesiaca.png"]:
        try:
            with open(file, "rb") as f:
                requests.post(WEBHOOK_URL, files={"file": (file, f)})
        except Exception as e:
            print(f"Could not send image to Discord: {e}")
