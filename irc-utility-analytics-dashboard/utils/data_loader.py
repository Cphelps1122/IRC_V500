from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Optional
from urllib.parse import parse_qs, urlparse

import pandas as pd
import streamlit as st

REQUIRED_COLUMNS = [
    "Property Name", "Provider", "City", "State", "# Treatments", "Utility",
    "Billing Date", "Month", "Year", "Number Days Billed", "Usage", "$ Amount"
]

COLUMN_ALIASES = {
    "Property": "Property Name",
    "PropertyName": "Property Name",
    "Property Name ": "Property Name",
    "Treatments": "# Treatments",
    "Treatment Count": "# Treatments",
    "Amount": "$ Amount",
    "Cost": "$ Amount",
    "Dollar Amount": "$ Amount",
    "BillingDate": "Billing Date",
    "Days Billed": "Number Days Billed",
}


def _get_config_value(name: str, default: Any = None) -> Any:
    """Read settings from Streamlit secrets, environment variables, or config.py.

    Streamlit secrets are great for hosted/private deployments, but for local
    company dashboards a plain config.py is much harder to misplace.
    """
    # 1) Streamlit secrets, if available.
    try:
        value = st.secrets.get(name, None)
        if value not in (None, "", "PASTE_YOUR_GOOGLE_SHEET_ID_HERE", "PASTE_YOUR_GOOGLE_SHEET_URL_HERE"):
            return value
    except Exception:
        pass

    # 2) Environment variable, if provided.
    try:
        import os
        value = os.getenv(name)
        if value not in (None, "", "PASTE_YOUR_GOOGLE_SHEET_ID_HERE", "PASTE_YOUR_GOOGLE_SHEET_URL_HERE"):
            return value
    except Exception:
        pass

    # 3) Root-level config.py. This is the easiest local setup.
    try:
        import config  # type: ignore
        value = getattr(config, name, None)
        if value not in (None, "", "PASTE_YOUR_GOOGLE_SHEET_ID_HERE", "PASTE_YOUR_GOOGLE_SHEET_URL_HERE"):
            return value
    except Exception:
        pass

    return default


def _secret(name: str, default: Any = None) -> Any:
    """Backward-compatible settings helper."""
    return _get_config_value(name, default)

def extract_sheet_id(url_or_id: str) -> str:
    """Accept either a full Google Sheet URL or just the spreadsheet ID."""
    if not url_or_id:
        return ""
    value = str(url_or_id).strip()
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", value)
    return match.group(1) if match else value


def extract_gid(url_or_id: str, default_gid: str = "0") -> str:
    """Read gid from a Google Sheet URL if present; otherwise use default."""
    if not url_or_id:
        return default_gid
    parsed = urlparse(str(url_or_id))
    qs = parse_qs(parsed.query)
    gid = qs.get("gid", [None])[0]
    if gid is None:
        gid_match = re.search(r"gid=([0-9]+)", str(url_or_id))
        gid = gid_match.group(1) if gid_match else default_gid
    return str(gid)


def google_sheet_to_csv_url(url_or_id: str, gid: str = "0") -> str:
    """Build a cache-busted public CSV export URL.

    This works when the Google Sheet is shared as viewable/public or published
    to the web. Private company sheets should use the service-account setup.
    """
    sheet_id = extract_sheet_id(url_or_id)
    if not sheet_id:
        return ""
    if "export?" in str(url_or_id) and "format=csv" in str(url_or_id):
        return str(url_or_id).strip()
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


def add_cache_buster(url: str) -> str:
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}_refresh={int(time.time())}"


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={k: v for k, v in COLUMN_ALIASES.items() if k in df.columns})
    return df


def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_columns(df)

    # Remove completely empty rows that often come from Google Sheets formulas or formatting.
    df = df.dropna(how="all")

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        st.warning(
            "Missing expected columns: " + ", ".join(missing) +
            ". Some dashboard sections may be limited."
        )

    for col in ["Billing Date", "Due Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in ["# Treatments", "Number Days Billed", "Usage", "$ Amount", "Previous Reading", "Current Reading"]:
        if col in df.columns:
            # Handles commas and dollar signs from Google Sheets display formatting.
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r"[$,]", "", regex=True)
                .replace({"nan": pd.NA, "None": pd.NA, "": pd.NA})
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "Billing Date" in df.columns:
        df["Bill Month"] = df["Billing Date"].dt.to_period("M").dt.to_timestamp()
    elif {"Month", "Year"}.issubset(df.columns):
        df["Bill Month"] = pd.to_datetime(df["Month"].astype(str) + " " + df["Year"].astype(str), errors="coerce")
    else:
        df["Bill Month"] = pd.NaT

    for col in ["Property Name", "Provider", "City", "State", "Utility", "Unit of Measure"]:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown").astype(str).str.strip()

    if {"$ Amount", "# Treatments"}.issubset(df.columns):
        df["Cost per Treatment"] = df["$ Amount"] / df["# Treatments"].replace({0: pd.NA})
    else:
        df["Cost per Treatment"] = pd.NA

    if {"Usage", "# Treatments"}.issubset(df.columns):
        df["Usage per Treatment"] = df["Usage"] / df["# Treatments"].replace({0: pd.NA})
    else:
        df["Usage per Treatment"] = pd.NA

    if {"$ Amount", "Number Days Billed"}.issubset(df.columns):
        df["Cost per Day"] = df["$ Amount"] / df["Number Days Billed"].replace({0: pd.NA})
    else:
        df["Cost per Day"] = pd.NA

    if {"Usage", "Number Days Billed"}.issubset(df.columns):
        df["Usage per Day"] = df["Usage"] / df["Number Days Billed"].replace({0: pd.NA})
    else:
        df["Usage per Day"] = pd.NA

    return df


@st.cache_data(show_spinner=False, ttl=60)
def load_excel(path: str | Path, sheet_name: str = "Property") -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet_name)
    return normalize_data(df)


def _service_account_info() -> Optional[dict[str, Any]]:
    """Return service account credentials from Streamlit secrets when present."""
    info = _secret("gcp_service_account", None)
    if info:
        return dict(info)

    # Alternative flat secret style for users who paste individual fields.
    client_email = _secret("GOOGLE_CLIENT_EMAIL", "")
    private_key = _secret("GOOGLE_PRIVATE_KEY", "")
    if client_email and private_key:
        return {
            "type": "service_account",
            "project_id": _secret("GOOGLE_PROJECT_ID", ""),
            "private_key_id": _secret("GOOGLE_PRIVATE_KEY_ID", ""),
            "private_key": private_key.replace("\\n", "\n"),
            "client_email": client_email,
            "client_id": _secret("GOOGLE_CLIENT_ID", ""),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": _secret("GOOGLE_CLIENT_X509_CERT_URL", ""),
        }
    return None


def load_google_sheet_service_account(sheet_id_or_url: str, worksheet_name: str = "Property") -> pd.DataFrame:
    """Load a private Google Sheet using a Google service account.

    This is the best production setup because analysts do not paste links,
    and the sheet does not need to be public.
    """
    try:
        import gspread
    except Exception as exc:
        raise RuntimeError(
            "gspread is not installed. Run: pip install gspread google-auth"
        ) from exc

    info = _service_account_info()
    if not info:
        raise RuntimeError("Service-account credentials were not found in .streamlit/secrets.toml.")

    sheet_id = extract_sheet_id(sheet_id_or_url)
    gc = gspread.service_account_from_dict(info)
    sh = gc.open_by_key(sheet_id)
    ws = sh.worksheet(worksheet_name)
    records = ws.get_all_records(empty2zero=False, head=1)
    return normalize_data(pd.DataFrame(records))


def load_google_sheet_public_csv(sheet_id_or_url: str, gid: str = "0") -> pd.DataFrame:
    """Load a public/published Google Sheet CSV without credentials."""
    csv_url = add_cache_buster(google_sheet_to_csv_url(sheet_id_or_url, gid=gid))
    if not csv_url:
        raise RuntimeError("GOOGLE_SHEET_ID or GOOGLE_SHEET_URL is missing.")
    return normalize_data(pd.read_csv(csv_url))


def load_live_google_sheet() -> pd.DataFrame:
    """Load the configured Google Sheet every time Streamlit reruns.

    No user link entry is shown in the app. Configure once using secrets:
    GOOGLE_SHEET_ID or GOOGLE_SHEET_URL, plus service-account credentials if private.
    """
    sheet_ref = _secret("GOOGLE_SHEET_ID", "") or _secret("GOOGLE_SHEET_URL", "")
    worksheet = _secret("GOOGLE_WORKSHEET", "Property")
    gid = str(_secret("GOOGLE_SHEET_GID", extract_gid(sheet_ref, "0")))

    if not sheet_ref:
        raise RuntimeError(
            "No Google Sheet is configured. Add GOOGLE_SHEET_ID or GOOGLE_SHEET_URL to .streamlit/secrets.toml."
        )

    # Prefer service account when credentials exist; otherwise use public CSV.
    if _service_account_info():
        return load_google_sheet_service_account(sheet_ref, worksheet_name=worksheet)
    return load_google_sheet_public_csv(sheet_ref, gid=gid)


def load_uploaded_file(uploaded_file) -> pd.DataFrame:
    if uploaded_file.name.lower().endswith(".csv"):
        return normalize_data(pd.read_csv(uploaded_file))
    return normalize_data(pd.read_excel(uploaded_file, sheet_name="Property"))


def load_data(source: str = "Google Sheet", uploaded_file=None) -> pd.DataFrame:
    if source == "Google Sheet":
        return load_live_google_sheet()
    if source == "Upload Excel/CSV" and uploaded_file is not None:
        return load_uploaded_file(uploaded_file)
    return load_excel(Path(__file__).resolve().parents[1] / "data" / "sample_irc_database.xlsx")
