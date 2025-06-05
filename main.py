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

