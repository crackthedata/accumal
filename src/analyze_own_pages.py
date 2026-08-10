import os
import requests
from bs4 import BeautifulSoup
import json
import datetime
import sqlite3
import config
from db import get_connection

def get_own_pages_to_scrape():
    """Fetch distinct pages we rank for in striking distance to analyze our own content depth."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # We'll scrape our own pages that appear in striking distance keywords
    cursor.execute(f"""
    SELECT DISTINCT page FROM keyword_rankings 
    WHERE position BETWEEN {config.STRIKING_DISTANCE_MIN_POS} AND {config.STRIKING_DISTANCE_MAX_POS}
    """)
    pages = [row[0] for row in cursor.fetchall()]
    conn.close()
    return pages

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

def upsert_own_page_data(date_str, page, word_count, headings_outline):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Using INSERT OR REPLACE allows us to update the metrics if we run the script on different days
    # It overwrites data with the same Primary Key (date, page) or inserts if it doesn't exist.
    cursor.execute('''
    INSERT OR REPLACE INTO my_page_data 
    (date, page, word_count, headings_outline)
    VALUES (?, ?, ?, ?)
    ''', (date_str, page, word_count, headings_outline))
    
    conn.commit()
    conn.close()

def main():
    date_str = datetime.date.today().strftime('%Y-%m-%d')
    pages = get_own_pages_to_scrape()
    
    if not pages:
        print("No pages found in striking distance. Make sure GSC data is populated.")
        return
        
    print(f"Analyzing {len(pages)} of your own pages...")
    
    for page in pages:
        print(f"  -> Scraping your page: {page}")
        
        word_count, headings = scrape_page_details(page)
        if word_count is not None:
            upsert_own_page_data(date_str, page, word_count, headings)

if __name__ == '__main__':
    main()
