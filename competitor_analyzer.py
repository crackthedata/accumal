import os
import requests
from bs4 import BeautifulSoup
import json
import datetime
import sqlite3
from dotenv import load_dotenv
from db import get_connection

load_dotenv()

SERPER_API_KEY = os.getenv('SERPER_API_KEY')

def get_striking_distance_keywords():
    """Fetch keywords in positions 7-15 from the last 3 days to optimize SERP API usage."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get keywords where the position is between 7 and 15, prioritize by impressions
    cursor.execute("""
    SELECT query FROM keyword_rankings 
    WHERE position BETWEEN 7 AND 15
    GROUP BY query
    ORDER BY SUM(impressions) DESC
    LIMIT 20
    """)
    keywords = [row[0] for row in cursor.fetchall()]
    conn.close()
    return keywords

def fetch_serper_results(query):
    if not SERPER_API_KEY:
        print("Error: SERPER_API_KEY is not set.")
        return []
        
    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        data = response.json()
        
        # Get top 3 organic results
        results = []
        for item in data.get('organic', [])[:3]:
            results.append({
                'url': item.get('link'),
                'title': item.get('title'),
                'position': item.get('position')
            })
        return results
    except Exception as e:
        print(f"Error fetching SERP for query '{query}': {e}")
        return []

def scrape_page_details(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script, style, header, footer, nav elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()
            
        text = soup.get_text(separator=' ')
        word_count = len(text.split())
        
        headings = {}
        for tag in ['h1', 'h2', 'h3']:
            elements = soup.find_all(tag)
            if elements:
                headings[tag] = [el.get_text(strip=True) for el in elements]
                
        return word_count, json.dumps(headings)
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None, None

def upsert_competitor_data(date_str, target_keyword, competitor_url, rank_position, title, word_count, headings_outline):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT OR REPLACE INTO competitor_analysis 
    (date, target_keyword, competitor_url, rank_position, title, word_count, headings_outline, domain_authority, referring_domains)
    VALUES (
        ?, ?, ?, ?, ?, ?, ?, 
        (SELECT domain_authority FROM competitor_analysis WHERE competitor_url = ? LIMIT 1),
        (SELECT referring_domains FROM competitor_analysis WHERE competitor_url = ? LIMIT 1)
    )
    ''', (date_str, target_keyword, competitor_url, rank_position, title, word_count, headings_outline, competitor_url, competitor_url))
    
    conn.commit()
    conn.close()

def main():
    date_str = datetime.date.today().strftime('%Y-%m-%d')
    keywords = get_striking_distance_keywords()
    
    if not keywords:
        print("No striking distance keywords found. Run GSC fetcher first or wait for rankings to populate.")
        return
        
    print(f"Analyzing {len(keywords)} striking distance keywords...")
    
    for query in keywords:
        print(f"Processing keyword: {query}")
        results = fetch_serper_results(query)
        
        for res in results:
            url = res['url']
            title = res['title']
            position = res['position']
            print(f"  -> Scraping competitor (Pos {position}): {url}")
            
            word_count, headings = scrape_page_details(url)
            if word_count is not None:
                upsert_competitor_data(date_str, query, url, position, title, word_count, headings)

if __name__ == '__main__':
    main()
