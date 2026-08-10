@echo off
REM SEO Ranking Database Pipeline

call .\venv\Scripts\activate
echo Starting SEO Ranking Database Pipeline...

REM 1. Initialize DB (creates tables if they don't exist)
echo [1/6] Initializing database...
python src/db.py

REM 2. Fetch GSC Data (populates keyword_rankings)
echo [2/6] Fetching GSC Data...
python src/gsc_fetcher.py

REM 3. Analyze Competitors (populates competitor_analysis from striking distance keywords)
echo [3/6] Analyzing competitors...
python src/competitor_analyzer.py

REM 4. Fetch Competitor Authority (updates competitor_analysis)
echo [4/6] Fetching domain authority...
python src/authority_fetcher.py

REM 5. Analyze Own Pages (populates my_page_data for the gap analysis)
echo [5/6] Scraping own pages...
python src/analyze_own_pages.py

REM 6. Export Reports (generates CSVs)
echo [6/6] Exporting reports...
python src/export_reports.py

echo Pipeline complete! Check the 'exports' folder for your reports.
pause
