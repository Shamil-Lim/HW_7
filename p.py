import json
import os
import time
import requests

from bs4 import BeautifulSoup

CACHE_FILE = "new_cache.json"
CACHE_EXPIRY = 3600

def read_news_source(config_path="sources.json"):
    with open(config_path, "r") as file:
        return json.load(file)
    
def fetch_news(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        headlines = [headline.get_text() for headline in soup.find_all("h2")]
        return headlines
    except Exception as e:
        print(f"Error fetching news from {url}: {e}")
        return []
    
def is_cache_valid(cache_file = CACHE_FILE):
    if os.path.exists(cache_file):
        last_modified = os.path.getmtime(cache_file)   
        if time.time() - last_modified < CACHE_EXPIRY:
            return True
    return False

def load_cache(results, cache_file=CACHE_FILE):
    with open(cache_file, "w") as file:
        json.dump(results, file)

def cache_results(results, cache_file=CACHE_FILE):
    with open(cache_file, "w") as file:
        json.dump(results, file)

def main():
    if is_cache_valid():
        print("Loading news from cache...")
        news_data = load_cache()
    else:
        print("Fetching news...")
        sources = read_news_source()
        news_data = {}
        for source in sources:
            url = source.get["url"]
            name = source.get["name", url]
            headlines = fetch_news(url)
            news_data[name] = headlines
        cache_results(news_data)
    print("News data:")
    for source, headlines in news_data.items():
        print(f"{source}:")
        for headline in headlines:
            print(f"- {headline}")

if __name__ == "__main__":
    main()  
        
  