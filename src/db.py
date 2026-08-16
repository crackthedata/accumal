import sqlite3
import os

DB_PATH = 'seo_ranking.db'

def get_connection():
    return sqlite3.connect(DB_PATH)

def add_column_if_not_exists(cursor, table, column, data_type):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [info[1] for info in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {data_type}")

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
    add_column_if_not_exists(cursor, 'keyword_rankings', 'search_volume', 'INTEGER')
    add_column_if_not_exists(cursor, 'keyword_rankings', 'keyword_difficulty', 'REAL')
    
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
    add_column_if_not_exists(cursor, 'competitor_analysis', 'title_has_keyword', 'BOOLEAN')
    add_column_if_not_exists(cursor, 'competitor_analysis', 'h1_has_keyword', 'BOOLEAN')
    add_column_if_not_exists(cursor, 'competitor_analysis', 'image_count', 'INTEGER')
    
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
    add_column_if_not_exists(cursor, 'my_page_data', 'title_has_keyword', 'BOOLEAN')
    add_column_if_not_exists(cursor, 'my_page_data', 'h1_has_keyword', 'BOOLEAN')
    add_column_if_not_exists(cursor, 'my_page_data', 'image_count', 'INTEGER')

    # Keyword SERP Features Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS keyword_serp_features (
        date TEXT,
        query TEXT,
        featured_snippet_url TEXT,
        has_local_pack BOOLEAN,
        has_paa BOOLEAN,
        PRIMARY KEY (date, query)
    )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized/upgraded successfully.")
