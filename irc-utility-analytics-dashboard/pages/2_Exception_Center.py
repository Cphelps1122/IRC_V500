import streamlit as st

from utils.auth import require_auth
from utils.app_state import render_page_setup
from utils.alerts import alert_counts, build_alerts
from utils.calculations import fmt_money
from utils.data_loader import load_data
from utils.theme import apply_theme, kpi_card, page_header

st.set_page_config(page_title="Exception Center", page_icon="🚨", layout="wide")
require_auth()
apply_theme()

try:
    df = load_data()
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

filters = render_page_setup(df)
fdf = filters["filtered"]
current_month = filters["current_month"]
previous_month = filters["previous_month"]

page_header("Exception Center", "Sortable anomaly queue for analyst review. No raw spreadsheet explorer is included.")
alerts = build_alerts(fdf, current_month, previous_month)
counts = alert_counts(alerts)

cols = st.columns(4)
with cols[0]:
    kpi_card("Critical", str(counts["Critical"]), "Requires review", None)
with cols[1]:
    kpi_card("Review", str(counts["Review"]), "Watch list", None)
with cols[2]:
    total_impact = alerts["Estimated Monthly Impact"].sum() if not alerts.empty else 0
    kpi_card("Est. Impact", fmt_money(total_impact), "Current flags", None)
with cols[3]:
    kpi_card("Total Flags", str(counts["Total"]), "Visible queue", None)

st.markdown('<div class="panel"><div class="panel-title">Anomaly Queue</div><div class="panel-caption">Filtered to the current month and compared with previous month. Click column headers to sort.</div>', unsafe_allow_html=True)
if alerts.empty:
    st.success("No active anomalies for the selected filters.")
else:
    level_filter = st.multiselect("Alert level", ["Critical", "Review", "Info"], default=["Critical", "Review", "Info"])
    queue = alerts[alerts["Severity"].isin(level_filter)].copy()
    display_cols = [
        "Severity", "State", "Property", "Utility", "Reason", "Current Cost", "Previous Cost", "Cost Change %",
        "Current Usage", "Usage Change %", "Current Cost/Treatment", "Cost/Treatment Change %", "Estimated Monthly Impact", "Explanation"
    ]
    st.dataframe(
        queue[display_cols],
        hide_index=True,
        use_container_width=True,
        height=620,
        column_config={
            "Current Cost": st.column_config.NumberColumn("Current Cost", format="$%.0f"),
            "Previous Cost": st.column_config.NumberColumn("Previous Cost", format="$%.0f"),
            "Cost Change %": st.column_config.NumberColumn("Cost Δ", format="%.1f%%"),
            "Current Usage": st.column_config.NumberColumn("Usage", format="%.0f"),
            "Usage Change %": st.column_config.NumberColumn("Usage Δ", format="%.1f%%"),
            "Current Cost/Treatment": st.column_config.NumberColumn("Cost/Treatment", format="$%.2f"),
            "Cost/Treatment Change %": st.column_config.NumberColumn("CPT Δ", format="%.1f%%"),
            "Estimated Monthly Impact": st.column_config.NumberColumn("Est. Impact", format="$%.0f"),
        },
    )
st.markdown('</div>', unsafe_allow_html=True)
