from __future__ import annotations

import numpy as np
import pandas as pd

import config
from utils.calculations import pct_change, utility_aggregate


def _severity_from_values(*changes) -> str:
    valid = [abs(c) for c in changes if c is not None and not pd.isna(c)]
    if not valid:
        return "Info"
    high = max(valid)
    if high >= getattr(config, "CRITICAL_THRESHOLD", 20.0):
        return "Critical"
    if high >= getattr(config, "WARNING_THRESHOLD", 10.0):
        return "Review"
    return "Info"


def _priority(sev: str) -> int:
    return {"Critical": 3, "Review": 2, "Info": 1, "Normal": 0}.get(sev, 0)


def build_alerts(df: pd.DataFrame, current_month, previous_month=None) -> pd.DataFrame:
    """Create one alert record per property/utility for current month vs previous."""
    uagg = utility_aggregate(df)
    if uagg.empty:
        return pd.DataFrame()

    current_month = pd.to_datetime(current_month)
    previous_month = pd.to_datetime(previous_month) if previous_month is not None else None
    cur = uagg[uagg["billing_month"] == current_month].copy()
    prev = uagg[uagg["billing_month"] == previous_month].copy() if previous_month is not None else uagg.iloc[0:0].copy()

    prev = prev.rename(columns={
        "amount": "prev_amount", "usage": "prev_usage", "treatments": "prev_treatments",
        "cost_per_treatment": "prev_cost_per_treatment", "cost_per_usage": "prev_cost_per_usage",
        "billing_date": "prev_billing_date",
    })
    merge_cols = ["state", "property", "utility"]
    merged = cur.merge(prev[merge_cols + ["prev_amount", "prev_usage", "prev_treatments", "prev_cost_per_treatment", "prev_cost_per_usage", "prev_billing_date"]], on=merge_cols, how="left")

    rows = []
    today = pd.Timestamp.today().normalize()
    for _, r in merged.iterrows():
        cost_chg = pct_change(r["amount"], r.get("prev_amount"))
        usage_chg = pct_change(r["usage"], r.get("prev_usage"))
        cpt_chg = pct_change(r["cost_per_treatment"], r.get("prev_cost_per_treatment"))
        cpu_chg = pct_change(r["cost_per_usage"], r.get("prev_cost_per_usage"))
        treatment_chg = pct_change(r["treatments"], r.get("prev_treatments"))

        reasons = []
        severity = _severity_from_values(cost_chg if cost_chg and cost_chg > 0 else np.nan,
                                         usage_chg if usage_chg and usage_chg > 0 else np.nan,
                                         cpt_chg if cpt_chg and cpt_chg > 0 else np.nan,
                                         cpu_chg if cpu_chg and cpu_chg > 0 else np.nan)
        if cost_chg is not None and not pd.isna(cost_chg) and cost_chg >= config.CRITICAL_THRESHOLD:
            reasons.append(f"Cost increased {cost_chg:.1f}%")
        elif cost_chg is not None and not pd.isna(cost_chg) and cost_chg >= config.WARNING_THRESHOLD:
            reasons.append(f"Cost increased {cost_chg:.1f}%")

        if usage_chg is not None and not pd.isna(usage_chg) and usage_chg >= config.CRITICAL_THRESHOLD:
            reasons.append(f"Usage increased {usage_chg:.1f}%")
        elif usage_chg is not None and not pd.isna(usage_chg) and usage_chg >= config.WARNING_THRESHOLD:
            reasons.append(f"Usage increased {usage_chg:.1f}%")

        if cpt_chg is not None and not pd.isna(cpt_chg) and cpt_chg >= config.CRITICAL_THRESHOLD:
            reasons.append(f"Cost/treatment increased {cpt_chg:.1f}%")
        elif cpt_chg is not None and not pd.isna(cpt_chg) and cpt_chg >= config.WARNING_THRESHOLD:
            reasons.append(f"Cost/treatment increased {cpt_chg:.1f}%")

        # Cost up while usage flat/down suggests rate or fees.
        if cost_chg is not None and usage_chg is not None and not pd.isna(cost_chg) and not pd.isna(usage_chg):
            if cost_chg >= config.WARNING_THRESHOLD and usage_chg <= config.FLAT_CHANGE_TOLERANCE:
                severity = "Critical" if cost_chg >= config.CRITICAL_THRESHOLD else max(severity, "Review", key=_priority)
                reasons.append("Cost rose while usage was flat/decreased")

        # Usage up while treatments flat suggests facility issue.
        if usage_chg is not None and treatment_chg is not None and not pd.isna(usage_chg) and not pd.isna(treatment_chg):
            if usage_chg >= config.WARNING_THRESHOLD and treatment_chg <= config.FLAT_CHANGE_TOLERANCE:
                severity = "Critical" if usage_chg >= config.CRITICAL_THRESHOLD else max(severity, "Review", key=_priority)
                reasons.append("Usage rose faster than treatments")

        days_since_bill = np.nan
        if pd.notna(r.get("billing_date")):
            days_since_bill = (today - pd.to_datetime(r["billing_date"]).normalize()).days
            if days_since_bill > config.MISSING_BILL_DAYS:
                severity = "Critical"
                reasons.append(f"Last bill is {days_since_bill} days old")

        if not reasons and severity == "Info":
            # Keep low-level positive/negative changes out of the alert center.
            continue

        rows.append({
            "Severity": severity,
            "State": r["state"],
            "Property": r["property"],
            "Utility": r["utility"],
            "Reason": "; ".join(dict.fromkeys(reasons)) or "Minor movement",
            "Current Cost": r["amount"],
            "Previous Cost": r.get("prev_amount"),
            "Cost Change %": cost_chg,
            "Current Usage": r["usage"],
            "Previous Usage": r.get("prev_usage"),
            "Usage Change %": usage_chg,
            "Current Cost/Treatment": r["cost_per_treatment"],
            "Previous Cost/Treatment": r.get("prev_cost_per_treatment"),
            "Cost/Treatment Change %": cpt_chg,
            "Current Cost/Usage": r["cost_per_usage"],
            "Previous Cost/Usage": r.get("prev_cost_per_usage"),
            "Cost/Usage Change %": cpu_chg,
            "Treatments Change %": treatment_chg,
            "Estimated Monthly Impact": max(0, (r["amount"] or 0) - (r.get("prev_amount") if pd.notna(r.get("prev_amount")) else 0)),
            "Days Since Bill": days_since_bill,
            "Explanation": explain_change(r["utility"], cost_chg, usage_chg, treatment_chg, cpt_chg),
        })

    if not rows:
        return pd.DataFrame(columns=["Severity", "Property", "Utility", "Reason"])
    out = pd.DataFrame(rows)
    out["Priority"] = out["Severity"].map({"Critical": 3, "Review": 2, "Info": 1}).fillna(0)
    out = out.sort_values(["Priority", "Estimated Monthly Impact"], ascending=[False, False]).drop(columns=["Priority"])
    return out


def explain_change(utility, cost_chg, usage_chg, treatment_chg, cpt_chg) -> str:
    def ok(x):
        return x is not None and not pd.isna(x)
    u = str(utility).title()
    if ok(cost_chg) and ok(usage_chg) and cost_chg >= 20 and usage_chg <= 5:
        return f"{u} cost rose significantly while usage stayed relatively flat. Review rates, fees, billing adjustments, or invoice line items."
    if ok(usage_chg) and ok(treatment_chg) and usage_chg >= 20 and treatment_chg <= 5:
        if "Water" in u or "Sewer" in u:
            return f"{u} usage rose much faster than treatment volume. Check for leak, meter issue, irrigation, or unusual facility activity."
        return f"{u} usage rose much faster than treatment volume. Check equipment operation, schedule changes, or meter/billing issues."
    if ok(cpt_chg) and cpt_chg >= 20:
        return "Cost per treatment increased sharply, meaning utility cost rose faster than treatment volume. Prioritize review."
    if ok(cost_chg) and ok(usage_chg) and abs(cost_chg - usage_chg) <= 5 and cost_chg >= 10:
        return "Cost and usage increased at a similar rate, which may be operationally consistent. Compare treatment volume and days billed."
    if ok(cost_chg) and cost_chg < 0:
        return "Cost decreased compared with the prior month. Monitor to confirm the improvement continues."
    return "Review cost, usage, days billed, and treatment volume to determine whether the change is operational or billing-related."


def alert_counts(alerts: pd.DataFrame) -> dict:
    if alerts is None or alerts.empty:
        return {"Critical": 0, "Review": 0, "Info": 0, "Total": 0}
    return {
        "Critical": int((alerts["Severity"] == "Critical").sum()),
        "Review": int((alerts["Severity"] == "Review").sum()),
        "Info": int((alerts["Severity"] == "Info").sum()),
        "Total": int(len(alerts)),
    }
