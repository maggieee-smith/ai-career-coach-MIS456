"""Job market data: BLS OEWS May 2025 wages (via WageDex) plus BLS typical education/experience."""
import json
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

STATE_ABBR = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA", "Colorado": "CO",
    "Connecticut": "CT", "Delaware": "DE", "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA",
    "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO", "Montana": "MT",
    "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM",
    "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC", "South Dakota": "SD",
    "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}

SOURCE_NOTE = ("Pay and state data: U.S. Bureau of Labor Statistics, Occupational Employment and Wage Statistics "
               "(OEWS), May 2025, as republished by WageDex. Education/experience: BLS Occupational Outlook Handbook. "
               "Where only the top-paying states are published, the map shows those states only.")


def occupations() -> list[dict]:
    return json.loads((DATA_DIR / "occupations.json").read_text())


def occupation_titles() -> list[str]:
    return [o["title"] for o in occupations()]


def get_occupation(title: str) -> dict | None:
    t = title.lower().strip()
    for o in occupations():
        if o["title"].lower() == t:
            return o
    for o in occupations():  # fuzzy: match on title, aka, or family words
        hay = f"{o['title']} {o['aka']}".lower()
        if t in hay or any(w in hay for w in t.split() if len(w) > 4):
            return o
    return None


def state_wages() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "state_wages.csv")
    df["abbr"] = df["state"].map(STATE_ABBR)
    return df


def pay_table(titles: list[str]) -> pd.DataFrame:
    rows = []
    for t in titles:
        o = get_occupation(t)
        if not o:
            continue
        rows.append({
            "Job": o["title"], "Low (10th pct)": o["p10"], "25th pct": o["p25"], "Median": o["p50"],
            "Mean": o["mean"], "75th pct": o["p75"], "High (90th pct)": o["p90"], "U.S. jobs": o["employment"],
        })
    return pd.DataFrame(rows)


# Illustrative promotion pipeline. Years are typical ranges students report for large employers; salary at each
# stage is anchored to the real BLS pay distribution for the occupation (25th pct -> median -> 75th -> 90th).
STAY_YEARS = [0, 2, 5, 9, 14]
SWITCH_YEARS = [0, 2, 4, 7, 11]   # assumption: changing employers every ~2-3 years compresses promotions
SWITCH_PREMIUM = 0.08             # assumption: ~8% higher pay at each level from external offers


def career_trajectory(title: str) -> pd.DataFrame:
    o = get_occupation(title)
    if not o:
        return pd.DataFrame()
    p10, p50, p90 = o["p10"], o["p50"], o["p90"]
    p25 = o["p25"] or round((p10 + p50) / 2, -2)
    p75 = o["p75"] or round((p50 + p90) / 2, -2)
    salaries = [p25 * 0.92, (p25 + p50) / 2, p75, (p75 + p90) / 2, p90 * 1.05]
    rows = []
    for i, stage in enumerate(o["ladder"]):
        rows.append({"Path": "Stay at one company", "Year": STAY_YEARS[i], "Title": stage, "Salary": round(salaries[i], -3)})
        rows.append({"Path": "Switch companies every 2–3 yrs", "Year": SWITCH_YEARS[i], "Title": stage,
                     "Salary": round(salaries[i] * (1 + SWITCH_PREMIUM) if i else salaries[i], -3)})
    return pd.DataFrame(rows)


def occupation_summary_text(o: dict) -> str:
    def m(v):
        return f"${v:,.0f}" if v else "n/a"
    growth = f"{o['growth']}% projected growth 2024–34" if o.get("growth") is not None else "growth n/a"
    return (f"{o['title']} ({o['aka']}, SOC {o['soc']}): {o['employment']:,} U.S. jobs; pay 10th pct {m(o['p10'])}, "
            f"median {m(o['p50'])}, 90th pct {m(o['p90'])}, mean {m(o['mean'])}; {growth}; typical education: "
            f"{o['edu']}; related work experience required: {o['exp']}; career ladder: {' -> '.join(o['ladder'])}; "
            f"example employers: {', '.join(o['companies'])}.")
