import streamlit as st

from core import agent, gamify, state, theme

SYSTEM = """You are a Career Match agent for college students. Your job: recommend the 4-5 jobs that best fit the student.
Work step by step using your tools:
1. Use search_resume to understand their strongest experiences and skills (if a resume exists).
2. Use list_occupations, then get_occupation_data for promising occupations to check pay, growth, and education.
3. Use search_knowledge_base for career paths by major and skills valued in an AI-shaped job market.\n4. If available, use search_live_jobs for your top picks to check current demand and advertised pay.
Then decide. Ground every claim in the resume, their stated preferences, or tool results. Include at least one
"stretch" option. Respect careers they said they are not interested in.

Final JSON:
{"summary": "2-3 sentences",
 "matches": [{"title": "specific job title", "dataset_title": "matching occupation from list_occupations or null",
   "fit_score": int 0-100, "why_fit": "2-3 sentences citing specific resume items or preferences",
   "gaps": ["skills/experience to build"], "next_steps": ["3 concrete actions this semester"],
   "example_roles": ["2-3 real-world job titles to search for"],
   "live_demand": "one sentence on current postings/pay from search_live_jobs, or null"}]}"""


def render():
    theme.page_header("Career Matches", "A Claude agent reads your resume, quiz results, and preferences, researches real job data with its tools, and recommends the jobs that fit you best.", eyebrow="Discover")
    state.need_resume()

    prefs = st.text_area("Anything specific you want in a job?", placeholder="e.g., want to be technical, client-facing, in Phoenix or Denver")
    if st.button("Find my best-fit careers", type="primary"):
        if not state.ai_ready():
            return
        goal = f"STUDENT PROFILE:\n{state.profile_context(resume_chars=2500)}\n\nEXTRA PREFERENCES: {prefs or 'none'}"
        with st.status("Agent is researching…", expanded=True) as status:
            st.write("Reading your resume, checking BLS job data, searching the knowledge base…")
            try:
                res, trace = agent.run_agent_json(SYSTEM, goal, state.toolbox())
            except Exception as e:
                status.update(label="Agent failed", state="error")
                st.error(f"Something went wrong: {e}")
                return
            status.update(label=f"Done: agent used {len(trace)} tool calls", state="complete", expanded=False)
        st.session_state.matches = (res, trace)
        st.session_state.suggested_titles = list(dict.fromkeys(
            [m.get("dataset_title") for m in res.get("matches", []) if m.get("dataset_title")] + state.suggested_titles()))
        gamify.award("career_matches")

    if st.session_state.get("matches"):
        res, trace = st.session_state.matches
        st.write(res.get("summary", ""))
        for m in res.get("matches", []):
            with st.container(border=True):
                a, b = st.columns([4, 1])
                a.markdown(f"### {m['title']}")
                b.metric("Fit", f"{m.get('fit_score', 0)}%")
                st.write(m.get("why_fit", ""))
                c1, c2, c3 = st.columns(3)
                c1.markdown("**Search for:**\n" + "\n".join(f"- {r}" for r in m.get("example_roles", [])))
                c2.markdown("**Gaps to close:**\n" + "\n".join(f"- {g}" for g in m.get("gaps", [])))
                c3.markdown("**Next steps:**\n" + "\n".join(f"- {s}" for s in m.get("next_steps", [])))
                if m.get("live_demand"):
                    st.caption(f"🟢 Live demand: {m['live_demand']}")
                if m.get("dataset_title"):
                    st.caption(f"📊 Pay and location data available in the Market Dashboard under *{m['dataset_title']}*")
        with st.expander("🔍 Agent trace: see how the agent reached these recommendations"):
            st.markdown(agent.trace_markdown(trace))
    gamify.render_footer()
