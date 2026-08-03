import sqlite3
import csv
import os
from dotenv import load_dotenv
from db import get_connection

load_dotenv()

EXPORT_DIR = 'exports'

def ensure_export_dir():
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)

def export_query_to_csv(query, filename, description):
    print(f"Exporting: {description} -> {filename}")
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        headers = [description[0] for description in cursor.description]
        
        filepath = os.path.join(EXPORT_DIR, filename)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        print(f"  -> Successfully exported {len(rows)} rows.")
    except Exception as e:
        print(f"  -> Error executing query for {filename}: {e}")
    finally:
        conn.close()

def main():
    ensure_export_dir()
    
    striking_distance_query = """
    SELECT query, page, SUM(impressions) as total_impressions, AVG(position) as avg_position 
    FROM keyword_rankings 
    WHERE date >= DATE('now', '-3 days') 
      AND position BETWEEN 7 AND 15 
    GROUP BY query, page
    ORDER BY total_impressions DESC;
    """
    
    ctr_rescue_query = """
    SELECT query, page, AVG(ctr) as avg_ctr, AVG(position) as avg_position 
    FROM keyword_rankings 
    WHERE position <= 3 
    GROUP BY query, page
    HAVING avg_ctr < 0.08
    ORDER BY avg_ctr ASC;
    """
    
    cannibalization_query = """
    SELECT date, query, COUNT(DISTINCT page) as page_count
    FROM keyword_rankings
    GROUP BY date, query
    HAVING page_count > 1
    ORDER BY page_count DESC, date DESC;
    """
    
    my_da = os.getenv('MY_DOMAIN_AUTHORITY', '0')
    content_gap_query = f"""
    SELECT 
        gsc.query, 
        AVG(gsc.position) AS my_position,
        comp.competitor_url,
        comp.rank_position AS comp_position,
        my_page.word_count AS my_words,
        comp.word_count AS comp_words,
        {my_da} AS my_da,
        comp.domain_authority AS comp_da
    FROM keyword_rankings gsc
    JOIN competitor_analysis comp ON gsc.query = comp.target_keyword
    LEFT JOIN my_page_data my_page ON gsc.page = my_page.page
    WHERE gsc.date >= DATE('now', '-3 days')
      AND comp.rank_position < gsc.position
    GROUP BY gsc.query, comp.competitor_url, my_page.word_count
    ORDER BY my_position ASC;
    """
    
    export_query_to_csv(striking_distance_query, '1_striking_distance.csv', 'Striking Distance Keywords')
    export_query_to_csv(ctr_rescue_query, '2_ctr_rescue.csv', 'CTR Rescue Keywords')
    export_query_to_csv(cannibalization_query, '3_cannibalization.csv', 'Keyword Cannibalization Alert')
    export_query_to_csv(content_gap_query, '4_content_gap.csv', 'Content & Authority Gap Analysis')

if __name__ == '__main__':
    main()
