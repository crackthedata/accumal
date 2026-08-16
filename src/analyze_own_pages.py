import os
import requests
from bs4 import BeautifulSoup
import json
import datetime
import sqlite3
import config
from db import get_connection

def get_own_pages_to_scrape():
    """Fetch distinct pages we rank for in striking distance and their top query to analyze our own content depth."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # We get the query with the highest impressions for each page to use as the target keyword
    cursor.execute(f"""
    SELECT page, query FROM (
        SELECT page, query, SUM(impressions) as total_impressions 
        FROM keyword_rankings 
        WHERE position BETWEEN {config.STRIKING_DISTANCE_MIN_POS} AND {config.STRIKING_DISTANCE_MAX_POS}
        GROUP BY page, query
        ORDER BY total_impressions DESC
    )
    GROUP BY page
    """)
    pages_with_queries = cursor.fetchall()
    conn.close()
    return pages_with_queries

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

def upsert_own_page_data(date_str, page, word_count, headings_outline, title_has_kw, h1_has_kw, image_count):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Using INSERT OR REPLACE allows us to update the metrics if we run the script on different days
    # It overwrites data with the same Primary Key (date, page) or inserts if it doesn't exist.
    cursor.execute('''
    INSERT OR REPLACE INTO my_page_data 
    (date, page, word_count, headings_outline, title_has_keyword, h1_has_keyword, image_count)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (date_str, page, word_count, headings_outline, title_has_kw, h1_has_kw, image_count))
    
    conn.commit()
    conn.close()

def main():
    date_str = datetime.date.today().strftime('%Y-%m-%d')
    pages_with_queries = get_own_pages_to_scrape()
    
    if not pages_with_queries:
        print("No pages found in striking distance. Make sure GSC data is populated.")
        return
        
    print(f"Analyzing {len(pages_with_queries)} of your own pages...")
    
    for page, target_query in pages_with_queries:
        print(f"  -> Scraping your page: {page} (Target Query: {target_query})")
        
        word_count, headings, title_has_kw, h1_has_kw, image_count = scrape_page_details(page, target_query)
        if word_count is not None:
            upsert_own_page_data(date_str, page, word_count, headings, title_has_kw, h1_has_kw, image_count)

if __name__ == '__main__':
    main()
