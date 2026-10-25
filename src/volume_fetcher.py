import sqlite3
import os
import requests
import json
from dotenv import load_dotenv
from db import get_connection

load_dotenv()

DATAFORSEO_AUTH_BASIC = os.getenv('DATAFORSEO_AUTH_BASIC')

def fetch_search_volume_and_kd(queries):
    """
    Fetch search volume and Keyword Difficulty from DataForSEO.
    Returns a dictionary mapping query -> {'search_volume': int, 'keyword_difficulty': float}
    """
    if not DATAFORSEO_AUTH_BASIC:
        print("  [Error] DATAFORSEO_AUTH_BASIC not set in .env")
        return {}

    url = "https://api.dataforseo.com/v3/dataforseo_labs/google/search_volume/live"
    
    # Payload can take up to 1000 keywords, we are passing the batch in 'queries'
    payload = json.dumps([{
        "location_name": "United States",
        "language_name": "English",
        "keywords": queries
    }])
    
    headers = {
        'Authorization': f'Basic {DATAFORSEO_AUTH_BASIC}',
        'Content-Type': 'application/json'
    }
    
    results = {}
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        data = response.json()
        
        if data.get('tasks') and len(data['tasks']) > 0:
            task_result = data['tasks'][0].get('result', [])
            if task_result:
                for item in task_result:
                    keyword = item.get('keyword')
                    if keyword:
                        results[keyword] = {
                            'search_volume': item.get('search_volume') or 0,
                            'keyword_difficulty': item.get('keyword_difficulty') or 0.0
                        }
    except Exception as e:
        print(f"  [Error] Failed to fetch data from DataForSEO: {e}")
        
    return results

def main():
    print("Starting Volume & KD Fetcher...")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Find queries that don't have search volume yet
    cursor.execute("""
        SELECT DISTINCT query FROM keyword_rankings 
        WHERE search_volume IS NULL OR keyword_difficulty IS NULL
    """)
    queries = [row[0] for row in cursor.fetchall()]
    
    if not queries:
        print("All queries already have volume and KD data.")
        conn.close()
        return
        
    print(f"Found {len(queries)} queries needing volume/KD data.")
    
    # Batch the queries if you have an API limit
    batch_size = 50
    for i in range(0, len(queries), batch_size):
        batch = queries[i:i+batch_size]
        metrics = fetch_search_volume_and_kd(batch)
        
        # Update the database
        for query, data in metrics.items():
            cursor.execute("""
                UPDATE keyword_rankings 
                SET search_volume = ?, keyword_difficulty = ?
                WHERE query = ?
            """, (data['search_volume'], data['keyword_difficulty'], query))
        
        conn.commit()
        
    conn.close()
    print("Finished updating Search Volume and Keyword Difficulty.")

if __name__ == '__main__':
    main()
