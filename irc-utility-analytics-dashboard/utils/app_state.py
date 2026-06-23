from __future__ import annotations

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

import config
from utils.auth import logout_button
from utils.calculations import filter_dimension, selected_previous_month
from utils.data_loader import available_months
from utils.theme import theme_toggle


def auto_refresh():
    seconds = int(getattr(config, "AUTO_REFRESH_SECONDS", 30))
    if seconds > 0:
        st_autorefresh(interval=seconds * 1000, key="live_sheet_refresh")


def render_sidebar(df: pd.DataFrame, title: str = "Filters") -> dict:
    st.sidebar.markdown("### IRC Utility Operations")
    st.sidebar.caption("Live Google Sheet dashboard")
    theme_toggle()
    st.sidebar.divider()
    st.sidebar.markdown(f"**{title}**")

    months = available_months(df)
    if not months:
        st.error("No billing months were found in the data.")
        st.stop()
    default_idx = len(months) - 1
    labels = [pd.to_datetime(m).strftime("%b %Y") for m in months]
    label_to_month = dict(zip(labels, months))
    selected_label = st.sidebar.selectbox("Current month", labels, index=default_idx)
    current_month = pd.to_datetime(label_to_month[selected_label])
    previous_month = selected_previous_month(df, current_month)

    states = ["All"] + sorted([s for s in df["state"].dropna().unique().tolist() if s and s != "Unknown"])
    state = st.sidebar.selectbox("State", states)

    temp = df if state == "All" else df[df["state"] == state]
    properties = ["All"] + sorted(temp["property"].dropna().unique().tolist())
    property_name = st.sidebar.selectbox("Property", properties)

    temp2 = temp if property_name == "All" else temp[temp["property"] == property_name]
    utilities = ["All"] + sorted(temp2["utility"].dropna().unique().tolist())
    utility = st.sidebar.selectbox("Utility", utilities)

    st.sidebar.divider()
    st.sidebar.caption(f"Current: {current_month.strftime('%b %Y')}")
    st.sidebar.caption(f"Previous: {previous_month.strftime('%b %Y') if previous_month is not None else 'None found'}")
    st.sidebar.caption(f"Auto-refresh: every {getattr(config, 'AUTO_REFRESH_SECONDS', 30)} seconds")
    logout_button()

    filtered = filter_dimension(df, state=state, property_name=property_name, utility=utility)
    return {
        "current_month": current_month,
        "previous_month": previous_month,
        "state": state,
        "property": property_name,
        "utility": utility,
        "filtered": filtered,
    }


def render_page_setup(df: pd.DataFrame) -> dict:
    auto_refresh()
    return render_sidebar(df)
