import json
import os
import time
import requests
import csv
from bs4 import BeautifulSoup
from collections import defaultdict
from tabulate import tabulate
import re


CACHE_FILE = "news_cache.json"
CACHE_EXPIRY = 3600
SOURCES_FILE = "sources.json"

CATEGORIES = {
    "Politics": ["election", "senate", "president", "congress", "policy"],
    "Technology": ["AI", "tech", "software", "hardware", "robot", "Python", "gadget"],
    "Sports": ["football", "soccer", "basketball", "tennis", "Olympics"],
    "Entertainment": ["movie", "music", "celebrity", "TV", "film", "show"],
    "Health": ["covid", "vaccine", "health", "hospital", "disease"],
    "War": ["conflict", "war", "military", "invasion", "attack"]
}


# Load news sources from config
def read_news_source(config_path=SOURCES_FILE):
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        print(f"Error reading sources file: {e}")
        return []


# Fetch headlines from a given URL
def fetch_news(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        headlines = [
            h.get_text(strip=True)
            for h in soup.find_all(["h2", "h3", "h4"])
            if len(h.get_text(strip=True).split()) > 3
            and not is_clickbait(h.get_text(strip=True))
        ]
        return headlines
    
    except requests.RequestException as e:
        print(f"Network error while fetching {url}: {e}")
        return []
    
    except Exception as e:
        print(f"Error parsing content from {url}: {e}")
        return []


# Cache handling
def is_cache_valid():
    if os.path.exists(CACHE_FILE):
        return time.time() - os.path.getmtime(CACHE_FILE) < CACHE_EXPIRY
    return False

def load_cache():
    with open(CACHE_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def cache_results(results):
    with open(CACHE_FILE, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=2)


# Filtering
def categorize_headline(headline, categories): # filter by categories
    headline_lower = headline.lower()
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword.lower() in headline_lower:
                return category
    return "Uncategorized"

def filter_headlines(news_data, user_input): # filter by user input
    user_input = user_input.lower().strip()
    filtered = []

    for source, headlines in news_data.items():
        for headline in headlines:
            if not user_input:
                filtered.append((source, headline))
            elif user_input in headline.lower():
                filtered.append((source, headline))
            else:
                category = categorize_headline(headline, CATEGORIES)
                if user_input in category.lower():
                    filtered.append((source, headline))

    return filtered


def is_clickbait(headline): # to check if headline is clickbait and avoid headlines like "top 5..."
    clickbait_patterns = [
        r"^\s*(top-|top|[0-9]+)\s", # starts with "top" or a number
        r"\b[0-9]{1,2}\s+(things|ways|reasons|facts|tips|besten)\b", # e.g., "5 things", "10 ways"
    ]
    headline = headline.lower()
    return any(re.search(p, headline) for p in clickbait_patterns)



# Export
def export_results(filtered, format="csv", filename="filtered_results"):
    try:
        if format == "csv":
            with open(f"{filename}.csv", "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(["Source", "Headline"])
                writer.writerows(filtered)
        elif format == "json":
            with open(f"{filename}.json", "w", encoding="utf-8") as file:
                json.dump([{"source": s, "headline": h} for s, h in filtered], file, indent=2)
        print(f"\nResults saved to {filename}.{format}\n")
    except Exception as e:
        print(f"Error saving file: {e}")


# Main
def main():
    if is_cache_valid():
        print("Loading news from cache...")
        news_data = load_cache()
    else:
        print("Fetching fresh news...")
        news_data = {}
        sources = read_news_source()
        for source in sources:
            url = source.get("url")
            name = source.get("name", url)
            headlines = fetch_news(url)
            news_data[name] = headlines
        cache_results(news_data)

    # Get user input for filtering
    user_input = input("\nEnter keyword or category to filter (press Enter to show all): ").strip()

    filtered = filter_headlines(news_data, user_input)

    if not filtered:
        print("No headlines matched your filter.")
        return

    # Display in a table
    print("\nFiltered News Headlines:\n")
    print(tabulate(filtered, headers=["Source", "Headline"], tablefmt="grid"))

    # Export
    export_format = input("\nSave results? Type 'csv' or 'json' (or press enter to skip): ").strip().lower()
    if export_format in ["csv", "json"]:
        export_results(filtered, format=export_format)

if __name__ == "__main__":
    main()
