import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import datetime
import pytest
from unittest.mock import patch, MagicMock

import gsc_fetcher

# --- Tests for fetch_gsc_data ---

def test_fetch_gsc_data_success():
    mock_service = MagicMock()
    mock_query = mock_service.searchanalytics.return_value.query.return_value
    mock_query.execute.return_value = {
        'rows': [
            {'keys': ['query1', 'page1'], 'impressions': 100, 'clicks': 10, 'ctr': 0.1, 'position': 5.0}
        ]
    }
    
    # We need to temporarily set the global GSC_PROPERTY_URL or mock it, 
    # but since it's already read at module level, we'll patch it in gsc_fetcher
    with patch('gsc_fetcher.GSC_PROPERTY_URL', 'https://example.com/'):
        rows = gsc_fetcher.fetch_gsc_data(mock_service, '2023-10-01')
        
    assert len(rows) == 1
    assert rows[0]['keys'][0] == 'query1'
    mock_service.searchanalytics.return_value.query.assert_called_once_with(
        siteUrl='https://example.com/',
        body={
            'startDate': '2023-10-01',
            'endDate': '2023-10-01',
            'dimensions': ['query', 'page'],
            'rowLimit': 25000
        }
    )

def test_fetch_gsc_data_exception():
    mock_service = MagicMock()
    mock_query = mock_service.searchanalytics.return_value.query.return_value
    mock_query.execute.side_effect = Exception("API Error")
    
    with patch('gsc_fetcher.GSC_PROPERTY_URL', 'https://example.com/'):
        rows = gsc_fetcher.fetch_gsc_data(mock_service, '2023-10-01')
        
    assert rows == []

# --- Tests for upsert_to_db ---

@patch('gsc_fetcher.get_connection')
def test_upsert_to_db(mock_get_connection):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn
    
    rows = [
        # Should be inserted
        {'keys': ['q1', 'p1'], 'impressions': 10, 'clicks': 1, 'ctr': 0.1, 'position': 5.5},
        # Should be skipped (impressions < 5)
        {'keys': ['q2', 'p2'], 'impressions': 3, 'clicks': 0, 'ctr': 0.0, 'position': 10.0},
        # Should be skipped (missing keys)
        {'keys': ['q3'], 'impressions': 20, 'clicks': 2, 'ctr': 0.1, 'position': 3.0}
    ]
    
    gsc_fetcher.upsert_to_db(rows, '2023-10-01')
    
    # Check that execute was called exactly once (for the first row)
    assert mock_cursor.execute.call_count == 1
    args, _ = mock_cursor.execute.call_args
    sql = args[0]
    params = args[1]
    
    assert 'INSERT OR IGNORE INTO keyword_rankings' in sql
    assert params == ('2023-10-01', 'q1', 'p1', 1, 10, 0.1, 5.5)
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()

# --- Tests for authenticate_gsc ---

@patch('gsc_fetcher.os.path.exists')
@patch('gsc_fetcher.Credentials.from_authorized_user_file')
@patch('gsc_fetcher.build')
def test_authenticate_gsc_existing_token(mock_build, mock_from_file, mock_exists):
    # Setup mock to simulate token.json exists and is valid
    mock_exists.side_effect = lambda path: path == 'token.json'
    
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_from_file.return_value = mock_creds
    
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    
    service = gsc_fetcher.authenticate_gsc()
    
    assert service == mock_service
    mock_build.assert_called_once_with('searchconsole', 'v1', credentials=mock_creds)

@patch('gsc_fetcher.os.path.exists')
@patch('gsc_fetcher.build')
def test_authenticate_gsc_no_client_secret(mock_build, mock_exists):
    # Simulate neither token.json nor client_secret.json exist
    mock_exists.return_value = False
    
    service = gsc_fetcher.authenticate_gsc()
    
    assert service is None
    mock_build.assert_not_called()
