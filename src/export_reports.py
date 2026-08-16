import sqlite3
import csv
import os
from dotenv import load_dotenv
import config
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
        
        if cursor.description:
            headers = [desc[0] for desc in cursor.description]
            filepath = os.path.join(EXPORT_DIR, filename)
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
            print(f"  -> Successfully exported {len(rows)} rows.")
        else:
            print("  -> No data to export (or query did not return columns).")
    except Exception as e:
        print(f"  -> Error executing query for {filename}: {e}")
    finally:
        conn.close()

def main():
    ensure_export_dir()
    
    striking_distance_query = f"""
    SELECT query, page, SUM(impressions) as total_impressions, AVG(position) as avg_position, MAX(search_volume) as search_volume, MAX(keyword_difficulty) as kd
    FROM keyword_rankings 
    WHERE date >= DATE('now', '-{config.EXPORT_LOOKBACK_DAYS} days') 
      AND position BETWEEN {config.STRIKING_DISTANCE_MIN_POS} AND {config.STRIKING_DISTANCE_MAX_POS} 
    GROUP BY query, page
    ORDER BY total_impressions DESC;
    """
    
    ctr_rescue_query = f"""
    SELECT query, page, AVG(ctr) as avg_ctr, AVG(position) as avg_position 
    FROM keyword_rankings 
    WHERE position <= {config.CTR_RESCUE_MAX_POS} 
    GROUP BY query, page
    HAVING avg_ctr < {config.CTR_RESCUE_MIN_CTR}
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
        comp.domain_authority AS comp_da,
        my_page.title_has_keyword AS my_title_opt,
        comp.title_has_keyword AS comp_title_opt,
        my_page.h1_has_keyword AS my_h1_opt,
        comp.h1_has_keyword AS comp_h1_opt
    FROM keyword_rankings gsc
    JOIN competitor_analysis comp ON gsc.query = comp.target_keyword
    LEFT JOIN my_page_data my_page ON gsc.page = my_page.page
    WHERE gsc.date >= DATE('now', '-{config.EXPORT_LOOKBACK_DAYS} days')
      AND comp.rank_position < gsc.position
    GROUP BY gsc.query, comp.competitor_url, my_page.word_count
    ORDER BY my_position ASC;
    """
    
    snippet_opportunities_query = f"""
    SELECT gsc.query, gsc.page, AVG(gsc.position) as avg_position, MAX(feat.featured_snippet_url) as snippet_url
    FROM keyword_rankings gsc
    JOIN keyword_serp_features feat ON gsc.query = feat.query
    WHERE gsc.date >= DATE('now', '-{config.EXPORT_LOOKBACK_DAYS} days')
      AND feat.featured_snippet_url IS NOT NULL
    GROUP BY gsc.query, gsc.page
    HAVING avg_position BETWEEN 2 AND 5
    ORDER BY avg_position ASC;
    """
    
    rank_drops_query = f"""
    WITH Ranked AS (
        SELECT query, page, position, date,
               ROW_NUMBER() OVER(PARTITION BY query, page ORDER BY date ASC) as rn_asc,
               ROW_NUMBER() OVER(PARTITION BY query, page ORDER BY date DESC) as rn_desc
        FROM keyword_rankings
        WHERE date >= DATE('now', '-{config.EXPORT_LOOKBACK_DAYS} days')
    )
    SELECT start.query, start.page, start.position as old_position, end.position as new_position, (end.position - start.position) as position_drop
    FROM Ranked start
    JOIN Ranked end ON start.query = end.query AND start.page = end.page
    WHERE start.rn_asc = 1 AND end.rn_desc = 1
      AND (end.position - start.position) > 2
    ORDER BY position_drop DESC;
    """
    
    share_of_voice_query = f"""
    SELECT competitor_url, COUNT(target_keyword) as keywords_in_top_3, AVG(rank_position) as avg_position
    FROM competitor_analysis
    WHERE date >= DATE('now', '-{config.EXPORT_LOOKBACK_DAYS} days')
    GROUP BY competitor_url
    ORDER BY keywords_in_top_3 DESC;
    """
    
    zero_click_query = f"""
    SELECT query, page, SUM(impressions) as total_impressions, SUM(clicks) as total_clicks, AVG(position) as avg_position
    FROM keyword_rankings
    WHERE date >= DATE('now', '-{config.EXPORT_LOOKBACK_DAYS} days')
    GROUP BY query, page
    HAVING total_impressions > 50 AND total_clicks = 0
    ORDER BY total_impressions DESC;
    """
    
    easy_wins_query = f"""
    SELECT 
        gsc.query, 
        AVG(gsc.position) AS my_position,
        comp.competitor_url,
        comp.rank_position AS comp_position,
        my_page.word_count AS my_words,
        comp.word_count AS comp_words
    FROM keyword_rankings gsc
    JOIN competitor_analysis comp ON gsc.query = comp.target_keyword
    LEFT JOIN my_page_data my_page ON gsc.page = my_page.page
    WHERE gsc.date >= DATE('now', '-{config.EXPORT_LOOKBACK_DAYS} days')
      AND comp.rank_position < gsc.position
      AND my_page.word_count < comp.word_count
      AND {my_da} > comp.domain_authority
    GROUP BY gsc.query, comp.competitor_url, my_page.word_count
    ORDER BY my_position ASC;
    """
    
    export_query_to_csv(striking_distance_query, '1_striking_distance.csv', 'Striking Distance Keywords')
    export_query_to_csv(ctr_rescue_query, '2_ctr_rescue.csv', 'CTR Rescue Keywords')
    export_query_to_csv(cannibalization_query, '3_cannibalization.csv', 'Keyword Cannibalization Alert')
    export_query_to_csv(content_gap_query, '4_content_gap.csv', 'Content & Authority Gap Analysis')
    export_query_to_csv(snippet_opportunities_query, '5_featured_snippet_opportunities.csv', 'Featured Snippet Opportunities')
    export_query_to_csv(rank_drops_query, '6_rank_drops_alert.csv', 'Rank Drops Alert')
    export_query_to_csv(share_of_voice_query, '7_competitor_share_of_voice.csv', 'Competitor Share of Voice')
    export_query_to_csv(zero_click_query, '8_zero_click_high_impression.csv', 'Zero Click High Impression')
    export_query_to_csv(easy_wins_query, '9_easy_wins_matrix.csv', 'Easy Wins Matrix')

if __name__ == '__main__':
    main()
