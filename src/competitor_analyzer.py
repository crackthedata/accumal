import os
import requests
from bs4 import BeautifulSoup
import json
import datetime
import sqlite3
from dotenv import load_dotenv
import config
from db import get_connection

load_dotenv()

SERPER_API_KEY = os.getenv('SERPER_API_KEY')

def get_striking_distance_keywords():
    """Fetch keywords in positions 7-15 from the last 3 days to optimize SERP API usage."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get keywords within striking distance, prioritize by impressions
    cursor.execute(f"""
    SELECT query FROM keyword_rankings 
    WHERE position BETWEEN {config.STRIKING_DISTANCE_MIN_POS} AND {config.STRIKING_DISTANCE_MAX_POS}
    GROUP BY query
    ORDER BY SUM(impressions) DESC
    LIMIT {config.MAX_KEYWORDS_TO_ANALYZE}
    """)
    keywords = [row[0] for row in cursor.fetchall()]
    conn.close()
    return keywords

def fetch_serper_results(query):
    if not SERPER_API_KEY:
        print("Error: SERPER_API_KEY is not set.")
        return [], {}
        
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
        
        # Parse SERP Features
        has_featured_snippet = bool(data.get('answerBox'))
        featured_snippet_url = data.get('answerBox', {}).get('link') if has_featured_snippet else None
        has_local_pack = bool(data.get('places'))
        has_paa = bool(data.get('peopleAlsoAsk'))
        
        serp_features = {
            'featured_snippet_url': featured_snippet_url,
            'has_local_pack': has_local_pack,
            'has_paa': has_paa
        }
        
        # Get top 3 organic results
        results = []
        for item in data.get('organic', [])[:3]:
            results.append({
                'url': item.get('link'),
                'title': item.get('title'),
                'position': item.get('position')
            })
        return results, serp_features
    except Exception as e:
        print(f"Error fetching SERP for query '{query}': {e}")
        return [], {}

def upsert_serp_features(date_str, query, serp_features):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO keyword_serp_features
    (date, query, featured_snippet_url, has_local_pack, has_paa)
    VALUES (?, ?, ?, ?, ?)
    ''', (
        date_str, 
        query, 
        serp_features.get('featured_snippet_url'), 
        serp_features.get('has_local_pack'), 
        serp_features.get('has_paa')
    ))
    conn.commit()
    conn.close()

def scrape_page_details(url, target_keyword):
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
        image_count = len(soup.find_all('img'))
        
        target_kw_lower = target_keyword.lower()
        title_text = soup.title.string if soup.title and soup.title.string else ""
        title_has_keyword = target_kw_lower in title_text.lower()
        
        h1_has_keyword = False
        headings = {}
        for tag in ['h1', 'h2', 'h3']:
            elements = soup.find_all(tag)
            if elements:
                tag_texts = [el.get_text(strip=True) for el in elements]
                headings[tag] = tag_texts
                if tag == 'h1' and any(target_kw_lower in h.lower() for h in tag_texts):
                    h1_has_keyword = True
                
        return word_count, json.dumps(headings), title_has_keyword, h1_has_keyword, image_count
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None, None, False, False, 0

def upsert_competitor_data(date_str, target_keyword, competitor_url, rank_position, title, word_count, headings_outline, title_has_kw, h1_has_kw, image_count):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT OR REPLACE INTO competitor_analysis 
    (date, target_keyword, competitor_url, rank_position, title, word_count, headings_outline, title_has_keyword, h1_has_keyword, image_count, domain_authority, referring_domains)
    VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        (SELECT domain_authority FROM competitor_analysis WHERE competitor_url = ? LIMIT 1),
        (SELECT referring_domains FROM competitor_analysis WHERE competitor_url = ? LIMIT 1)
    )
    ''', (date_str, target_keyword, competitor_url, rank_position, title, word_count, headings_outline, title_has_kw, h1_has_kw, image_count, competitor_url, competitor_url))
    
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
        results, serp_features = fetch_serper_results(query)
        if serp_features:
            upsert_serp_features(date_str, query, serp_features)
        
        for res in results:
            url = res['url']
            title = res['title']
            position = res['position']
            print(f"  -> Scraping competitor (Pos {position}): {url}")
            
            word_count, headings, title_has_kw, h1_has_kw, image_count = scrape_page_details(url, query)
            if word_count is not None:
                upsert_competitor_data(date_str, query, url, position, title, word_count, headings, title_has_kw, h1_has_kw, image_count)

if __name__ == '__main__':
    main()
