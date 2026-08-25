import os
import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
import sqlite3
import config
from db import get_connection

load_dotenv()

# Configuration
GSC_CLIENT_SECRET_FILE = os.getenv('GSC_CLIENT_SECRET_FILE', 'client_secret.json')
GSC_PROPERTY_URL = os.getenv('GSC_PROPERTY_URL')

def authenticate_gsc():
    scopes = ['https://www.googleapis.com/auth/webmasters.readonly']
    creds = None
    
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', scopes)
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(GSC_CLIENT_SECRET_FILE):
                print(f"Error: Client secret file '{GSC_CLIENT_SECRET_FILE}' not found.")
                print("Please download it from the Google Cloud Console (OAuth 2.0 Client IDs -> Desktop App).")
                return None
                
            flow = InstalledAppFlow.from_client_secrets_file(
                GSC_CLIENT_SECRET_FILE, scopes)
            creds = flow.run_local_server(port=8080, open_browser=False)
            
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return build('searchconsole', 'v1', credentials=creds)

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
        if impressions < config.MIN_IMPRESSIONS:
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
        
    # GSC data usually has a lag
    target_date = datetime.date.today() - datetime.timedelta(days=config.GSC_DATA_LAG_DAYS)
    date_str = target_date.strftime('%Y-%m-%d')
    
    rows = fetch_gsc_data(service, date_str)
    if rows:
        upsert_to_db(rows, date_str)
    else:
        print("No data found or an error occurred.")

if __name__ == '__main__':
    main()
