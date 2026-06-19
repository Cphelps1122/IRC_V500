"""Application configuration.

This file is intentionally simple so the dashboard can run on Streamlit Cloud
without asking users to paste anything into the app.

IMPORTANT: If this GitHub repo is public, anyone can read values stored here.
For stronger security, move GOOGLE_SHEET_URL and APP_PASSWORD into Streamlit
Cloud Secrets later.
"""

APP_TITLE = "IRC Utility Operations"

# Live Google Sheet source already inserted from the conversation.
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1_4coHOmEkzY9cLYRtqmnUJ51LuqeY6yz/edit?gid=910919948#gid=910919948"
GOOGLE_SHEET_ID = "1_4coHOmEkzY9cLYRtqmnUJ51LuqeY6yz"
GOOGLE_SHEET_GID = "910919948"
GOOGLE_WORKSHEET = "Property"

# Auto refresh interval for live sheet updates.
AUTO_REFRESH_SECONDS = 30

# Password protection.
# Change this before deploying, or set APP_PASSWORD in Streamlit Cloud Secrets.
APP_PASSWORD = "PlumCt2212"

# Alert thresholds.
WARNING_THRESHOLD = 10.0
CRITICAL_THRESHOLD = 20.0
FLAT_CHANGE_TOLERANCE = 5.0
MISSING_BILL_DAYS = 45

# PDF report settings.
REPORT_TITLE = "Monthly Utility Summary Report"
REPORT_SUBTITLE = "Dialysis Center Utility Portfolio"
