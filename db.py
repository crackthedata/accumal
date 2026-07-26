import sqlite3
import os

DB_PATH = 'seo_ranking.db'

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Keyword Rankings Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS keyword_rankings (
        date TEXT,
        query TEXT,
        page TEXT,
        clicks INTEGER,
        impressions INTEGER,
        ctr REAL,
        position REAL,
        PRIMARY KEY (date, query, page)
    )
    ''')
    
    # Competitor Analysis Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS competitor_analysis (
        date TEXT,
        target_keyword TEXT,
        competitor_url TEXT,
        rank_position INTEGER,
        title TEXT,
        word_count INTEGER,
        headings_outline TEXT,
        domain_authority REAL,
        referring_domains INTEGER,
        PRIMARY KEY (date, target_keyword, competitor_url)
    )
    ''')
    
    # My Page Data Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS my_page_data (
        date TEXT,
        page TEXT,
        word_count INTEGER,
        headings_outline TEXT,
        PRIMARY KEY (date, page)
    )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully.")
