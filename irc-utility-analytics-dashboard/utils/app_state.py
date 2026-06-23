from __future__ import annotations

from datetime import datetime

import streamlit as st

from utils.alerts import build_alerts
from utils.calculations import monthly_summary
from utils.data_loader import load_data


def _secret(name: str, default=None):
    """Read settings from Streamlit secrets, environment variables, or config.py."""
    try:
        value = st.secrets.get(name, None)
        if value not in (None, "", "PASTE_YOUR_GOOGLE_SHEET_ID_HERE", "PASTE_YOUR_GOOGLE_SHEET_URL_HERE"):
            return value
    except Exception:
        pass

    try:
        import os
        value = os.getenv(name)
        if value not in (None, "", "PASTE_YOUR_GOOGLE_SHEET_ID_HERE", "PASTE_YOUR_GOOGLE_SHEET_URL_HERE"):
            return value
    except Exception:
        pass

    try:
        import config  # type: ignore
        value = getattr(config, name, None)
        if value not in (None, "", "PASTE_YOUR_GOOGLE_SHEET_ID_HERE", "PASTE_YOUR_GOOGLE_SHEET_URL_HERE"):
            return value
    except Exception:
        pass

    return default

def _auto_refresh() -> None:
    """Refresh the app automatically so Google Sheet edits appear without clicks."""
    refresh_seconds = int(_secret("AUTO_REFRESH_SECONDS", 30) or 30)
    refresh_seconds = max(refresh_seconds, 10)
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=refresh_seconds * 1000, key="google_sheet_auto_refresh")
    except Exception:
        # The app still reads live data on every normal Streamlit rerun. This message
        # helps if requirements were not installed after patching.
        st.sidebar.caption(
            "Auto-refresh package missing. Run: pip install streamlit-autorefresh"
        )


def data_source_sidebar() -> tuple[str, object | None]:
    """Render shared controls. Google Sheet mode is automatic, not user-entered."""
    st.sidebar.markdown("# 📊 Utility Analytics")
    st.sidebar.markdown("for Dialysis Centers")
    st.sidebar.divider()

    _auto_refresh()

    source_options = ["Google Sheet", "Sample Excel", "Upload Excel/CSV"]
    default_source = _secret("DATA_SOURCE", "Google Sheet")
    default_index = source_options.index(default_source) if default_source in source_options else 0

    source = st.sidebar.selectbox("Data Source", source_options, index=default_index, key="data_source")

    uploaded_file = None
    if source == "Google Sheet":
        worksheet = _secret("GOOGLE_WORKSHEET", "Property")
        refresh_seconds = int(_secret("AUTO_REFRESH_SECONDS", 30) or 30)
        st.sidebar.success("Live Google Sheet connected")
        st.sidebar.caption(f"Worksheet: {worksheet}")
        st.sidebar.caption(f"Auto-refresh: every {refresh_seconds} seconds")
        st.sidebar.caption("Edits appear automatically after the next refresh/rerun.")
    elif source == "Upload Excel/CSV":
        uploaded_file = st.sidebar.file_uploader("Upload Property Excel/CSV", type=["xlsx", "xls", "csv"])
    else:
        st.sidebar.warning("Using sample Excel data, not the live Google Sheet.")

    st.sidebar.divider()
    st.sidebar.caption(f"Last app refresh: {datetime.now().strftime('%I:%M:%S %p')}")
    return source, uploaded_file


def load_current_data():
    """Load fresh data and store the normalized raw, monthly, and alerts dataframes."""
    source, uploaded_file = data_source_sidebar()

    try:
        df = load_data(source, uploaded_file)
    except Exception as exc:
        st.error(f"Could not load data: {exc}")
        if source == "Google Sheet":
            st.info(
                "Configure the sheet once in config.py using GOOGLE_SHEET_URL or GOOGLE_SHEET_ID. "
                "You can still use .streamlit/secrets.toml for hosted/private deployments, but config.py "
                "is the easiest local setup. Make sure you run `streamlit run app.py` from the folder "
                "that contains app.py and config.py."
            )
        st.stop()

    monthly = monthly_summary(df)
    alerts = build_alerts(monthly)
    st.session_state["raw_df"] = df
    st.session_state["monthly"] = monthly
    st.session_state["alerts"] = alerts
    return df, monthly, alerts
