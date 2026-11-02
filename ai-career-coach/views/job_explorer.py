import pandas as pd
import streamlit as st

from core import data, gamify, llm, rag, state, theme

SYSTEM = """You write a job overview for a college student exploring a career.
Use the retrieved knowledge base context (recruiting timelines, career paths) and the BLS job data provided.
Personalize the application tips to the student's profile. Keep timelines realistic for U.S. undergraduates and say
"typically". Use the student's graduation year to translate timelines into actual months/years when possible.

Return JSON:
{"overview": "3-4 sentences on what the job is", "day_to_day": [5 bullets], "key_skills": [6-8 skills],
 "entry_titles": [4 entry-level titles to search],
 "recruiting_timeline": [{"when": "e.g., Aug–Oct of junior year (2026)", "what": "what happens / what to do"}],  // 4-6 rows in order
 "application_tips": [4 personalized tips],
 "companies": [{"name": str, "why": "why it's a good target", "notes": "program name, location, or recruiting note"}]}  // 6-8 companies"""


def render():
    theme.page_header("Job Explorer", "Description, recruiting timeline, and companies to apply to, using our recruiting knowledge base plus BLS data.", eyebrow="Research")

    suggested = state.suggested_titles()
    options = list(dict.fromkeys(suggested + data.occupation_titles()))
    c1, c2 = st.columns(2)
    pick = c1.selectbox("Pick a career" + (" (your matches are listed first)" if suggested else ""), options)
    custom = c2.text_input("…or type any job title", placeholder="e.g., Technology Assurance Associate")
    title = custom.strip() or pick

    o = data.get_occupation(title)
    if o:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Median pay", f"${o['p50']:,.0f}")
        m2.metric("U.S. jobs", f"{o['employment']:,}")
        m3.metric("Projected growth", f"{o['growth']}%" if o.get("growth") is not None else "n/a")
        m4.metric("Typical education", o["edu"].replace(" degree", ""))
        st.caption(data.SOURCE_NOTE)

    cache = st.session_state.setdefault("job_overviews", {})
    if st.button(f"Generate overview for {title}", type="primary"):
        if not state.ai_ready():
            return
        kb = state.kb_index()
        family = o["family"] if o else title
        ctx = rag.format_context(kb.search(f"recruiting timeline {family} {title}", 3) +
                                 kb.search(f"careers {title} skills", 2))
        prompt = (f"JOB: {title}\nBLS DATA: {data.occupation_summary_text(o) if o else 'not in dataset'}\n\n"
                  f"KNOWLEDGE BASE CONTEXT:\n{ctx}\n\nSTUDENT:\n{state.profile_context(resume_chars=2000)}")
        with st.spinner("Researching this career…"):
            try:
                cache[title] = llm.ask_json(SYSTEM, prompt)
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                return
        gamify.award("job_explore")

    r = cache.get(title)
    if r:
        st.subheader("Overview")
        st.write(r.get("overview", ""))
        a, b = st.columns(2)
        a.markdown("**Day to day**\n" + "\n".join(f"- {x}" for x in r.get("day_to_day", [])))
        b.markdown("**Key skills**\n" + "\n".join(f"- {x}" for x in r.get("key_skills", [])))
        st.markdown("**Entry-level titles to search:** " + ", ".join(r.get("entry_titles", [])))

        st.subheader("🗓️ Recruiting timeline")
        for i, step in enumerate(r.get("recruiting_timeline", []), 1):
            st.markdown(f"**{i}. {step.get('when', '')}** — {step.get('what', '')}")

        st.subheader("🏢 Companies to apply to")
        st.dataframe(pd.DataFrame(r.get("companies", [])).rename(
            columns={"name": "Company", "why": "Why apply", "notes": "Notes"}), hide_index=True, use_container_width=True)

        st.subheader("💡 Tips for you")
        for t in r.get("application_tips", []):
            st.markdown(f"- {t}")
        st.caption("Timelines vary by company and year. Always confirm deadlines on company career pages.")
    gamify.render_footer()
