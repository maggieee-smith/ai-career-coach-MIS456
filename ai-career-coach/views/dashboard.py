"""Market Dashboard: a salary-profile layout (job header + tabs, big pay figure with range bar, career path
timeline, ranked salary list), using real BLS data."""
import pandas as pd
import plotly.express as px
import streamlit as st

import plotly.graph_objects as go

from core import data, gamify, jobs_api, state, theme

esc = theme.esc

CSS = """
<style>
.sp-head { background:#fff; border:1px solid #ECEDF3; border-radius:18px; padding:20px 24px 6px;
  box-shadow:0 8px 24px rgba(22,24,29,.04); margin-bottom: 6px; }
.sp-head .t { font-family:'Instrument Serif', Georgia, serif; font-size:2.3rem; line-height:1.05; color:#16181D; }
.sp-head .s { color:#6B7080; font-size:.92rem; margin-top:4px; }
.sp-card { background:#fff; border:1px solid #ECEDF3; border-radius:18px; padding:24px 26px;
  box-shadow:0 8px 24px rgba(22,24,29,.04); height:100%; }
.sp-q { font-weight:700; font-size:1.3rem; color:#16181D; line-height:1.3; }
.sp-badge { display:inline-flex; gap:6px; align-items:center; background:#E8F7EE; color:#137A3A; font-weight:600;
  font-size:.78rem; border-radius:999px; padding:3px 10px; margin:12px 0 6px; }
.sp-badge.est { background:#FFF6E0; color:#8A5A00; }
.sp-big { font-family:'Instrument Serif', Georgia, serif; font-size:3.6rem; line-height:1; color:#16181D; margin-top:8px; }
.sp-big span, .sp-mid span { font-family:Inter, sans-serif; font-size:.95rem; color:#6B7080; }
.sp-lbl { color:#6B7080; font-size:.85rem; border-bottom:1px dotted #B8BDC9; display:inline-block; margin-top:4px; }
.sp-row { display:flex; gap:34px; align-items:flex-start; margin-top:22px; flex-wrap:wrap; }
.sp-stats { min-width:150px; }
.sp-mid { font-weight:700; font-size:1.25rem; color:#16181D; }
.sp-mid + .sp-l2 { color:#6B7080; font-size:.84rem; margin-bottom:14px; }
.sp-range { flex:1; min-width:300px; padding-top:4px; }
.rb { position:relative; height:110px; }
.rb .track { position:absolute; top:58px; left:0; right:0; height:14px; border-radius:7px; background:#D9DCFF; }
.rb .likely { position:absolute; top:58px; height:14px; background:#1F2BFF; border-radius:3px; }
.rb .mk { position:absolute; top:38px; width:0; height:0; border-left:7px solid transparent; border-right:7px solid transparent;
  border-top:9px solid #16181D; transform:translateX(-7px); }
.rb .mkl { position:absolute; top:6px; transform:translateX(-50%); font-weight:700; font-size:.95rem; white-space:nowrap; }
.rb .mkl span { font-weight:400; color:#6B7080; font-size:.8rem; }
.rb .lab { position:absolute; font-size:.82rem; color:#3B3F4A; transform:translateX(-50%); white-space:nowrap; }
.rb .lab.top { top:34px; } .rb .lab.bot { top:80px; }
.rb .lab.l { transform:none; } .rb .lab.r { transform:translateX(-100%); }
.legend { display:flex; gap:22px; font-size:.82rem; color:#3B3F4A; margin-top:2px; }
.legend i { display:inline-block; width:14px; height:14px; border-radius:3px; vertical-align:-2px; margin-right:6px; }
.sp-note { color:#6B7080; font-size:.84rem; margin-top:16px; line-height:1.5; }
.cp-t { font-weight:700; font-size:1.05rem; margin-bottom:14px; color:#16181D; }
.cp { position:relative; padding-left:22px; }
.cp:before { content:''; position:absolute; left:5px; top:8px; bottom:8px; width:2px; background:#E3E5F2; }
.cp .it { position:relative; margin-bottom:16px; }
.cp .it:before { content:''; position:absolute; left:-21px; top:5px; width:10px; height:10px; border-radius:50%;
  background:#fff; border:2px solid #B8BDC9; }
.cp .it.on:before { background:#1F2BFF; border-color:#1F2BFF; }
.cp .p { font-weight:700; color:#16181D; font-size:.95rem; } .cp .p span { font-weight:400; color:#6B7080; font-size:.8rem; }
.cp .n { color:#3B3F4A; font-size:.86rem; } .cp .y { color:#9095A5; font-size:.76rem; }
.sl { background:#fff; border:1px solid #ECEDF3; border-radius:18px; padding:8px 26px 10px;
  box-shadow:0 8px 24px rgba(22,24,29,.04); }
.sl .r { display:grid; grid-template-columns: 1.6fr .8fr 1.4fr; align-items:center; gap:18px; padding:16px 0;
  border-bottom:1px solid #ECEDF3; }
.sl .r:last-child { border-bottom:none; }
.sl .jt { color:#1F2BFF; font-weight:650; font-size:1.08rem; }
.sl .js { color:#9095A5; font-size:.78rem; margin-top:2px; }
.sl .pay { font-size:1.25rem; color:#16181D; text-align:right; } .sl .pay span { color:#9095A5; font-size:.78rem; display:block; }
.sl .bar { position:relative; height:8px; background:#ECEDF6; border-radius:6px; }
.sl .bar .f { position:absolute; top:0; bottom:0; background:#B8BDFF; border-radius:6px; }
.sl .bar .d { position:absolute; top:-4px; width:12px; height:12px; background:#1F2BFF; border:2px solid #fff;
  border-radius:50%; transform:translateX(-6px); box-shadow:0 0 0 1px #1F2BFF; }
.sl .bl { display:flex; justify-content:space-between; color:#9095A5; font-size:.72rem; margin-top:6px; }
.sl .r.me .jt:after { content:'Your match'; margin-left:8px; font-size:.68rem; font-weight:600; color:#1F2BFF;
  background:#EEF0FF; border-radius:999px; padding:2px 8px; vertical-align:2px; }
.sl-h { display:grid; grid-template-columns: 1.6fr .8fr 1.4fr; gap:18px; color:#6B7080; font-size:.75rem;
  text-transform:uppercase; letter-spacing:1px; font-weight:600; padding:16px 0 4px; border-bottom:1px solid #ECEDF3; }
.sl-h div:nth-child(2) { text-align:right; }
</style>
"""


def money(v):
    return f"${v:,.0f}" if v is not None and pd.notna(v) and v else "n/a"


def k(v):
    return f"${v / 1000:,.0f}K"


def pct(o: dict) -> dict:
    """National percentiles; fills unpublished 25th/75th by interpolation (flagged as estimated)."""
    p10, p50, p90 = o["p10"], o["p50"], o["p90"]
    est = o["p25"] is None or o["p75"] is None
    p25 = o["p25"] or (p10 + p50) / 2
    p75 = o["p75"] or (p50 + p90) / 2
    return dict(p10=p10, p25=p25, p50=p50, p75=p75, p90=p90, mean=o["mean"], est=est)


def location_pay(o: dict, loc: str):
    """Pay figures for a location. For a state we have the real median/mean; the range is the national range scaled
    to that state's median (labeled as an estimate)."""
    nat = pct(o)
    if loc == "United States":
        return nat, False
    row = data.state_wages().query("occupation == @o['title'] and state == @loc").iloc[0]
    f = row["median"] / nat["p50"]
    scaled = {key: nat[key] * f for key in ["p10", "p25", "p75", "p90"]}
    return dict(**scaled, p50=row["median"], mean=row["mean"] if pd.notna(row["mean"]) else None,
                est=True, jobs=row["employment"]), True


def range_bar(p: dict) -> str:
    lo, hi = p["p10"], p["p90"]

    def x(v):
        return max(0, min(100, (v - lo) / (hi - lo) * 100))
    a, b, m = x(p["p25"]), x(p["p75"]), x(p["p50"])
    return f"""<div class="rb">
      <div class="mkl" style="left:{m}%">{money(p['p50'])} <span>/yr</span></div>
      <div class="mk" style="left:{m}%"></div>
      <div class="lab top" style="left:{a}%">{k(p['p25'])}</div><div class="lab top" style="left:{b}%">{k(p['p75'])}</div>
      <div class="track"></div><div class="likely" style="left:{a}%;width:{b - a}%"></div>
      <div class="lab bot l" style="left:0">{k(lo)}</div><div class="lab bot r" style="left:100%">{k(hi)}</div></div>
      <div class="legend"><span><i style="background:#1F2BFF"></i>Most likely range (25th–75th pct)</span>
      <span><i style="background:#D9DCFF"></i>Possible range (10th–90th pct)</span></div>"""


def career_path_html(o: dict) -> str:
    df = data.career_trajectory(o["title"])
    stay = df[df["Path"].str.startswith("Stay")]
    items = "".join(
        f"""<div class="it {'on' if i == 0 else ''}"><div class="p">{money(r.Salary)} <span>/yr</span></div>
        <div class="n">{esc(r.Title)}</div><div class="y">Year {r.Year}+</div></div>"""
        for i, r in enumerate(stay.itertuples()))
    return f'<div class="sp-card"><div class="cp-t">Typical career path <span style="font-weight:400;color:#9095A5;font-size:.8rem">(U.S. pay)</span></div><div class="cp">{items}</div>' \
           f'<div class="y" style="color:#9095A5;font-size:.76rem">Illustrative ladder anchored to BLS pay percentiles. ' \
           f'See the Career Path tab to compare switching companies.</div></div>'


def salary_list_html(mine: set) -> str:
    occs = sorted(data.occupations(), key=lambda o: -o["p50"])
    lo = min(o["p10"] for o in occs)
    hi = max(o["p90"] for o in occs)
    rows = []
    for o in occs:
        a = (o["p10"] - lo) / (hi - lo) * 100
        b = (o["p90"] - lo) / (hi - lo) * 100
        m = (o["p50"] - lo) / (hi - lo) * 100
        rows.append(f"""<div class="r {'me' if o['title'] in mine else ''}">
          <div><div class="jt">{esc(o['title'])}</div><div class="js">{esc(o['aka'])} · {o['employment']:,} U.S. jobs</div></div>
          <div class="pay">{k(o['p50'])}<span>median /yr</span></div>
          <div><div class="bar"><div class="f" style="left:{a}%;width:{b - a}%"></div><div class="d" style="left:{m}%"></div></div>
          <div class="bl" style="padding-left:{a}%;padding-right:{100 - b}%"><span>{k(o['p10'])}</span><span>{k(o['p90'])}</span></div></div></div>""")
    return ('<div class="sl"><div class="sl-h"><div>Job title</div><div>Median pay</div><div>Pay range (10th–90th pct) · dot = median</div></div>'
            + "".join(rows) + "</div>")


def render():
    st.markdown(CSS, unsafe_allow_html=True)
    gamify.award("dashboard")

    titles = data.occupation_titles()
    mine = state.suggested_titles()
    default = mine[0] if mine else "Management Analysts"

    with st.container(key="card_header"):
        c1, c2 = st.columns([3, 2])
        job = c1.selectbox("Job title", titles, index=titles.index(default))
        o = data.get_occupation(job)
        states = sorted(data.state_wages().query("occupation == @job")["state"].tolist())
        loc = c2.selectbox("Location", ["United States"] + states)
        st.markdown(f"""<div class="sp-head" style="border:none;box-shadow:none;padding:4px 0 0">
            <div class="t">{esc(o['title'])} Salaries</div>
            <div class="s">{esc(o['aka'])} · SOC {o['soc']} · {o['employment']:,} jobs in the U.S.</div></div>""",
                    unsafe_allow_html=True)

    tabs = st.tabs(["Salaries", "Live Job Postings", "Locations", "Education & Experience", "Career Path", "Compare All Jobs"])

    with tabs[0]:
        p, is_state = location_pay(o, loc)
        left, right = st.columns([2.2, 1], gap="medium")
        with left:
            badge = ('<div class="sp-badge est">◐ Range estimated from national data</div>' if p["est"]
                     else '<div class="sp-badge">▮ BLS reported data</div>')
            mean_html = (f'<div class="sp-mid">{money(p["mean"])} <span>/yr</span></div><div class="sp-l2">Average (mean) pay</div>'
                         if p.get("mean") else "")
            jobs_line = (f'<div class="sp-mid">{p["jobs"]:,.0f}</div><div class="sp-l2">Jobs in {esc(loc)}</div>'
                         if is_state and pd.notna(p.get("jobs")) else
                         f'<div class="sp-mid">{o["employment"]:,}</div><div class="sp-l2">Jobs nationwide</div>' if not is_state else "")
            note = (f"The median pay for {esc(o['title'].lower())} in {esc(loc)} is {money(p['p50'])} per year"
                    + (f", with an average of {money(p['mean'])}." if p.get("mean") else ".")
                    + " Half of workers earn more than the median and half earn less.")
            if is_state:
                note += " The state range is estimated by scaling the national percentile range to this state's median."
            st.markdown(f"""<div class="sp-card">
                <div class="sp-q">How much does a {esc(o['aka'].split('/')[0].strip())} make in {esc(loc)}?</div>
                {badge}
                <div class="sp-big">{money(p['p50'])}<span> /yr</span></div><div class="sp-lbl">Median pay</div>
                <div class="sp-row"><div class="sp-stats">{mean_html}{jobs_line}</div>
                <div class="sp-range">{range_bar(p)}</div></div>
                <div class="sp-note">{note}</div></div>""", unsafe_allow_html=True)
        with right:
            st.markdown(career_path_html(o), unsafe_allow_html=True)

    with tabs[1]:
        live_tab(o, loc)
    with tabs[2]:
        map_tab(o)
    with tabs[3]:
        edu_tab(o)
    with tabs[4]:
        trajectory_tab(o)
    with tabs[5]:
        st.markdown(salary_list_html(set(mine)), unsafe_allow_html=True)
        st.caption("Sorted by median pay. Bars share one scale so you can compare jobs at a glance."
                   + (" “Your match” marks careers from your quiz or Career Matches." if mine else ""))

    st.caption(data.SOURCE_NOTE)
    gamify.render_footer()


def map_tab(o):
    sw = data.state_wages()
    sub = sw[sw["occupation"] == o["title"]]
    full = sub["employment"].notna().sum() > 20
    metric = st.radio("Color states by", ["Number of jobs", "Median pay"] if full else ["Median pay"], horizontal=True)
    col = "employment" if metric == "Number of jobs" else "median"
    left, right = st.columns([2.2, 1], gap="medium")
    with left:
        fig = px.choropleth(sub, locations="abbr", locationmode="USA-states", scope="usa", color=col,
                            color_continuous_scale=[[0, "#EEF0FF"], [1, "#1F2BFF"]], hover_name="state",
                            hover_data={"abbr": False, "employment": ":,", "median": ":$,.0f"},
                            labels={"employment": "Jobs", "median": "Median pay"})
        fig.update_layout(height=430, margin=dict(l=0, r=0, t=10, b=0), geo=dict(bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig, use_container_width=True)
        if not full:
            st.caption("For this job, BLS (via WageDex) publishes only the top-paying states, so only those are colored.")
    with right:
        top = sub.sort_values(col, ascending=False).head(8)
        rows = "".join(f"""<div class="it {'on' if i == 0 else ''}"><div class="p">{esc(r.state)}</div>
            <div class="n">{money(r.median)} median{f' · {r.employment:,.0f} jobs' if pd.notna(r.employment) else ''}</div></div>"""
                       for i, r in enumerate(top.itertuples()))
        st.markdown(f'<div class="sp-card"><div class="cp-t">Top states by {metric.lower()}</div><div class="cp">{rows}</div></div>',
                    unsafe_allow_html=True)


def edu_tab(o):
    edu_levels = ["High school diploma", "Associate's degree", "Bachelor's degree", "Master's degree", "Doctoral degree"]
    exp_levels = ["None", "Less than 5 years", "5 years or more"]

    def steps(levels, value):
        return "".join(f"""<div class="it {'on' if l == value else ''}"><div class="p" style="{'' if l == value else 'color:#9095A5;font-weight:500'}">
            {esc(l)}</div>{'<div class="n">Typical for this job</div>' if l == value else ''}</div>""" for l in levels)
    c1, c2, c3 = st.columns(3, gap="medium")
    c1.markdown(f'<div class="sp-card"><div class="cp-t">🎓 Typical entry education</div><div class="cp">{steps(edu_levels, o["edu"])}</div></div>',
                unsafe_allow_html=True)
    c2.markdown(f'<div class="sp-card"><div class="cp-t">💼 Related work experience</div><div class="cp">{steps(exp_levels, o["exp"])}</div>'
                f'<div class="y" style="color:#9095A5;font-size:.78rem">“None” means new grads can enter directly. Internships still help a lot.</div></div>',
                unsafe_allow_html=True)
    if o.get("growth") is not None:
        big, lbl = f"{o['growth']}%", "Projected growth, 2024–34"
        extra = f'<div class="sp-row" style="margin-top:18px"><div><div class="sp-mid">{o["employment"]:,}</div><div class="sp-l2">Jobs in the U.S. today</div></div></div>'
    else:
        big, lbl, extra = f"{o['employment']:,}", "Jobs in the U.S. today", ""
    c3.markdown(f"""<div class="sp-card"><div class="cp-t">📈 Outlook</div>
        <div class="sp-big" style="font-size:3rem">{big}</div><div class="sp-lbl">{lbl}</div>{extra}
        <div class="y" style="color:#9095A5;font-size:.78rem;margin-top:14px">Source: BLS.</div></div>""",
                unsafe_allow_html=True)


def trajectory_tab(o):
    df = data.career_trajectory(o["title"])
    fig = px.line(df, x="Year", y="Salary", color="Path", markers=True, text="Title",
                  color_discrete_sequence=["#16181D", "#1F2BFF"], line_shape="hv")
    fig.update_traces(textfont_size=11)
    fig.for_each_trace(lambda t: t.update(textposition="bottom right" if t.name.startswith("Stay") else "top left"))
    fig.update_layout(height=500, yaxis_tickformat="$,.0f", xaxis_title="Years after graduation",
                      legend=dict(orientation="h", y=1.08, title=None), margin=dict(t=40))
    with st.container(border=True):
        st.plotly_chart(fig, use_container_width=True)
    stay, switch = df[df["Path"].str.startswith("Stay")], df[df["Path"].str.startswith("Switch")]
    c1, c2, c3 = st.columns(3)
    c1.metric("Top rung: staying", f"{stay['Year'].max()} yrs")
    c2.metric("Top rung: switching", f"{switch['Year'].max()} yrs", delta=f"{switch['Year'].max() - stay['Year'].max()} yrs",
              delta_color="inverse")
    c3.metric("Pay at top rung (switching)", money(switch["Salary"].max()),
              delta=money(switch["Salary"].max() - stay["Salary"].max()))
    st.caption("Illustrative model. Titles are a typical ladder at large employers; salaries are anchored to real BLS "
               "percentiles for this job (entry ≈ 25th percentile, top ≈ 90th). The 'switch' path assumes faster promotions "
               "and about 8% higher pay per level from outside offers. These are planning assumptions, not guarantees.")


def live_tab(o, loc):
    if not jobs_api.enabled():
        st.info("Add `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` to the app's Secrets to see live job postings "
                "(keys at developer.adzuna.com).", icon="🔑")
        return
    c1, c2 = st.columns([3, 1.2])
    what = c1.text_input("Search postings for", o["entry_titles"][0], key=f"live_q_{o['title']}")
    c2.markdown(f"<div style='padding-top:30px;color:#6B7080'>in <b>{esc(loc)}</b></div>", unsafe_allow_html=True)

    # Results are kept in this session, so switching tabs or pages never spends another API call.
    store = st.session_state.setdefault("live_results", {})
    key = (what.strip().lower(), loc)
    if key not in store:
        st.caption("Live postings load on request to save API calls. Each search uses 1 call.")
        if st.button(f"🔎 Load live postings for “{what}” in {loc}", type="primary", key=f"load_{key}"):
            try:
                with st.spinner("Fetching live postings…"):
                    store[key] = jobs_api.search_with_count(what, loc, n=20)
            except Exception as e:
                st.warning(f"Couldn't reach the Adzuna jobs API ({e}). If you used all your trial calls, "
                           "the rest of the dashboard still works.")
                return
            st.rerun()
        return
    jobs, total = store[key]

    p, _ = location_pay(o, loc)
    with_pay = [j for j in jobs if j.get("salary_min")]
    mids = [((j["salary_min"] or 0) + (j["salary_max"] or j["salary_min"])) / 2 for j in with_pay]
    m1, m2, m3 = st.columns(3)
    m1.metric("Open postings (last 30 days)", f"{total:,}" if total is not None else "n/a")
    m2.metric(f"BLS median pay · {loc}", money(p["p50"]))
    m3.metric(f"Avg. advertised pay ({len(mids)} postings)", money(sum(mids) / len(mids)) if mids else "n/a")

    left, right = st.columns([1.15, 1], gap="medium")
    with left:
        rows = "".join(f"""<div class="r" style="grid-template-columns:1.7fr 1fr">
            <div><a class="jt" href="{esc(j['url'])}" target="_blank" rel="noopener" style="text-decoration:none">{esc(j['title'])}</a>
            <div class="js">{esc(j['company'])} · {esc(j['location'])} · posted {esc(j['created'])}</div></div>
            <div class="pay" style="font-size:1rem">{esc(jobs_api.salary_text(j))}<span>advertised</span></div></div>"""
                       for j in jobs[:10]) or "<div class='r'>No recent postings found. Try a broader title.</div>"
        st.markdown(f'<div class="sl"><div class="sl-h" style="grid-template-columns:1.7fr 1fr"><div>Recent postings</div>'
                    f'<div>Salary</div></div>{rows}</div>', unsafe_allow_html=True)
    with right:
        if mids:
            fig = go.Figure(go.Histogram(x=mids, xbins=dict(size=10000), marker_color="#B8BDFF",
                                         hovertemplate="%{x}: %{y} postings<extra></extra>"))
            fig.add_vline(x=p["p50"], line_color="#1F2BFF", line_width=3,
                          annotation_text=f"BLS median {k(p['p50'])}", annotation_position="top")
            fig.update_layout(height=380, title=dict(text="Advertised pay in these postings vs. BLS median", font=dict(size=15)),
                              xaxis_title="Advertised salary (midpoint of range)", yaxis_title="Postings",
                              xaxis_tickformat="$,.0f", margin=dict(t=60, l=10, r=10, b=40), showlegend=False, bargap=0.08)
            with st.container(border=True):
                st.plotly_chart(fig, use_container_width=True)
        st.caption("Live data from the Adzuna jobs API. “(est.)” means Adzuna estimated the salary because the posting "
                   "didn't list one. Advertised pay is what employers post today; BLS pay is what workers were actually "
                   "paid in the May 2025 survey.")
