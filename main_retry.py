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

def safe_parse(url):
    try:
        return feedparser.parse(url)
    except Exception as e:
        print(f"[{url}] Błąd: {e}")
        class EmptyFeed:
            entries = []
        return EmptyFeed()

TENDER_KEYWORDS = [
    "construction", "expansion", "building permit", "tender", "contract", "development",
    "investment", "planning", "project", "site acquisition", "civil works", "procurement",
    "EPC", "approved site", "new facility", "rfp", "rfq"
]

SERVICE_KEYWORDS = [
    "mep", "hvac", "cooling", "ventilation", "bms", "heat recovery", "vrf", "rooftop unit",
    "ductwork", "airflow", "fire protection", "commissioning", "fit-out", "structured cabling",
    "electrical installation", "electrical infrastructure", "ups", "genset", "containment",
    "electrical", "mechanical", "power", "technical room", "building envelope", "raised floor",
    "concrete frame", "steel structure", "clean room", "data center", "dc cooling",
    "prefabrication", "prefab", "pipe installation", "pipework", "steel prefabrication",
    "spawanie", "welding", "rury", "pipes", "kanały", "ducts", "izolacja", "insulation",
    "montaż", "installation", "montaz rurociągów", "pipe assembly", "metal fabrication",
    "sheet metal", "pipe supports", "structure supports", "konstrukcje stalowe", "stalowe kanały",
    "wsporniki", "podpory", "technical services", "fabrication", "warsztat", "workshop",
    "engineering support", "on-site installation", "assembly", "prefabrykacja", "trays",
    "drip trays", "drain trays", "ociekowe", "tace ociekowe", "mezzanine", "platform",
    "pomiar", "pomiary", "3d scanning", "inwentaryzacja", "cad", "projektowanie", "3d model",
    "laser scanning", "scan to bim", "3d documentation", "revit", "modelowanie"
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

new_records = []

for source, url in FEEDS.items():
    feed = safe_parse(url)
    for entry in feed.entries:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        link = entry.get("link", "")
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

if len(df_new) > 0:
    high = df_new[df_new["WARTO_ANALIZY"] == "TAK"]
    normal = df_new[df_new["WARTO_ANALIZY"] == ""]

    if EMAIL and PASSWORD:
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = EMAIL
        msg['Subject'] = "📡 Nowe Projekty Data Center – CSA/MEP"

        body = "<h3>🔶 WARTO ANALIZY:</h3><ul>"
        for _, r in high.iterrows():
            body += f"<li><a href='{r['Link']}'>{r['Firma']}</a> – {r['Opis'][:100]}...</li>"
        body += "</ul><h3>🔹 Pozostałe:</h3><ul>"
        for _, r in normal.iterrows():
            body += f"<li><a href='{r['Link']}'>{r['Firma']}</a> – {r['Opis'][:100]}...</li>"
        body += "</ul>"
        msg.attach(MIMEText(body, 'html'))

        for file in ["projekty_wg_kraju.png", "projekty_wg_miesiaca.png"]:
            if os.path.exists(file):
                with open(file, "rb") as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f'attachment; filename= {file}')
                    msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)
        server.quit()

    if WEBHOOK_URL:
        msg = "**🔶 WARTO ANALIZY:**\n" if not high.empty else ""
        for _, r in high.iterrows():
            msg += f"• {r['Firma']} → {r['Link']}\n"
        msg += "\n**🔹 Pozostałe:**\n" if not normal.empty else ""
        for _, r in normal.iterrows():
            msg += f"• {r['Firma']} → {r['Link']}\n"

        requests.post(WEBHOOK_URL, json={"content": msg.strip()})
        for file in ["projekty_wg_kraju.png", "projekty_wg_miesiaca.png"]:
            if os.path.exists(file):
                with open(file, "rb") as f:
                    requests.post(WEBHOOK_URL, files={"file": (file, f)})
