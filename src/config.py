"""
Central configuration file for all numeric thresholds used in the SEO Ranking Database pipeline.
"""

# --- Data Fetching Settings ---
# Minimum daily impressions for a keyword to be saved to the database.
MIN_IMPRESSIONS = 1

# The number of days ago to fetch GSC data for (accounts for GSC's 3-day data delay).
GSC_DATA_LAG_DAYS = 3

# --- Striking Distance Analysis Settings ---
# The highest ranking position to include in the striking distance analysis.
STRIKING_DISTANCE_MIN_POS = 2

# The lowest ranking position to include in the striking distance analysis.
STRIKING_DISTANCE_MAX_POS = 60

# The maximum number of keywords to send to the SERP API (to save credits/time).
MAX_KEYWORDS_TO_ANALYZE = 20

# --- Reporting Settings ---
# The number of days to look back in the database when generating the final CSV reports.
EXPORT_LOOKBACK_DAYS = 7

# The maximum position a keyword can rank to be considered for a CTR rescue alert.
CTR_RESCUE_MAX_POS = 3

# The CTR threshold (e.g., 0.08 = 8%) below which a top-ranking keyword is flagged for CTR rescue.
CTR_RESCUE_MIN_CTR = 0.08
