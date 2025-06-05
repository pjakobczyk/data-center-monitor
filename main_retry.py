import feedparser
import time

def safe_parse(url, retries=3, wait=3):
    for attempt in range(retries):
        try:
            return feedparser.parse(url)
        except Exception as e:
            print(f"[{url}] Błąd ({attempt+1}/{retries}): {e}")
            time.sleep(wait)
    return {"entries": []}  # jeśli się nie uda, zwraca pustą listę

# W dalszej części main.py zamieniasz:
# feed = feedparser.parse(url)
# NA:
# feed = safe_parse(url)