"""Live job postings from the Adzuna API (https://developer.adzuna.com).

Adzuna's trial gives only 25 calls, so by default the app is frugal: postings load only when the user clicks a
button, each search is ONE call (postings + total count together), and results are cached for an hour.
Set ADZUNA_FULL = "1" in secrets (paid plan) to also use live postings on the home page and in the agent.
If ADZUNA_APP_ID / ADZUNA_APP_KEY aren't set, `enabled()` is False and the app falls back to LinkedIn links.
"""
from __future__ import annotations

import os

import requests
import streamlit as st

from core import config

BASE = os.getenv("ADZUNA_BASE", "https://api.adzuna.com/v1/api/jobs/us")


def enabled() -> bool:
    return config.fake_mode() or bool(config.get_secret("ADZUNA_APP_ID") and config.get_secret("ADZUNA_APP_KEY"))


def full_mode() -> bool:
    """Paid plan: allow automatic calls (home page, agent tool). Off by default to save trial calls."""
    return enabled() and str(config.get_secret("ADZUNA_FULL", "0")) == "1"


def _auth() -> dict:
    return {"app_id": config.get_secret("ADZUNA_APP_ID"), "app_key": config.get_secret("ADZUNA_APP_KEY")}


def _clean(r: dict) -> dict:
    return {
        "title": (r.get("title") or "").replace("<strong>", "").replace("</strong>", ""),
        "company": (r.get("company") or {}).get("display_name", "Company not listed"),
        "location": (r.get("location") or {}).get("display_name", ""),
        "salary_min": r.get("salary_min"),
        "salary_max": r.get("salary_max"),
        "salary_predicted": str(r.get("salary_is_predicted", "0")) == "1",
        "url": r.get("redirect_url", ""),
        "created": (r.get("created") or "")[:10],
        "description": (r.get("description") or "")[:300],
    }


@st.cache_data(ttl=3600, show_spinner=False)
def search_with_count(what: str, where: str = "", n: int = 20, max_days_old: int = 30) -> tuple[list[dict], int | None]:
    """ONE API call: the most recent postings matching `what` in `where`, plus the total number of matches."""
    if config.fake_mode():
        return _fake(what, n), 1234
    params = {**_auth(), "what": what, "results_per_page": n, "max_days_old": max_days_old,
              "sort_by": "date", "content-type": "application/json"}
    if where and where != "United States":
        params["where"] = where
    resp = requests.get(f"{BASE}/search/1", params=params, timeout=15)
    resp.raise_for_status()
    body = resp.json()
    return [_clean(r) for r in body.get("results", [])], body.get("count")


def search(what: str, where: str = "", n: int = 10, max_days_old: int = 30) -> list[dict]:
    return search_with_count(what, where, n, max_days_old)[0]


@st.cache_data(ttl=3600, show_spinner=False)
def count(what: str, where: str = "") -> int | None:
    """Total number of current postings for a query."""
    if config.fake_mode():
        return 1234
    params = {**_auth(), "what": what, "results_per_page": 1, "content-type": "application/json"}
    if where and where != "United States":
        params["where"] = where
    resp = requests.get(f"{BASE}/search/1", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("count")


@st.cache_data(ttl=3600, show_spinner=False)
def histogram(what: str, where: str = "") -> dict[int, int]:
    """Advertised-salary distribution: {salary bucket lower bound: number of postings}."""
    if config.fake_mode():
        return {40000: 120, 60000: 340, 80000: 520, 100000: 410, 120000: 220, 140000: 90}
    params = {**_auth(), "what": what, "content-type": "application/json"}
    if where and where != "United States":
        params["where"] = where
    resp = requests.get(f"{BASE}/histogram", params=params, timeout=15)
    resp.raise_for_status()
    return {int(float(k)): int(v) for k, v in (resp.json().get("histogram") or {}).items()}


def salary_text(j: dict) -> str:
    lo, hi = j.get("salary_min"), j.get("salary_max")
    if not lo and not hi:
        return "Salary not listed"
    if lo and hi and abs(hi - lo) > 1:
        s = f"${lo / 1000:,.0f}K–${hi / 1000:,.0f}K"
    else:
        s = f"${(lo or hi) / 1000:,.0f}K"
    return s + (" (est.)" if j.get("salary_predicted") else "")


def _fake(what, n):
    cos = [("Deloitte", "Phoenix, AZ"), ("KPMG", "Tempe, AZ"), ("EY", "Denver, CO"), ("Accenture", "Austin, TX"),
           ("PwC", "Chicago, IL"), ("Intel", "Chandler, AZ")]
    return [{"title": f"{what} {'I' if i % 2 else 'Associate'}", "company": c, "location": l,
             "salary_min": 65000 + i * 4000, "salary_max": 85000 + i * 5000, "salary_predicted": i % 3 == 0,
             "url": "https://www.adzuna.com", "created": "2026-11-0" + str(1 + i % 2), "description": "Sample posting."}
            for i, (c, l) in enumerate(cos[:n])]
