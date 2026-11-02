"""Visual theme: fonts, colors, and reusable HTML components (hero, page headers, cards, job rows)."""
import html
from pathlib import Path
from urllib.parse import quote_plus

import streamlit as st

ASSETS = Path(__file__).resolve().parent.parent / "assets"

BLUE = "#1F2BFF"
BLUE_SOFT = "#EEF0FF"
INK = "#16181D"
MUTED = "#6B7080"
LINE = "#ECEDF3"
# Chart palette (blue-first, matches the UI)
CHART = ["#1F2BFF", "#16181D", "#7B83FF", "#F5B400", "#00A3A3", "#E5484D", "#8E95A9", "#B8BDFF"]

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600;700&display=swap');

html, body, .stApp, .stMarkdown, p, li, label, input, textarea, [data-testid="stWidgetLabel"],
[data-testid="stSidebarNavLink"] span:not([data-testid="stIconMaterial"]) {{
  font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif;
}}
[data-testid="stIconMaterial"] {{ font-family: 'Material Symbols Rounded' !important; }}
.stApp {{
  background:
    radial-gradient(1200px 500px at 85% -10%, #EEF0FF 0%, rgba(238,240,255,0) 60%),
    radial-gradient(900px 400px at -10% 10%, #F5F3FF 0%, rgba(245,243,255,0) 55%),
    #FFFFFF;
  color: {INK};
}}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stToolbar"], [data-testid="stAppDeployButton"], footer {{ display: none !important; }}
[data-testid="stMainBlockContainer"] {{ padding-top: 2.2rem; max-width: 1180px; }}

/* Headings */
h1, .serif {{ font-family: 'Instrument Serif', Georgia, serif !important; font-weight: 400 !important;
  letter-spacing: -0.5px; color: {INK}; }}
h2, h3, h4 {{ font-family: 'Inter', sans-serif !important; font-weight: 650 !important; color: {INK};
  letter-spacing: -0.3px; }}
[data-testid="stHeaderActionElements"] {{ display: none; }}

/* Sidebar */
[data-testid="stSidebar"] {{ background: #FAFAFD; border-right: 1px solid {LINE}; }}
[data-testid="stNavSectionHeader"] {{ color: {MUTED}; font-size: 0.72rem; text-transform: uppercase;
  letter-spacing: 1px; font-weight: 600; }}
[data-testid="stSidebarNavLink"] {{ border-radius: 10px; padding: 0.35rem 0.75rem; margin: 1px 0; }}
[data-testid="stSidebarNavLink"] span {{ color: #3B3F4A !important; font-weight: 500; }}
[data-testid="stSidebarNavLink"][aria-current="page"] {{ background: #FFFFFF; box-shadow: 0 1px 3px rgba(22,24,29,.08); }}
[data-testid="stSidebarNavLink"][aria-current="page"] span {{ color: {INK} !important; font-weight: 650; }}
[data-testid="stSidebarNavLink"]:hover {{ background: {BLUE_SOFT}; }}

/* Buttons */
button[data-testid="stBaseButton-primary"], [data-testid="stDownloadButton"] button {{
  background: {BLUE} !important; border: 1px solid {BLUE} !important; color: #fff !important;
  border-radius: 10px !important; font-weight: 600 !important; padding: 0.55rem 1.3rem !important;
  box-shadow: 0 6px 16px rgba(31,43,255,.22);
}}
button[data-testid="stBaseButton-primary"]:hover {{ background: #1420D6 !important; }}
button[data-testid="stBaseButton-secondary"] {{
  background: {BLUE_SOFT} !important; border: 1px solid {BLUE_SOFT} !important; color: {BLUE} !important;
  border-radius: 10px !important; font-weight: 600 !important;
}}
button[data-testid="stBaseButton-secondary"]:hover {{ border-color: {BLUE} !important; }}
[data-testid="stPageLink"] a {{ background: {BLUE_SOFT}; border-radius: 10px; }}
[data-testid="stPageLink"] a span {{ color: {BLUE} !important; font-weight: 600; }}

/* Inputs */
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div {{
  border-radius: 10px !important; background: #FFFFFF !important; border-color: {LINE} !important;
}}
[data-testid="stFileUploaderDropzone"] {{ background: #FFFFFF; border: 1.5px dashed #C9CCF5; border-radius: 12px; }}
label p {{ font-weight: 500; color: #3B3F4A; }}

/* Cards: bordered containers, expanders, metrics */
[data-testid="stVerticalBlockBorderWrapper"], div[class*="st-key-card"] {{
  border-radius: 16px !important; border-color: {LINE} !important; background: #FFFFFF;
  box-shadow: 0 1px 2px rgba(22,24,29,.04), 0 8px 24px rgba(22,24,29,.04);
}}
[data-testid="stExpander"] details {{ border-radius: 12px; border-color: {LINE}; background: #FFFFFF; }}
[data-testid="stMetric"] {{ background: #FFFFFF; border: 1px solid {LINE}; border-radius: 14px; padding: 14px 16px; }}
[data-testid="stMetricLabel"] p {{ color: {MUTED}; font-size: .8rem; }}
[data-testid="stMetricValue"] {{ font-family: 'Instrument Serif', Georgia, serif; font-size: 2.1rem; }}
[data-testid="stProgressBarTrack"] > div {{ background-color: #E7E9F6; }}
[data-testid="stAlert"] {{ border-radius: 12px; }}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{ gap: 18px; border-bottom: 1px solid {LINE}; }}
.stTabs [data-baseweb="tab"] p {{ font-weight: 600; }}
.stTabs [aria-selected="true"] p {{ color: {INK}; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: {BLUE}; }}

/* Blue panel (steps section on home) */
div[class*="st-key-bluepanel"] {{ background: linear-gradient(160deg, #5B5FF5 0%, #3A3FF0 100%); border-radius: 22px;
  padding: 26px 26px 18px; box-shadow: 0 20px 50px rgba(31,43,255,.25); }}
div[class*="st-key-bluepanel"] div[class*="st-key-inner"] {{ background: #FFFFFF; border-radius: 14px; padding: 16px 18px; }}

/* Custom HTML components */
.cc-eyebrow {{ color: {BLUE}; font-size: .74rem; font-weight: 700; letter-spacing: 1.6px; text-transform: uppercase; }}
.cc-hero {{ text-align: center; padding: 34px 0 10px; }}
.cc-hero h1 {{ font-size: clamp(2.6rem, 6vw, 4.4rem) !important; line-height: 1.02; margin: 10px auto 18px; max-width: 900px; }}
.cc-hero p {{ color: {MUTED}; font-size: 1.12rem; max-width: 660px; margin: 0 auto; line-height: 1.6; }}
.cc-pagehead {{ text-align: center; padding: 8px 0 18px; }}
.cc-pagehead h1 {{ font-size: clamp(2.3rem, 5vw, 3.4rem) !important; margin: 6px 0 8px; line-height: 1.05; }}
.cc-pagehead p {{ color: {MUTED}; max-width: 640px; margin: 0 auto; }}
.cc-section {{ text-align: center; margin: 40px 0 18px; }}
.cc-section h2 {{ font-family: 'Instrument Serif', Georgia, serif !important; font-weight: 400 !important;
  font-size: 2.4rem; line-height: 1.1; margin: 4px 0 6px; letter-spacing: -.3px; }}
.cc-section p {{ color: {MUTED}; }}
.cc-stat {{ text-align: center; padding: 10px; }}
.cc-stat .n {{ font-family: 'Instrument Serif', Georgia, serif; font-size: 2.8rem; line-height: 1; color: {INK}; }}
.cc-stat .l {{ color: {MUTED}; font-size: .86rem; margin-top: 6px; }}
.cc-step {{ padding: 14px 0 16px; border-bottom: 1px solid {LINE}; }}
.cc-step .num {{ display:inline-block; font-size:.7rem; font-weight:700; color:{BLUE}; background:{BLUE_SOFT};
  border-radius:6px; padding:2px 7px; }}
.cc-step .t {{ font-weight: 650; font-size: 1.08rem; margin-top: 8px; }}
.cc-step .d {{ color: {MUTED}; font-size: .9rem; margin-top: 2px; }}
.cc-step.active .t {{ color: {BLUE}; }}
.cc-welcome h2 {{ font-size: 1.8rem; margin: 0; }}
.cc-welcome p {{ color: {MUTED}; margin: 2px 0 0; }}
.cc-tool {{ background:#fff; border:1px solid {LINE}; border-radius:16px; padding:18px; height: 100%;
  box-shadow: 0 8px 24px rgba(22,24,29,.04); }}
.cc-tool .ic {{ width:44px; height:44px; border-radius:12px; background:{BLUE_SOFT}; display:flex; align-items:center;
  justify-content:center; font-size:22px; }}
.cc-tool .t {{ font-weight:650; margin-top:12px; }}
.cc-tool .d {{ color:{MUTED}; font-size:.86rem; margin-top:4px; min-height: 2.6em; }}
.cc-jobs {{ background:#fff; border:1px solid {LINE}; border-radius:18px; padding:20px 20px 10px;
  box-shadow: 0 8px 24px rgba(22,24,29,.05); }}
.cc-jobs .hd {{ font-weight:700; font-size:1.15rem; margin-bottom: 12px; }}
.cc-jobgrid {{ display:grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 10px; }}
.cc-job {{ display:flex; align-items:center; gap:12px; background:#F7F8FC; border-radius:12px; padding:12px 14px; }}
.cc-job .logo {{ width:36px; height:36px; border-radius:50%; color:#fff; font-weight:700; display:flex;
  align-items:center; justify-content:center; font-size:.9rem; flex-shrink:0; }}
.cc-job .tt {{ font-weight:650; font-size:.92rem; color:{INK}; line-height:1.2; }}
.cc-job .co {{ color:{MUTED}; font-size:.78rem; }}
.cc-job a {{ margin-left:auto; color:{BLUE}; font-weight:650; font-size:.88rem; text-decoration:none; }}
.cc-job a:hover {{ text-decoration: underline; }}
.cc-promo {{ background:#fff; border:1px solid {LINE}; border-radius:18px; padding:24px; text-align:center;
  box-shadow: 0 8px 24px rgba(22,24,29,.05); height:100%; }}
.cc-promo .art {{ width:96px; height:96px; border-radius:50%; background:{BLUE_SOFT}; margin:0 auto 14px;
  display:flex; align-items:center; justify-content:center; font-size:42px; }}
.cc-promo .t {{ font-weight:700; font-size:1.2rem; }}
.cc-promo .d {{ color:{MUTED}; font-size:.88rem; margin-top:6px; }}
.cc-footer {{ display:flex; align-items:center; gap:18px; flex-wrap:wrap; background:#fff; border:1px solid {LINE};
  border-radius:16px; padding:14px 18px; margin-top: 30px; }}
.cc-footer .lv {{ font-weight:700; }}
.cc-footer .bar {{ flex:1; min-width:160px; height:8px; background:#E7E9F6; border-radius:8px; overflow:hidden; }}
.cc-footer .bar > div {{ height:100%; background:{BLUE}; border-radius:8px; }}
.cc-footer .badges {{ color:{MUTED}; font-size:.85rem; }}
.cc-chip {{ display:inline-block; background:{BLUE_SOFT}; color:{BLUE}; border-radius:999px; padding:3px 10px;
  font-size:.78rem; font-weight:600; margin: 2px 4px 2px 0; }}
</style>
"""


def _plotly_template():
    import plotly.graph_objects as go
    import plotly.io as pio
    t = go.layout.Template(pio.templates["plotly_white"])
    t.layout.font = dict(family="Inter, -apple-system, Segoe UI, sans-serif", color=INK, size=13)
    t.layout.colorway = CHART
    t.layout.paper_bgcolor = "rgba(0,0,0,0)"
    t.layout.plot_bgcolor = "rgba(0,0,0,0)"
    t.layout.xaxis = dict(gridcolor="#EEF0F6", zeroline=False)
    t.layout.yaxis = dict(gridcolor="#EEF0F6", zeroline=False)
    pio.templates["career"] = t
    pio.templates.default = "career"


def apply():
    _plotly_template()
    st.markdown(CSS, unsafe_allow_html=True)
    st.logo(str(ASSETS / "logo.svg"), icon_image=str(ASSETS / "icon.svg"), size="large")


def esc(s) -> str:
    return html.escape(str(s or ""))


def page_header(title: str, subtitle: str = "", eyebrow: str = ""):
    st.markdown(f"""<div class="cc-pagehead">{f'<div class="cc-eyebrow">{esc(eyebrow)}</div>' if eyebrow else ''}
      <h1>{esc(title)}</h1>{f'<p>{esc(subtitle)}</p>' if subtitle else ''}</div>""", unsafe_allow_html=True)


def section(title: str, subtitle: str = "", eyebrow: str = ""):
    st.markdown(f"""<div class="cc-section">{f'<div class="cc-eyebrow">{esc(eyebrow)}</div>' if eyebrow else ''}
      <h2>{esc(title)}</h2>{f'<p>{esc(subtitle)}</p>' if subtitle else ''}</div>""", unsafe_allow_html=True)


LOGO_COLORS = ["#E5484D", "#1F2BFF", "#16181D", "#00A3A3", "#F59E0B", "#8B5CF6", "#0EA5E9", "#22C55E"]


def job_rows_html(jobs: list, title: str = "Trending Jobs") -> str:
    """jobs = [(title, company)] or [{title, company, sub, url}]. Tuples link to a live LinkedIn search;
    dicts (live Adzuna postings) link to the real listing."""
    rows = []
    for i, j in enumerate(jobs):
        if isinstance(j, dict):
            t, c, sub, url = j["title"], j["company"], j.get("sub", j["company"]), j["url"]
        else:
            t, c = j
            sub, url = c, f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(t + ' ' + c)}"
        initials = "".join(w[0] for w in c.replace("&", "").split()[:2]).upper() or "?"
        rows.append(f"""<div class="cc-job"><div class="logo" style="background:{LOGO_COLORS[i % len(LOGO_COLORS)]}">{esc(initials)}</div>
          <div><div class="tt">{esc(t)}</div><div class="co">{esc(sub)}</div></div>
          <a href="{esc(url)}" target="_blank" rel="noopener">Apply</a></div>""")
    return f'<div class="cc-jobs"><div class="hd">{esc(title)}</div><div class="cc-jobgrid">{"".join(rows)}</div></div>'


def chips(items) -> str:
    return "".join(f'<span class="cc-chip">{esc(i)}</span>' for i in items)
