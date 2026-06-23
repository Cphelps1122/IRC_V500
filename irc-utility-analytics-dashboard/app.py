import pandas as pd
import streamlit as st

import config
from utils.auth import require_auth
from utils.app_state import render_page_setup
from utils.alerts import alert_counts, build_alerts
from utils.calculations import (
    fmt_money,
    fmt_num,
    monthly_trend,
    selected_month_summary,
    utility_cost_per_usage_breakdown,
)
from utils.charts import bar_chart, line_chart
from utils.data_loader import load_data
from utils.theme import apply_theme, kpi_card, page_header

st.set_page_config(page_title="Operations Command Center", page_icon="⚡", layout="wide")
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
selected_utility = filters["utility"]

page_header(
    "Utility Operations Command Center",
    "Live portfolio overview with month-over-month cost, usage, treatment, and alert performance.",
)

summary = selected_month_summary(fdf, current_month, previous_month)
alerts = build_alerts(fdf, current_month, previous_month)
counts = alert_counts(alerts)

cols = st.columns(6)
with cols[0]:
    kpi_card("Total Cost", fmt_money(summary["current"]["amount"]), fmt_money(summary["previous"]["amount"]), summary["delta_amount"])
with cols[1]:
    kpi_card("Cost / Treatment", fmt_money(summary["current"]["cost_per_treatment"], 2), fmt_money(summary["previous"]["cost_per_treatment"], 2), summary["delta_cpt"])
with cols[2]:
    if selected_utility != "All":
        kpi_card("Cost / Usage", fmt_money(summary["current"]["cost_per_usage"], 4), fmt_money(summary["previous"]["cost_per_usage"], 4), summary["delta_cpu"], "Selected utility")
    else:
        kpi_card("Cost / Usage", "By Utility", "", None, "See breakdown below")
with cols[3]:
    kpi_card("Total Usage", fmt_num(summary["current"]["usage"]), fmt_num(summary["previous"]["usage"]), summary["delta_usage"])
with cols[4]:
    kpi_card("Treatments", fmt_num(summary["current"]["treatments"]), fmt_num(summary["previous"]["treatments"]), summary["delta_treatments"])
with cols[5]:
    kpi_card("Active Alerts", str(counts["Total"]), f"{counts['Critical']} Critical", None, f"{counts['Review']} Review")

st.markdown("<br>", unsafe_allow_html=True)
left, right = st.columns([1.45, 1])

with left:
    st.markdown('<div class="panel"><div class="panel-title">Portfolio Trend</div><div class="panel-caption">Monthly cost, usage, and cost per treatment for the selected filters.</div>', unsafe_allow_html=True)
    trend = monthly_trend(fdf)
    if not trend.empty:
        metric_choice = st.radio("Trend metric", ["Cost", "Usage", "Cost per Treatment"], horizontal=True, label_visibility="collapsed")
        if metric_choice == "Cost":
            fig = line_chart(trend, "month_label", "amount", "Total Cost", 380)
            fig.update_yaxes(title="Cost")
        elif metric_choice == "Usage":
            fig = line_chart(trend, "month_label", "usage", "Total Usage", 380)
            fig.update_yaxes(title="Usage")
        else:
            fig = line_chart(trend, "month_label", "cost_per_treatment", "Cost per Treatment", 380)
            fig.update_yaxes(title="Cost per Treatment")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No trend data available for the selected filters.")
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel"><div class="panel-title">Cost per Usage by Utility</div><div class="panel-caption">All-utilities view keeps units separate instead of mixing kWh, gallons, therms, and trash units.</div>', unsafe_allow_html=True)
    breakdown = utility_cost_per_usage_breakdown(fdf, current_month, previous_month)
    if not breakdown.empty:
        display = breakdown[["Utility", "This Month", "Previous Month", "% Change", "Unit"]].copy()
        st.dataframe(
            display,
            hide_index=True,
            use_container_width=True,
            column_config={
                "This Month": st.column_config.NumberColumn("This Month", format="$%.4f"),
                "Previous Month": st.column_config.NumberColumn("Previous Month", format="$%.4f"),
                "% Change": st.column_config.NumberColumn("% Change", format="%.1f%%"),
            },
        )
    else:
        st.info("No utility breakdown available.")
    st.markdown('</div>', unsafe_allow_html=True)

bottom_left, bottom_right = st.columns([1.2, 1])
with bottom_left:
    st.markdown('<div class="panel"><div class="panel-title">Top Cost Drivers</div><div class="panel-caption">Current month utility spend by utility.</div>', unsafe_allow_html=True)
    cur = fdf[fdf["billing_month"] == current_month]
    by_util = cur.groupby("utility", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
    if not by_util.empty:
        fig = bar_chart(by_util, "utility", "amount", title="Current Month Cost by Utility", height=330)
        fig.update_yaxes(title="Cost")
        fig.update_xaxes(title="Utility")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No current month utility data.")
    st.markdown('</div>', unsafe_allow_html=True)

with bottom_right:
    st.markdown('<div class="panel"><div class="panel-title">Priority Alerts</div><div class="panel-caption">Highest-impact items requiring analyst review.</div>', unsafe_allow_html=True)
    if not alerts.empty:
        priority = alerts[["Severity", "Property", "Utility", "Reason", "Estimated Monthly Impact"]].head(8)
        st.dataframe(
            priority,
            hide_index=True,
            use_container_width=True,
            column_config={"Estimated Monthly Impact": st.column_config.NumberColumn("Impact", format="$%.0f")},
        )
    else:
        st.success("No active anomalies for the selected filters.")
    st.markdown('</div>', unsafe_allow_html=True)
