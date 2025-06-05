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
import time

EMAIL = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASS")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Retry logic
def safe_parse(url, retries=3, wait=3):
    for attempt in range(retries):
        try:
            return feedparser.parse(url)
        except Exception as e:
            print(f"[{url}] Błąd ({attempt+1}/{retries}): {e}")
            time.sleep(wait)
    class EmptyFeed:
    entries = []

return EmptyFeed()


# Słowa kluczowe i firmy
TENDER_KEYWORDS = [
    "construction", "expansion", "building permit", "tender", "contract", "development", "investment",
    "planning", "project", "site acquisition", "civil works", "procurement", "EPC", "approved site",
    "new facility", "rfp", "rfq"
]

SERVICE_KEYWORDS = [
    "hvac", "cooling", "ventilation", "bms", "heat recovery", "vrf", "rooftop unit", "steel structure",
    "welding", "prefab", "bim", "cad", "fabrication", "mech", "commissioning", "dms", "inspection",
    "logistics", "rental", "tooling", "subcontracting", "technical support", "mep", "installation", "hac"
]

COMPANIES = [
    "skanska", "mercury", "flynn", "ttk", "winthrop", "vantage", "equinix", "aws", "meta", "google", "ntt",
    "astron", "atlas", "cemex", "cersanit", "cmt", "crown", "daldehog", "eurobox", "euroglas", "exbud",
    "ferrcon", "firetech", "glent", "grupa azoty", "hochtief", "ikea", "lafarge", "mostostal", "mtm",
    "nordec", "orlen", "pern", "pepsico", "polpharma", "porr", "rembud", "royal sub", "sanin", "starmet",
    "spec bau", "theta", "toolmex", "t-mobile", "ilv", "generiks", "fam", "marbet", "polsat",
    "nami development", "john paul construction", "gloster", "harder", "globalworth", "grudzeń las", "hutchinson"
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
    "BuildInDigital": "https://www.buildindigital.com/feed/",
    "ComputerWeekly": "https://www.computerweekly.com/rss/All-Computer-Weekly-content.xml",
    "TED": "https://ted.europa.eu/TED/rss/en/RSS_ALL.xml",
    "ITwiz": "https://itwiz.pl/feed/",
    "Data Economy": "https://data-economy.com/feed/",
    "Capacity Media": "https://www.capacitymedia.com/rss/news",
    "BNP Paribas RE": "https://www.realestate.bnpparibas.com/rss.xml",
    "Commercial Property Exec": "https://www.commercialsearch.com/news/feed/",
    "Business Wire Tech": "https://www.businesswire.com/portal/site/home/news/?vns=rss_tech-latest",
    "PR Newswire Infra": "https://www.prnewswire.com/rss/subject/infrastructure.xml",
    "InfraNews": "https://www.inframationnews.com/rss.xml",
    "Construction Index UK": "https://www.theconstructionindex.co.uk/news/rss/news",
    "Irish Construction News": "https://constructionnews.ie/feed/",
    "Zajawka": "https://zajawka.pl/feed/",
    "Eurobuild CEE": "https://eurobuildcee.com/rss/"
}

def detect_country(text):
    for country, keywords in COUNTRIES.items():
        if any(word in text for word in keywords):
            return country
    return None

def is_high_potential(text):
    text = text.lower()
    return (
        any(f in text for f in COMPANIES) and
        any(s in text for s in SERVICE_KEYWORDS) and
        any(t in text for t in TENDER_KEYWORDS)
    )
try:
    df_old = pd.read_csv("data_center_monitoring.csv")
except:
    df_old = pd.DataFrame(columns=["Data", "Kraj", "Firma", "Opis", "Link", "WARTO_ANALIZY"])

new_records = []

for source, url in FEEDS.items():
    feed = safe_parse(url)  # ZAMIANA feedparser.parse → safe_parse
    for entry in feed.entries:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        link = entry.get("link", "")
        content = f"{title} {summary}".lower()

        country = detect_country(content)
        if not country:
            continue

        if not any(k in content for k in TENDER_KEYWORDS):
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

# Wykresy
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
# Wysyłka mail i Discord
if len(df_new) > 0:
    high = df_new[df_new["WARTO_ANALIZY"] == "TAK"]
    normal = df_new[df_new["WARTO_ANALIZY"] == ""]

    # Wysyłka maila
    if EMAIL and PASSWORD:
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = EMAIL
        msg['Subject'] = "📡 Nowe Projekty Data Center"

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

    # Wysyłka Discord Webhook
    if WEBHOOK_URL:
        msg = "**🔶 WARTO ANALIZY:**\\n" if not high.empty else ""
        for _, r in high.iterrows():
            msg += f"• {r['Firma']} → {r['Link']}\\n"
        msg += "\\n**🔹 Pozostałe:**\\n" if not normal.empty else ""
        for _, r in normal.iterrows():
            msg += f"• {r['Firma']} → {r['Link']}\\n"

        requests.post(WEBHOOK_URL, json={"content": msg.strip()})

        for file in ["projekty_wg_kraju.png", "projekty_wg_miesiaca.png"]:
            if os.path.exists(file):
                with open(file, "rb") as f:
                    requests.post(WEBHOOK_URL, files={"file": (file, f)})
