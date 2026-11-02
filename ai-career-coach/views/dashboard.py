import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core import data, gamify, state, theme

COLORS = theme.CHART


def money(v):
    return f"${v:,.0f}" if pd.notna(v) and v else "n/a"


def render():
    theme.page_header("Market Dashboard", "Compare pay, locations, education, and career paths using real U.S. Bureau of Labor Statistics data.", eyebrow="Research")
    st.caption(data.SOURCE_NOTE)
    gamify.award("dashboard")

    all_titles = data.occupation_titles()
    default = state.suggested_titles()[:4] or ["Management Analysts", "Accountants and Auditors", "Software Developers"]
    jobs = st.multiselect("Compare jobs (your matches are pre-selected)", all_titles, default=default)
    if not jobs:
        st.info("Pick at least one job.")
        gamify.render_footer()
        return

    tab1, tab2, tab3, tab4 = st.tabs(["💰 Pay ranges", "🗺️ Where the jobs are", "🎓 Education & experience", "📈 Career trajectory"])

    with tab1:
        pay_tab(jobs)
    with tab2:
        map_tab(jobs)
    with tab3:
        edu_tab(jobs)
    with tab4:
        trajectory_tab(jobs)
    gamify.render_footer()


def pay_tab(jobs):
    df = data.pay_table(jobs)
    fig = go.Figure()
    for i, r in df.iterrows():
        y = r["Job"]
        fig.add_trace(go.Scatter(x=[r["Low (10th pct)"], r["High (90th pct)"]], y=[y, y], mode="lines",
                                 line=dict(color="#E3E5F5", width=10), showlegend=False, hoverinfo="skip"))
        if pd.notna(r["25th pct"]) and pd.notna(r["75th pct"]):
            fig.add_trace(go.Scatter(x=[r["25th pct"], r["75th pct"]], y=[y, y], mode="lines",
                                     line=dict(color="#B8BDFF", width=10), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=[r["Median"]], y=[y], mode="markers", marker=dict(color="#1F2BFF", size=14, symbol="diamond"),
                                 name="Median", showlegend=i == 0, hovertemplate="Median $%{x:,.0f}<extra></extra>"))
        if pd.notna(r["Mean"]):
            fig.add_trace(go.Scatter(x=[r["Mean"]], y=[y], mode="markers", marker=dict(color="#16181D", size=10),
                                     name="Mean", showlegend=i == 0, hovertemplate="Mean $%{x:,.0f}<extra></extra>"))
    fig.update_layout(height=120 + 70 * len(df), xaxis_title="Annual pay (USD)", xaxis_tickformat="$,.0f",
                      margin=dict(l=10, r=10, t=30, b=40), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Light bar = 10th to 90th percentile (low to high). Darker bar = middle 50% (25th–75th), where published.")

    show = df.copy()
    for c in ["Low (10th pct)", "25th pct", "Median", "Mean", "75th pct", "High (90th pct)"]:
        show[c] = show[c].map(money)
    show["U.S. jobs"] = show["U.S. jobs"].map(lambda v: f"{v:,}")
    st.dataframe(show, hide_index=True, use_container_width=True)
    st.caption("BLS publishes percentiles rather than true minimums/maximums or a mode, so the 10th and 90th percentiles "
               "stand in for low and high pay. Some percentiles aren't published for every job.")


def map_tab(jobs):
    sw = data.state_wages()
    job = st.selectbox("Job", jobs, key="map_job")
    sub = sw[sw["occupation"] == job]
    full = sub["employment"].notna().sum() > 20
    metric = st.radio("Color states by", ["Number of jobs", "Median pay"] if full else ["Median pay"], horizontal=True)
    col = "employment" if metric == "Number of jobs" else "median"
    fig = px.choropleth(sub, locations="abbr", locationmode="USA-states", scope="usa", color=col,
                        color_continuous_scale=[[0, "#EEF0FF"], [1, "#1F2BFF"]] if col == "employment" else [[0, "#F1EEFF"], [1, "#5B3FD6"]], hover_name="state",
                        hover_data={"abbr": False, "employment": ":,", "median": ":$,.0f"},
                        labels={"employment": "Jobs", "median": "Median pay"})
    fig.update_layout(height=480, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)
    if not full:
        st.info("For this job, BLS (via WageDex) publishes only the top-paying states, so only those are colored.")
    top = sub.sort_values(col, ascending=False).head(10)[["state", "employment", "median", "mean"]]
    top.columns = ["State", "Jobs", "Median pay", "Mean pay"]
    for c in ["Median pay", "Mean pay"]:
        top[c] = top[c].map(money)
    top["Jobs"] = top["Jobs"].map(lambda v: f"{v:,.0f}" if pd.notna(v) else "n/a")
    st.markdown(f"**Top states by {metric.lower()}**")
    st.dataframe(top, hide_index=True, use_container_width=True)


def edu_tab(jobs):
    rows = []
    for t in jobs:
        o = data.get_occupation(t)
        rows.append({"Job": o["title"], "Typical entry education": o["edu"], "Related work experience required": o["exp"],
                     "Projected growth 2024–34": f"{o['growth']}%" if o.get("growth") is not None else "n/a",
                     "U.S. jobs": f"{o['employment']:,}"})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    edu_rank = {"High school diploma": 1, "Associate's degree": 2, "Bachelor's degree": 3, "Master's degree": 4, "Doctoral degree": 5}
    exp_rank = {"None": 0, "Less than 5 years": 1, "5 years or more": 2}
    plot = pd.DataFrame([{"Job": r["Job"], "Education": edu_rank.get(r["Typical entry education"], 3),
                          "Experience": exp_rank.get(r["Related work experience required"], 0)} for r in rows])
    c1, c2 = st.columns(2)
    f1 = px.bar(plot, x="Job", y="Education", color="Job", color_discrete_sequence=COLORS, title="Typical education level")
    f1.update_yaxes(tickvals=list(edu_rank.values()), ticktext=list(edu_rank.keys()), range=[0, 5.5])
    f1.update_layout(showlegend=False, xaxis_title=None, height=380)
    c1.plotly_chart(f1, use_container_width=True)
    f2 = px.bar(plot, x="Job", y="Experience", color="Job", color_discrete_sequence=COLORS, title="Prior work experience expected")
    f2.update_yaxes(tickvals=list(exp_rank.values()), ticktext=["None (entry level)", "< 5 years", "5+ years"], range=[0, 2.3])
    f2.update_layout(showlegend=False, xaxis_title=None, height=380)
    c2.plotly_chart(f2, use_container_width=True)
    st.caption("Source: BLS Occupational Outlook Handbook. 'None' means new grads can enter directly; internships still help a lot.")


def trajectory_tab(jobs):
    job = st.selectbox("Job", jobs, key="traj_job")
    df = data.career_trajectory(job)
    fig = px.line(df, x="Year", y="Salary", color="Path", markers=True, text="Title",
                  color_discrete_sequence=["#16181D", "#1F2BFF"], line_shape="hv")
    fig.update_traces(textfont_size=11)
    fig.for_each_trace(lambda t: t.update(textposition="bottom right" if t.name.startswith("Stay") else "top left"))
    fig.update_layout(height=520, yaxis_tickformat="$,.0f", xaxis_title="Years after graduation",
                      legend=dict(orientation="h", y=1.08), margin=dict(t=40))
    st.plotly_chart(fig, use_container_width=True)
    stay, switch = df[df["Path"].str.startswith("Stay")], df[df["Path"].str.startswith("Switch")]
    c1, c2 = st.columns(2)
    c1.metric("Years to top rung: staying", f"{stay['Year'].max()} yrs")
    c2.metric("Years to top rung: switching", f"{switch['Year'].max()} yrs",
              delta=f"{switch['Year'].max() - stay['Year'].max()} yrs", delta_color="inverse")
    st.caption("Illustrative model. Titles are a typical ladder at large employers; salaries are anchored to real BLS "
               "percentiles for this job (entry ≈ 25th percentile, top ≈ 90th). The 'switch' path assumes faster promotions "
               "and about 8% higher pay per level from outside offers. These are planning assumptions, not guarantees. "
               "Switching also has costs (lost bonuses/vesting, rebuilding reputation).")
