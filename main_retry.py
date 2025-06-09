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
import json

EMAIL = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASS")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

SENT_ARTICLES_FILE = "sent_articles.json"

def load_sent_articles():
    if not os.path.exists(SENT_ARTICLES_FILE):
        return set()
    with open(SENT_ARTICLES_FILE, "r", encoding="utf-8") as f:
        return set(json.load(f))

def save_sent_articles(sent_links):
    with open(SENT_ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump(list(sent_links), f, indent=2)

def safe_parse(url):
    try:
        return feedparser.parse(url)
    except Exception as e:
        print(f"[{url}] Błąd: {e}")
        class EmptyFeed:
            entries = []
        return EmptyFeed()

TENDER_KEYWORDS = ["construction", "expansion", "building permit", "tender", "contract", "development", "investment", "planning", "project", "site acquisition", "civil works", "procurement", "EPC", "approved site", "new facility", "rfp", "rfq"]

SERVICE_KEYWORDS = [
    "mep", "hvac", "cooling", "ventilation", "bms", "heat recovery", "vrf", "rooftop unit", "ductwork", "airflow", "fire protection", "commissioning", "fit-out", "structured cabling",
    "electrical installation", "electrical infrastructure", "ups", "genset", "containment", "electrical", "mechanical", "power", "technical room", "building envelope", "raised floor",
    "concrete frame", "steel structure", "clean room", "data center", "dc cooling", "prefabrication", "prefab", "pipe installation", "pipework", "steel prefabrication", "spawanie",
    "welding", "rury", "pipes", "kanały", "ducts", "izolacja", "insulation", "montaż", "installation", "montaz rurociągów", "pipe assembly", "metal fabrication", "sheet metal",
    "pipe supports", "structure supports", "konstrukcje stalowe", "stalowe kanały", "wsporniki", "podpory", "technical services", "fabrication", "warsztat", "workshop",
    "engineering support", "on-site installation", "assembly", "prefabrykacja", "trays", "drip trays", "drain trays", "ociekowe", "tace ociekowe", "mezzanine", "platform",
    "pomiar", "pomiary", "3d scanning", "inwentaryzacja", "cad", "projektowanie", "3d model", "laser scanning", "scan to bim", "3d documentation", "revit", "modelowanie"
]

COUNTRIES = {
    "Poland": ["poland", "warsaw", "wroclaw", "krakow", "poznan", "gdansk", "lodz", "katowice"],
    "Germany": ["germany", "frankfurt", "berlin", "munich", "hamburg"],
    "Ireland": ["ireland", "dublin", "wicklow"],
    "Sweden": ["sweden", "stockholm"],
    "Norway": ["norway", "oslo"],
    "Finland": ["finland", "helsinki"],
    "Denmark": ["denmark", "copenhagen"]
}

FEEDS = {
    "DCD": "https://www.datacenterdynamics.com/en/rss/",
    "Data Economy": "https://data-economy.com/feed/",
    "Capacity Media": "https://www.capacitymedia.com/rss/news",
    "Construction Index UK": "https://www.theconstructionindex.co.uk/news/rss/news",
    "Commercial Property Exec": "https://www.commercialsearch.com/news/feed/",
    "PR Newswire Infra": "https://www.prnewswire.com/rss/subject/infrastructure.xml",
    "InfraNews": "https://www.inframationnews.com/rss.xml",
    "BNP Paribas RE": "https://www.realestate.bnpparibas.com/rss.xml",
    "ITwiz": "https://itwiz.pl/feed/",
    "Irish Construction News": "https://constructionnews.ie/feed/"
}

def detect_country(text):
    for country, keywords in COUNTRIES.items():
        if any(word in text for word in keywords):
            return country
    return None

def is_high_potential(text):
    text = text.lower()
    return (
        "data center" in text and
        any(s in text for s in SERVICE_KEYWORDS) and
        any(t in text for t in TENDER_KEYWORDS)
    )

try:
    df_old = pd.read_csv("data_center_monitoring.csv")
except:
    df_old = pd.DataFrame(columns=["Data", "Kraj", "Firma", "Opis", "Link", "WARTO_ANALIZY"])

sent_links = load_sent_articles()
new_records = []

for source, url in FEEDS.items():
    feed = safe_parse(url)
    for entry in feed.entries:
        link = entry.get("link", "")
        if link in sent_links:
            continue

        title = entry.get("title", "")
        summary = entry.get("summary", "")
        content = f"{title} {summary}".lower()

        country = detect_country(content)
        if not country:
            continue

        if not (
            "data center" in content and
            any(k in content for k in TENDER_KEYWORDS) and
            any(s in content for s in SERVICE_KEYWORDS)
        ):
            continue

        warto = is_high_potential(content)
        new_records.append({
            "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Kraj": country,
            "Firma": title[:60],
            "Opis": summary[:200],
            "Link": link,
            "WARTO_ANALIZY": "TAK" if warto else ""
        })

        sent_links.add(link)

df_new = pd.DataFrame(new_records)
df_combined = pd.concat([df_old, df_new]).drop_duplicates(subset=["Link"])
df_combined.to_csv("data_center_monitoring.csv", index=False)

if len(df_combined) > 0:
    df_combined['Data'] = pd.to_datetime(df_combined['Data'], errors='coerce')
    df_combined['Miesiąc'] = df_combined['Data'].dt.to_period('M').astype(str)
    df_combined['Kraj'].value_counts().plot(kind='bar', title="Projekty wg kraju")
    plt.tight_layout()
    plt.savefig("projekty_wg_kraju.png")
    plt.clf()
    df_combined['Miesiąc'].value_counts().sort_index().plot(kind='line', marker='o', title="Projekty wg miesiąca")
    plt.tight_layout()
    plt.savefig("projekty_wg_miesiaca.png")
    plt.clf()

if "WARTO_ANALIZY" in_
