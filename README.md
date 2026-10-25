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
5. An API key from [DataForSEO](https://dataforseo.com/) to fetch search volume and keyword difficulty data.

## Setup Instructions

1. **Environment Variables**: Copy `.env.example` to `.env` and fill in the values:
   - `GSC_CLIENT_SECRET_FILE`: Path to your downloaded OAuth 2.0 Client ID JSON file (e.g., `client_secret.json`).
   - `GSC_PROPERTY_URL`: Your exact website URL as registered in GSC (e.g., `https://example.com/` or `sc-domain:example.com`).
   - `SERPER_API_KEY`: Your Serper API key.
   - `OPEN_PAGERANK_API_KEY`: Your Open PageRank API key.
   - `DATAFORSEO_AUTH_BASIC`: Your DataForSEO API key encoded in Base64 (Basic Auth format).
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

## Configuration

The pipeline's numeric thresholds and analysis parameters are centralized in `src/config.py`. You can adjust these values to suit your data volume and SEO strategy:

- `MIN_IMPRESSIONS`: Minimum daily impressions for a keyword to be saved (default: `1`).
- `GSC_DATA_LAG_DAYS`: The number of days ago to fetch GSC data for, accounting for Google's data delay (default: `3`).
- `STRIKING_DISTANCE_MIN_POS`: Highest ranking position for striking distance analysis (default: `2`).
- `STRIKING_DISTANCE_MAX_POS`: Lowest ranking position for striking distance analysis (default: `60`).
- `MAX_KEYWORDS_TO_ANALYZE`: Max keywords to send to the SERP API (default: `20`).
- `EXPORT_LOOKBACK_DAYS`: Days to look back in the database for CSV exports (default: `7`).
- `CTR_RESCUE_MAX_POS`: Max position to be considered for CTR rescue (default: `3`).
- `CTR_RESCUE_MIN_CTR`: CTR threshold below which a top-ranking keyword is flagged (default: `0.08`).

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

**Via Docker:**
You can also run the pipeline as a background cron job using Docker. 
1. Build the image: `docker build -t accumal .`
2. Create the database file and exports folder on your host machine first (so Docker doesn't mistakenly create the database as a directory):
   ```bash
   touch seo_ranking.db
   mkdir -p exports
   ```
3. **Important**: Because the Docker container runs as a background cron job, you must authenticate with Google manually the **first time** to generate a `token.json` file. Run a temporary interactive container:
   ```bash
   docker run --name accumal-login --rm -it -p 8080:8080 -v $(pwd):/app accumal bash
   ```
   Inside the container, run `python src/gsc_fetcher.py`. It will print a Google authentication URL. 
   Open that URL in your local browser, log in, and you will be redirected to an error page starting with `http://localhost:8080/`. Copy that entire URL.
   Open a *second* terminal and run this command to complete the login:
   ```bash
   docker exec -it accumal-login python -c "import urllib.request; urllib.request.urlopen('PASTE_YOUR_COPIED_URL_HERE')"
   ```
   The first terminal will finish and save `token.json` to your directory. Type `exit` to close the temporary container.
4. Run the cron container with volume mounts to persist your data locally, and importantly, mount your `token.json` and `client_secret.json`:
   ```bash
   docker run -d \
     --name accumal-cron \
     -v $(pwd)/seo_ranking.db:/app/seo_ranking.db \
     -v $(pwd)/exports:/app/exports \
     -v $(pwd)/token.json:/app/token.json \
     -v $(pwd)/client_secret.json:/app/client_secret.json \
     accumal
   ```

*Note on Docker Logging*: The `Dockerfile` has been configured to properly redirect the output of all Python scripts to the container logs. If you need to troubleshoot the pipeline, you can view the complete execution logs by running:
```bash
docker logs accumal-cron
```
*(Note: The `Dockerfile` directly executes the Python scripts sequentially in the cron job rather than executing `run_pipeline.sh`. This is the preferred approach for Docker because `run_pipeline.sh` contains a `source venv/bin/activate` command that would fail in the container's global Python environment.)*

## Outputs

The pipeline will generate SQLite database records (`seo_ranking.db`) and export the following CSV reports into the `exports/` folder:
1. `1_striking_distance.csv` - Keywords ranking in positions 7-15, now including Search Volume and KD.
2. `2_ctr_rescue.csv` - Top 3 keywords with poor click-through rates.
3. `3_cannibalization.csv` - Keywords where multiple pages are competing.
4. `4_content_gap.csv` - The Ultimate Diagnostic Matrix comparing your word counts, keyword presence in H1/Title, and domain authority against competitors outranking you.
5. `5_featured_snippet_opportunities.csv` - Keywords where you rank in top 5 and a featured snippet exists.
6. `6_rank_drops_alert.csv` - Keywords that have dropped by more than 2 positions over your lookback window.
7. `7_competitor_share_of_voice.csv` - Which competitors appear most frequently in the top 3 spots across your keywords.
8. `8_zero_click_high_impression.csv` - Keywords with high impressions (>50) but 0 clicks.
9. `9_easy_wins_matrix.csv` - Keywords where your DA is higher than the competitor AND you have less word count, making them low-hanging fruit to outrank.

