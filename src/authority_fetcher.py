import os
import sqlite3
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv
from db import get_connection

load_dotenv()

OPEN_PAGERANK_API_KEY = os.getenv('OPEN_PAGERANK_API_KEY')

def extract_domain(url):
    netloc = urlparse(url).netloc
    return netloc.replace('www.', '')

def get_domain_authority(domain, api_key):
    url = "https://openpagerank.keywordseverywhere.com/v1/domains/bulk"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"domains": [domain], "include_history": False}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        domain_data = data.get("response", {}).get(domain, {})
        da_score = domain_data.get("open_page_rank")
        ref_domains = domain_data.get("referring_domains")
        
        return da_score, ref_domains
    except Exception as e:
        print(f"Error fetching backlink data for {domain}: {e}")
        return None, None

def update_competitor_authority():
    if not OPEN_PAGERANK_API_KEY:
        print("Error: OPEN_PAGERANK_API_KEY is not set.")
        return
        
    conn = get_connection()
    cursor = conn.cursor()
    
    # Grab URLs we have scraped but haven't gotten authority data for yet
    cursor.execute("""
    SELECT DISTINCT competitor_url 
    FROM competitor_analysis 
    WHERE domain_authority IS NULL OR domain_authority = ''
    """)
    urls = [row[0] for row in cursor.fetchall()]
    
    if not urls:
        print("No missing authority data found.")
        conn.close()
        return
        
    print(f"Fetching authority data for {len(urls)} URLs...")
    
    for url in urls:
        domain = extract_domain(url)
        print(f"  -> Fetching DA for {domain}")
        da, ref = get_domain_authority(domain, OPEN_PAGERANK_API_KEY)
        
        if da is not None:
            cursor.execute("""
            UPDATE competitor_analysis 
            SET domain_authority = ?, referring_domains = ? 
            WHERE competitor_url = ?
            """, (da, ref, url))
            
    conn.commit()
    conn.close()

if __name__ == '__main__':
    update_competitor_authority()
