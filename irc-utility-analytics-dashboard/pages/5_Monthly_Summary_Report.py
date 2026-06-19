import pandas as pd
import streamlit as st

from utils.auth import require_auth
from utils.app_state import render_page_setup
from utils.alerts import alert_counts, build_alerts
from utils.calculations import fmt_money, fmt_num, selected_month_summary, top_performers, utility_cost_per_usage_breakdown
from utils.data_loader import load_data
from utils.reporting import generate_monthly_pdf, monthly_takeaways, recommended_followups
from utils.theme import apply_theme, kpi_card, page_header

st.set_page_config(page_title="Monthly Summary Report", page_icon="📄", layout="wide")
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

month_label = current_month.strftime("%B %Y")
page_header("Monthly Summary Report", "Boss-friendly one-page overview with PDF export. No raw data export included.")

summary = selected_month_summary(fdf, current_month, previous_month)
alerts = build_alerts(fdf, current_month, previous_month)
counts = alert_counts(alerts)

cols = st.columns(5)
with cols[0]:
    kpi_card("Total Cost", fmt_money(summary["current"]["amount"]), fmt_money(summary["previous"]["amount"]), summary["delta_amount"])
with cols[1]:
    kpi_card("Cost / Treatment", fmt_money(summary["current"]["cost_per_treatment"], 2), fmt_money(summary["previous"]["cost_per_treatment"], 2), summary["delta_cpt"])
with cols[2]:
    kpi_card("Usage", fmt_num(summary["current"]["usage"]), fmt_num(summary["previous"]["usage"]), summary["delta_usage"])
with cols[3]:
    kpi_card("Treatments", fmt_num(summary["current"]["treatments"]), fmt_num(summary["previous"]["treatments"]), summary["delta_treatments"])
with cols[4]:
    kpi_card("Anomalies", str(counts["Total"]), f"{counts['Critical']} Critical", None, f"{counts['Review']} Review")

st.markdown('<div class="panel"><div class="panel-title">Export Report</div><div class="panel-caption">Downloads a clean one-page landscape PDF for emailing a monthly overview.</div>', unsafe_allow_html=True)
pdf_bytes = generate_monthly_pdf(fdf, current_month, previous_month)
st.download_button(
    "Export Monthly Report PDF",
    data=pdf_bytes,
    file_name=f"utility-summary-{current_month.strftime('%Y-%m')}.pdf",
    mime="application/pdf",
    use_container_width=True,
)
st.markdown('</div>', unsafe_allow_html=True)

left, right = st.columns([1.1, 1])
with left:
    st.markdown('<div class="panel"><div class="panel-title">Key Monthly Takeaways</div><div class="panel-caption">Automatically generated from cost, usage, treatment, and alert movement.</div>', unsafe_allow_html=True)
    for item in monthly_takeaways(fdf, current_month, previous_month, alerts):
        st.markdown(f'<div class="insight-box">{item}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel"><div class="panel-title">Recommended Follow-Up</div><div class="panel-caption">Action-focused summary for analyst or management review.</div>', unsafe_allow_html=True)
    for item in recommended_followups(alerts):
        st.markdown(f'<div class="insight-box">{item}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="panel"><div class="panel-title">Top Anomalies</div><div class="panel-caption">Highest-priority flags for the selected month.</div>', unsafe_allow_html=True)
if not alerts.empty:
    top = alerts[["Severity", "Property", "Utility", "Reason", "Estimated Monthly Impact", "Explanation"]].head(5)
    st.dataframe(top, hide_index=True, use_container_width=True,
        column_config={"Estimated Monthly Impact": st.column_config.NumberColumn("Impact", format="$%.0f")})
else:
    st.success("No active anomalies for this month.")
st.markdown('</div>', unsafe_allow_html=True)

col_a, col_b = st.columns(2)
with col_a:
    st.markdown('<div class="panel"><div class="panel-title">Top Performing Properties</div><div class="panel-caption">Lowest cost per treatment in the selected filtered view.</div>', unsafe_allow_html=True)
    performers = top_performers(fdf, current_month, previous_month, n=7)
    if not performers.empty:
        display = performers.rename(columns={"property": "Property", "state": "State", "amount": "Total Cost", "treatments": "Treatments"})
        st.dataframe(display[["Property", "State", "Cost/Treatment", "Prev Cost/Treatment", "Improvement %"]], hide_index=True, use_container_width=True,
            column_config={
                "Cost/Treatment": st.column_config.NumberColumn("Cost/Treatment", format="$%.2f"),
                "Prev Cost/Treatment": st.column_config.NumberColumn("Prev CPT", format="$%.2f"),
                "Improvement %": st.column_config.NumberColumn("Change", format="%.1f%%"),
            })
    else:
        st.info("No performer data available.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_b:
    st.markdown('<div class="panel"><div class="panel-title">Utility Breakdown</div><div class="panel-caption">Cost per usage by utility, keeping units separate.</div>', unsafe_allow_html=True)
    util = utility_cost_per_usage_breakdown(fdf, current_month, previous_month)
    if not util.empty:
        st.dataframe(util[["Utility", "This Month", "Previous Month", "% Change", "Unit", "Current Cost"]], hide_index=True, use_container_width=True,
            column_config={
                "This Month": st.column_config.NumberColumn("This Month", format="$%.4f"),
                "Previous Month": st.column_config.NumberColumn("Previous", format="$%.4f"),
                "% Change": st.column_config.NumberColumn("Change", format="%.1f%%"),
                "Current Cost": st.column_config.NumberColumn("Cost", format="$%.0f"),
            })
    else:
        st.info("No utility breakdown available.")
    st.markdown('</div>', unsafe_allow_html=True)
