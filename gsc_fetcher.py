import os
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import sqlite3
from db import get_connection

load_dotenv()

# Configuration
GSC_CREDENTIALS_FILE = os.getenv('GSC_CREDENTIALS_FILE')
GSC_PROPERTY_URL = os.getenv('GSC_PROPERTY_URL')
MIN_IMPRESSIONS = 5

def authenticate_gsc():
    if not GSC_CREDENTIALS_FILE or not os.path.exists(GSC_CREDENTIALS_FILE):
        print(f"Error: GSC credentials file '{GSC_CREDENTIALS_FILE}' not found.")
        return None
        
    credentials = service_account.Credentials.from_service_account_file(
        GSC_CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/webmasters.readonly']
    )
    return build('searchconsole', 'v1', credentials=credentials)

def fetch_gsc_data(service, date_str):
    print(f"Fetching GSC data for {GSC_PROPERTY_URL} on {date_str}...")
    request = {
        'startDate': date_str,
        'endDate': date_str,
        'dimensions': ['query', 'page'],
        'rowLimit': 25000  # Adjust as necessary
    }
    
    try:
        response = service.searchanalytics().query(
            siteUrl=GSC_PROPERTY_URL, body=request).execute()
        return response.get('rows', [])
    except Exception as e:
        print(f"Failed to fetch GSC data: {e}")
        return []

def upsert_to_db(rows, date_str):
    conn = get_connection()
    cursor = conn.cursor()
    
    count = 0
    for row in rows:
        impressions = row.get('impressions', 0)
        if impressions < MIN_IMPRESSIONS:
            continue
            
        keys = row.get('keys', [])
        if len(keys) != 2:
            continue
            
        query = keys[0]
        page = keys[1]
        clicks = row.get('clicks', 0)
        ctr = row.get('ctr', 0)
        position = row.get('position', 0)
        
        cursor.execute('''
        INSERT OR IGNORE INTO keyword_rankings 
        (date, query, page, clicks, impressions, ctr, position)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (date_str, query, page, clicks, impressions, ctr, position))
        count += 1
        
    conn.commit()
    conn.close()
    print(f"Upserted {count} rows into the database.")

def main():
    service = authenticate_gsc()
    if not service:
        return
        
    # GSC data usually has a 3 day lag
    target_date = datetime.date.today() - datetime.timedelta(days=3)
    date_str = target_date.strftime('%Y-%m-%d')
    
    rows = fetch_gsc_data(service, date_str)
    if rows:
        upsert_to_db(rows, date_str)
    else:
        print("No data found or an error occurred.")

if __name__ == '__main__':
    main()
