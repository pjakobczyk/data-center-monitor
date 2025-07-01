
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime
import time
import json

KEYWORDS = [
    "data center", "data centre", "datacenter", "poland", "wrocław", "warsaw",
    "frankfurt", "germany", "sweden", "finland", "denmark", "ireland", "scandinavia",
    "construction", "expansion", "build", "mech", "electrical"
]

SOURCES = [
    {"name": "Byggfakta", "url": "https://byggfakta.se"},
    {"name": "Cloudscene", "url": "https://cloudscene.com"},
    {"name": "DCM Alliance", "url": "https://dcm-alliance.de"},
    {"name": "Irish Building Magazine", "url": "https://irishbuildingmagazine.ie"},
    {"name": "TED Europa", "url": "https://ted.europa.eu"}
]

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

def scrape_site(driver, source):
    driver.get(source["url"])
    time.sleep(5)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    results = []
    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        href = a["href"]
        if not title or not href:
            continue
        if not href.startswith("http"):
            href = source["url"].rstrip("/") + "/" + href.lstrip("/")

        combined = (title + " " + href).lower()
        if any(kw in combined for kw in KEYWORDS):
            results.append({
                "source": source["name"],
                "title": title,
                "url": href,
                "scraped_at": datetime.now().isoformat()
            })
    return results

def main():
    driver = setup_driver()
    all_results = []

    for source in SOURCES:
        try:
            print(f"Scraping: {source['name']}")
            items = scrape_site(driver, source)
            all_results.extend(items)
        except Exception as e:
            all_results.append({
                "source": source["name"],
                "title": f"ERROR: {str(e)}",
                "url": source["url"],
                "scraped_at": datetime.now().isoformat()
            })

    driver.quit()

    # Save to JSON
    with open("scraped_results.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(all_results)} entries to scraped_results.json")

if __name__ == "__main__":
    main()
