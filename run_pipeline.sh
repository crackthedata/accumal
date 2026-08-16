#!/bin/bash
# SEO Ranking Database Pipeline

source venv/bin/activate
echo "Starting SEO Ranking Database Pipeline..."

# 1. Initialize DB (creates tables if they don't exist)
echo "[1/6] Initializing database..."
python3 src/db.py

# 2. Fetch GSC Data (populates keyword_rankings)
echo "[2/7] Fetching GSC Data..."
python3 src/gsc_fetcher.py

# 3. Fetch Search Volume and KD
echo "[3/7] Fetching Volume and Keyword Difficulty..."
python3 src/volume_fetcher.py

# 4. Analyze Competitors (populates competitor_analysis from striking distance keywords)
echo "[4/7] Analyzing competitors..."
python3 src/competitor_analyzer.py

# 5. Fetch Competitor Authority (updates competitor_analysis)
echo "[5/7] Fetching domain authority..."
python3 src/authority_fetcher.py

# 6. Analyze Own Pages (populates my_page_data for the gap analysis)
echo "[6/7] Scraping own pages..."
python3 src/analyze_own_pages.py

# 7. Export Reports (generates CSVs)
echo "[7/7] Exporting reports..."
python3 src/export_reports.py

echo "Pipeline complete! Check the 'exports' folder for your reports."
