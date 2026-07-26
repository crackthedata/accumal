#!/bin/bash
# SEO Ranking Database Pipeline

echo "Starting SEO Ranking Database Pipeline..."

# 1. Initialize DB (creates tables if they don't exist)
echo "[1/6] Initializing database..."
python3 db.py

# 2. Fetch GSC Data (populates keyword_rankings)
echo "[2/6] Fetching GSC Data..."
python3 gsc_fetcher.py

# 3. Analyze Competitors (populates competitor_analysis from striking distance keywords)
echo "[3/6] Analyzing competitors..."
python3 competitor_analyzer.py

# 4. Fetch Competitor Authority (updates competitor_analysis)
echo "[4/6] Fetching domain authority..."
python3 authority_fetcher.py

# 5. Analyze Own Pages (populates my_page_data for the gap analysis)
echo "[5/6] Scraping own pages..."
python3 analyze_own_pages.py

# 6. Export Reports (generates CSVs)
echo "[6/6] Exporting reports..."
python3 export_reports.py

echo "Pipeline complete! Check the 'exports' folder for your reports."
