import numpy as np
import pandas as pd
import streamlit as st

from utils.auth import require_auth
from utils.app_state import auto_refresh
from utils.alerts import build_alerts
from utils.calculations import fmt_money, fmt_num, monthly_trend, selected_month_summary, utility_aggregate
from utils.charts import line_chart, bar_chart
from utils.data_loader import load_data
from utils.theme import apply_theme, kpi_card, page_header, theme_toggle
from utils.auth import logout_button

st.set_page_config(page_title="Property Scorecard", page_icon="🏥", layout="wide")
require_auth()
apply_theme()

try:
    df = load_data()
except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()

auto_refresh()
st.sidebar.markdown("### IRC Utility Operations")
st.sidebar.caption("Property-level investigation")
theme_toggle()
st.sidebar.divider()
months = sorted(pd.to_datetime(df["billing_month"].dropna().unique()))
month_labels = [m.strftime("%b %Y") for m in months]
selected_label = st.sidebar.selectbox("Current month", month_labels, index=len(months)-1)
current_month = months[month_labels.index(selected_label)]
prev = current_month - pd.DateOffset(months=1)
previous_month = pd.Timestamp(prev.year, prev.month, 1)

states = ["All"] + sorted([s for s in df["state"].dropna().unique() if s and s != "Unknown"])
state = st.sidebar.selectbox("State", states)
temp = df if state == "All" else df[df["state"] == state]
properties = sorted(temp["property"].dropna().unique().tolist())
property_name = st.sidebar.selectbox("Property", properties)
prop_df = temp[temp["property"] == property_name]
utilities = ["All"] + sorted(prop_df["utility"].dropna().unique().tolist())
utility = st.sidebar.selectbox("Utility", utilities)
logout_button()

if utility != "All":
    prop_df = prop_df[prop_df["utility"] == utility]

page_header("Property Scorecard", f"{property_name} | {utility} | {current_month.strftime('%b %Y')}")
summary = selected_month_summary(prop_df, current_month, previous_month)
alerts = build_alerts(prop_df, current_month, previous_month)

cols = st.columns(5)
with cols[0]:
    kpi_card("Current Cost", fmt_money(summary["current"]["amount"]), fmt_money(summary["previous"]["amount"]), summary["delta_amount"])
with cols[1]:
    kpi_card("Cost / Treatment", fmt_money(summary["current"]["cost_per_treatment"], 2), fmt_money(summary["previous"]["cost_per_treatment"], 2), summary["delta_cpt"])
with cols[2]:
    kpi_card("Cost / Usage", fmt_money(summary["current"]["cost_per_usage"], 4), fmt_money(summary["previous"]["cost_per_usage"], 4), summary["delta_cpu"])
with cols[3]:
    kpi_card("Usage", fmt_num(summary["current"]["usage"]), fmt_num(summary["previous"]["usage"]), summary["delta_usage"])
with cols[4]:
    kpi_card("Treatments", fmt_num(summary["current"]["treatments"]), fmt_num(summary["previous"]["treatments"]), summary["delta_treatments"])

left, right = st.columns([1.45, 1])
with left:
    st.markdown('<div class="panel"><div class="panel-title">Monthly Trends</div><div class="panel-caption">Cost, usage, and treatment-normalized performance.</div>', unsafe_allow_html=True)
    trend = monthly_trend(prop_df)
    if not trend.empty:
        fig = line_chart(trend, "month_label", ["amount", "cost_per_treatment"], "Cost and Cost per Treatment", height=370)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No property trend data available.")
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel"><div class="panel-title">Automatic Explanation</div><div class="panel-caption">Rule-based notes from current vs previous month.</div>', unsafe_allow_html=True)
    if not alerts.empty:
        for _, r in alerts.head(4).iterrows():
            sev_class = "pill-danger" if r["Severity"] == "Critical" else "pill-warning"
            st.markdown(f'<span class="pill {sev_class}">{r["Severity"]}</span> <b>{r["Utility"]}</b>', unsafe_allow_html=True)
            st.markdown(f'<div class="insight-box">{r["Explanation"]}</div>', unsafe_allow_html=True)
    else:
        st.success("No active anomalies for this property and selected month.")
    st.markdown('</div>', unsafe_allow_html=True)

bottom_left, bottom_right = st.columns([1, 1])
with bottom_left:
    st.markdown('<div class="panel"><div class="panel-title">Utility Cost Mix</div><div class="panel-caption">Current month spend split by utility.</div>', unsafe_allow_html=True)
    cur = prop_df[prop_df["billing_month"] == current_month]
    mix = cur.groupby("utility", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
    if not mix.empty:
        fig = bar_chart(mix, "utility", "amount", title="Current Month Cost", height=320)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No current month utility mix available.")
    st.markdown('</div>', unsafe_allow_html=True)

with bottom_right:
    st.markdown('<div class="panel"><div class="panel-title">Billing History Summary</div><div class="panel-caption">Condensed monthly history. This is not a raw data explorer.</div>', unsafe_allow_html=True)
    hist = utility_aggregate(prop_df).sort_values("billing_month", ascending=False)
    if not hist.empty:
        table = hist[["billing_month", "utility", "amount", "usage", "treatments", "cost_per_treatment", "cost_per_usage", "days_billed"]].copy()
        table["Month"] = table["billing_month"].dt.strftime("%b %Y")
        table = table.drop(columns=["billing_month"])
        table = table[["Month", "utility", "amount", "usage", "treatments", "cost_per_treatment", "cost_per_usage", "days_billed"]]
        st.dataframe(table.head(18), hide_index=True, use_container_width=True, height=320,
            column_config={
                "amount": st.column_config.NumberColumn("Cost", format="$%.0f"),
                "usage": st.column_config.NumberColumn("Usage", format="%.0f"),
                "cost_per_treatment": st.column_config.NumberColumn("Cost/Treatment", format="$%.2f"),
                "cost_per_usage": st.column_config.NumberColumn("Cost/Usage", format="$%.4f"),
            })
    else:
        st.info("No billing history available.")
    st.markdown('</div>', unsafe_allow_html=True)
