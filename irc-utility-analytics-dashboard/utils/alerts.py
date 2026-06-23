from __future__ import annotations
import numpy as np
import pandas as pd

CRITICAL = 0.20
REVIEW = 0.10
FLAT = 0.05


def build_alerts(monthly: pd.DataFrame) -> pd.DataFrame:
    df = monthly.copy()
    if df.empty:
        return df
    reasons, levels, alert_types = [], [], []
    for _, r in df.iterrows():
        cost_ch = r.get("Total_Cost_Change", np.nan)
        usage_ch = r.get("Total_Usage_Change", np.nan)
        cpt_ch = r.get("Cost_per_Treatment_Change", np.nan)
        days_since = np.nan
        if pd.notna(r.get("Last_Bill_Date", pd.NaT)):
            days_since = (pd.Timestamp.today().normalize() - pd.to_datetime(r["Last_Bill_Date"])).days

        level = "Normal"; atype = "No Significant Change"; reason = "Changes are within normal range."
        max_ch = np.nanmax([x for x in [cost_ch, usage_ch, cpt_ch] if pd.notna(x)] or [np.nan])
        if pd.notna(days_since) and days_since > 45:
            level = "Critical"; atype = "Missing/Late Bill"; reason = f"Last bill date is {int(days_since)} days ago."
        elif pd.notna(cost_ch) and cost_ch >= CRITICAL and (pd.isna(usage_ch) or abs(usage_ch) <= FLAT):
            level = "Critical"; atype = "Cost Up / Usage Flat"; reason = f"Cost changed {cost_ch:+.1%} while usage changed {usage_ch:+.1%}. Possible rate, fee, or billing adjustment."
        elif pd.notna(usage_ch) and usage_ch >= CRITICAL and (pd.isna(r.get("Treatments_Change")) or abs(r.get("Treatments_Change")) <= FLAT):
            level = "Critical"; atype = "Usage Up / Treatments Flat"; reason = f"Usage changed {usage_ch:+.1%} while treatments changed {r.get('Treatments_Change', np.nan):+.1%}. Possible leak, meter, or operational issue."
        elif pd.notna(max_ch) and max_ch >= CRITICAL:
            level = "Critical"; atype = ">20% Change"; reason = f"At least one key metric increased more than 20%."
        elif pd.notna(max_ch) and max_ch >= REVIEW:
            level = "Review"; atype = "10–20% Change"; reason = f"At least one key metric increased between 10% and 20%."
        elif pd.notna(max_ch) and max_ch > 0:
            level = "Info"; atype = "Minor Change"; reason = "Minor movement under 10%."
        levels.append(level); alert_types.append(atype); reasons.append(reason)
    df["Alert Level"] = levels
    df["Alert Type"] = alert_types
    df["Reason"] = reasons
    df["Estimated Monthly Impact"] = (df["Total_Cost"] - df["Total_Cost_Prev"]).clip(lower=0).fillna(0)
    return df


def generate_insight(row: pd.Series) -> str:
    prop = row.get("Property Name", "This property")
    utility = row.get("Utility", "utility")
    cost = row.get("Total_Cost_Change")
    usage = row.get("Total_Usage_Change")
    tx = row.get("Treatments_Change")
    if pd.notna(usage) and pd.notna(tx) and usage >= 0.20 and abs(tx) <= 0.05:
        return f"{prop} {utility} usage increased {usage:.0%} while treatments changed only {tx:.0%}. Review for leaks, meter accuracy, equipment issues, or unusual operations."
    if pd.notna(cost) and pd.notna(usage) and cost >= 0.20 and abs(usage) <= 0.05:
        return f"{prop} {utility} cost increased {cost:.0%} while usage stayed relatively stable. This may indicate a rate increase, added fees, or a billing adjustment."
    if pd.notna(cost) and pd.notna(usage) and cost >= 0.10 and usage >= 0.10:
        return f"{prop} {utility} cost and usage both increased. Compare against treatment volume and days billed to determine whether the change is operationally justified."
    if row.get("Alert Type") == "Missing/Late Bill":
        return f"{prop} may have a missing or late {utility} bill based on the last bill date. Confirm bill receipt and provider status."
    return row.get("Reason", "No major anomaly detected.")
