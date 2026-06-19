import pandas as pd
import streamlit as st

from utils.auth import require_auth
from utils.app_state import render_page_setup
from utils.alerts import build_alerts
from utils.calculations import fmt_money, utility_aggregate
from utils.charts import state_choropleth, bar_chart
from utils.data_loader import load_data
from utils.theme import apply_theme, kpi_card, page_header

st.set_page_config(page_title="Geographic View", page_icon="🗺️", layout="wide")
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

page_header("Geographic View", "State-level portfolio visibility with cost, treatment-normalized performance, and active alerts.")
cur = fdf[fdf["billing_month"] == current_month]
alerts = build_alerts(fdf, current_month, previous_month)

# State summary. Treatments counted once per property/state/month.
if not cur.empty:
    cost_state = cur.groupby("state", as_index=False)["amount"].sum()
    treat_state = cur.groupby(["state", "property"], as_index=False)["treatments"].max().groupby("state", as_index=False)["treatments"].sum()
    usage_state = cur.groupby("state", as_index=False)["usage"].sum()
    state_df = cost_state.merge(treat_state, on="state", how="left").merge(usage_state, on="state", how="left")
    alert_state = alerts.groupby("State", as_index=False).size().rename(columns={"State": "state", "size": "Alerts"}) if not alerts.empty else pd.DataFrame(columns=["state", "Alerts"])
    state_df = state_df.merge(alert_state, on="state", how="left")
    state_df["Alerts"] = state_df["Alerts"].fillna(0).astype(int)
    state_df["Cost/Treatment"] = state_df["amount"] / state_df["treatments"].replace({0: pd.NA})
    state_df = state_df.rename(columns={"state": "State", "amount": "Total Cost", "treatments": "Treatments", "usage": "Usage"})
else:
    state_df = pd.DataFrame()

cols = st.columns(4)
with cols[0]:
    kpi_card("States Visible", str(state_df["State"].nunique() if not state_df.empty else 0), "Filtered view", None)
with cols[1]:
    kpi_card("Total State Cost", fmt_money(state_df["Total Cost"].sum() if not state_df.empty else 0), "Current month", None)
with cols[2]:
    kpi_card("Active Alerts", str(int(state_df["Alerts"].sum()) if not state_df.empty else 0), "Across states", None)
with cols[3]:
    highest = state_df.sort_values("Cost/Treatment", ascending=False).iloc[0]["State"] if not state_df.empty and state_df["Cost/Treatment"].notna().any() else "—"
    kpi_card("Highest CPT State", highest, "Cost/treatment", None)

left, right = st.columns([1.45, 1])
with left:
    st.markdown('<div class="panel"><div class="panel-title">US Portfolio Map</div><div class="panel-caption">Color is based on current month total utility cost for selected filters.</div>', unsafe_allow_html=True)
    if not state_df.empty:
        fig = state_choropleth(state_df, location_col="State", value_col="Total Cost", title="Current Month Cost by State")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No state data available for the selected filters.")
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="panel"><div class="panel-title">State Summary</div><div class="panel-caption">Compare cost, alerts, and cost per treatment by state.</div>', unsafe_allow_html=True)
    if not state_df.empty:
        st.dataframe(
            state_df.sort_values("Total Cost", ascending=False),
            hide_index=True,
            use_container_width=True,
            height=510,
            column_config={
                "Total Cost": st.column_config.NumberColumn("Total Cost", format="$%.0f"),
                "Cost/Treatment": st.column_config.NumberColumn("Cost/Treatment", format="$%.2f"),
                "Usage": st.column_config.NumberColumn("Usage", format="%.0f"),
                "Treatments": st.column_config.NumberColumn("Treatments", format="%.0f"),
            },
        )
    else:
        st.info("No state summary available.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="panel"><div class="panel-title">Top Properties by State</div><div class="panel-caption">Highest current month utility spend. Use filters to narrow to a state or utility.</div>', unsafe_allow_html=True)
if not cur.empty:
    prop = cur.groupby(["state", "property"], as_index=False).agg(amount=("amount", "sum"), usage=("usage", "sum"), treatments=("treatments", "max"))
    prop["Cost/Treatment"] = prop["amount"] / prop["treatments"].replace({0: pd.NA})
    prop = prop.rename(columns={"state": "State", "property": "Property", "amount": "Total Cost", "usage": "Usage", "treatments": "Treatments"})
    st.dataframe(
        prop.sort_values("Total Cost", ascending=False).head(25),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Total Cost": st.column_config.NumberColumn("Total Cost", format="$%.0f"),
            "Cost/Treatment": st.column_config.NumberColumn("Cost/Treatment", format="$%.2f"),
            "Usage": st.column_config.NumberColumn("Usage", format="%.0f"),
            "Treatments": st.column_config.NumberColumn("Treatments", format="%.0f"),
        },
    )
else:
    st.info("No property summary available.")
st.markdown('</div>', unsafe_allow_html=True)
