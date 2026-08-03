# SEO Ranking Database (accumal)

This project builds an automated, local SEO ranking database. It pulls your ranking data from Google Search Console, analyzes your striking distance keywords, scrapes competitor structure and domain authority, and provides a customized gap analysis (comparing your pages against top competitors).

## Prerequisites

1. Python 3.7+
2. **Google Search Console API Access**: 
   - In Google Cloud Platform (GCP), enable the "Google Search Console API".
   - Go to **APIs & Services > Credentials** and configure the OAuth consent screen.
   - Create an **OAuth 2.0 Client ID** (select "Desktop app" as the application type).
   - Download the JSON file and save it locally (e.g., as `client_secret.json`).
3. A free API key from [Serper.dev](https://serper.dev/).
4. A free API key from [Open PageRank](https://www.domcop.com/openpagerank/what-is-openpagerank).

## Setup Instructions

1. **Environment Variables**: Copy `.env.example` to `.env` and fill in the values:
   - `GSC_CLIENT_SECRET_FILE`: Path to your downloaded OAuth 2.0 Client ID JSON file (e.g., `client_secret.json`).
   - `GSC_PROPERTY_URL`: Your exact website URL as registered in GSC (e.g., `https://example.com/` or `sc-domain:example.com`).
   - `SERPER_API_KEY`: Your Serper API key.
   - `OPEN_PAGERANK_API_KEY`: Your Open PageRank API key.
   - `MY_DOMAIN_AUTHORITY`: Your own website's domain authority score (e.g., `3.1`). *(Optional: Defaults to 0 if omitted, but helps complete the final gap analysis matrix).*

2. **Virtual Environment Setup (Windows)**:
   Open PowerShell or Command Prompt in the project directory and run:
   ```bash
   # Create a virtual environment
   python -m venv venv
   
   # Activate the virtual environment
   .\venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

   *For Mac/Linux, use `python3 -m venv venv` and `source venv/bin/activate`.*

## Running the Pipeline

Once your environment is set up and activated, you can run the entire data extraction and analysis pipeline.

**On Windows:**
```bash
.\run_pipeline.bat
```

**On Linux / Mac:**
```bash
chmod +x run_pipeline.sh
./run_pipeline.sh
```

## Outputs

The pipeline will generate SQLite database records (`seo_ranking.db`) and export the following CSV reports into the `exports/` folder:
1. `1_striking_distance.csv` - Keywords ranking in positions 7-15.
2. `2_ctr_rescue.csv` - Top 3 keywords with poor click-through rates.
3. `3_cannibalization.csv` - Keywords where multiple pages are competing.
4. `4_content_gap.csv` - The Ultimate Diagnostic Matrix comparing your word counts and domain authority against competitors outranking you.