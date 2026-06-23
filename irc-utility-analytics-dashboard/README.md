# IRC Utility Operations Dashboard

Streamlit dashboard for utility billing analytics across dialysis centers.

This version includes:

- Live Google Sheet connection already configured
- Password-protected dashboard access
- Dark dashboard design on every page
- Light/dark toggle in the sidebar
- No raw Data Explorer page
- Read-only data access
- Operations Command Center
- Exception Center
- Property Scorecard
- Geographic View
- Monthly Summary Report with one-page PDF export

## Configured Google Sheet

The dashboard is already connected to:

```python
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1_4coHOmEkzY9cLYRtqmnUJ51LuqeY6yz/edit?gid=910919948#gid=910919948"
```

The app reads this sheet live every 30 seconds.

## Important security note

The dashboard has password protection, but the Google Sheet URL is currently stored in `config.py` because you asked for it to be inserted directly.

If your GitHub repo is public, anyone can read the URL from the code. For stronger security, make the GitHub repo private or move the sheet URL into Streamlit Cloud Secrets later.

Also, if the Google Sheet is set to "Anyone with the link can view," anyone who has that sheet link can open the sheet directly. The password protects the dashboard, not the Google Sheet itself.

## Password

The default password is set in `config.py`:

```python
APP_PASSWORD = "ChangeMeUtility2026!"
```

Change this before deploying.

Best practice on Streamlit Cloud:

1. Open your deployed app settings.
2. Go to **Secrets**.
3. Add:

```toml
APP_PASSWORD = "your-real-password-here"
```

The app will use the Streamlit secret password instead of the default in `config.py`.

## Deploy on Streamlit Cloud

1. Upload this repo to GitHub.
2. Go to Streamlit Community Cloud.
3. Create a new app.
4. Select this repo.
5. Main file path:

```text
app.py
```

6. Deploy.

## Local run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Pages

### 1. Operations Command Center

High-level monthly dashboard showing:

- Total cost this month vs previous month
- Cost per treatment this month vs previous month
- Cost per usage by utility
- Usage and treatments
- Active alerts
- Cost trend
- Utility cost breakdown

### 2. Exception Center

Analyst queue showing:

- Critical anomalies
- Review anomalies
- Estimated impact
- Cost, usage, and treatment-normalized changes
- Rule-based explanations

### 3. Property Scorecard

Property-level investigation page showing:

- Current month vs previous month metrics
- Cost per usage
- Cost per treatment
- Trend charts
- Condensed billing history
- Automatic explanations

### 4. Geographic View

State-level map and summary showing:

- Current month cost by state
- Alerts by state
- Cost per treatment by state
- Top properties by state

### 5. Monthly Summary Report

Boss-friendly monthly report page with:

- KPI summary
- Key takeaways
- Top anomalies
- Top performers
- Utility breakdown
- Recommended follow-up
- One-page PDF export button

## Alert logic

Critical:

- Cost increase greater than 20%
- Usage increase greater than 20%
- Cost per treatment increase greater than 20%
- Missing or late bill based on configured days
- Usage increased while treatment volume stayed flat

Review:

- Cost increase 10-20%
- Usage increase 10-20%
- Cost per treatment increase 10-20%
- Cost rose while usage stayed flat/decreased

Thresholds can be changed in `config.py`.

## Customization files

- `config.py` - sheet URL, password fallback, thresholds, refresh timing
- `utils/theme.py` - dark/light styling and KPI card design
- `utils/alerts.py` - anomaly logic and explanations
- `utils/reporting.py` - PDF report content
- `utils/data_loader.py` - Google Sheet connection and column normalization
