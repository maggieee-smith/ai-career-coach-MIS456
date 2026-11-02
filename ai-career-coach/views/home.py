import streamlit as st

from core import data, documents, gamify, nav, state, theme

TOOLS = [
    ("📝", "Resume Review", "Line-by-line edits for wording, tense, and impact."),
    ("✉️", "Cover Letter", "A tailored draft from your resume and the job post."),
    ("🎤", "Mock Interview", "Answer out loud and get scored feedback."),
    ("🧭", "Career Quiz", "Find where your strengths are most valuable."),
]


def first_name() -> str:
    for line in state.resume_text().splitlines():
        w = line.strip().split()
        if w and w[0].isalpha() and len(w[0]) < 20:
            return w[0].title()
    return ""


def trending_jobs(limit: int = 6) -> list[tuple[str, str]]:
    titles = state.suggested_titles() or [
        o["title"] for o in data.occupations()
        if any(w in (state.profile().get("targets", "") + " " + state.profile().get("major", "")).lower()
               for w in o["family"].lower().split())
    ] or ["Management Analysts", "Accountants and Auditors", "Data Scientists"]
    occs = [data.get_occupation(t) for t in titles if data.get_occupation(t)]
    jobs, i = [], 0
    while len(jobs) < limit and occs and i < 40:
        o = occs[i % len(occs)]
        k = i // len(occs)
        jobs.append((o["entry_titles"][k % len(o["entry_titles"])], o["companies"][k % len(o["companies"])]))
        i += 1
    return jobs


def render():
    # ---------- Hero ----------
    st.markdown("""<div class="cc-hero">
        <div class="cc-eyebrow">Your AI-powered career coach</div>
        <h1>Take Your Career Search To The Next Level.</h1>
        <p>Discover careers that fit you, polish your resume, research real pay data, and practice interviews out loud,
        all in one place, personalized to you.</p></div>""", unsafe_allow_html=True)
    _, b1, b2, _ = st.columns([2.6, 1.6, 1.6, 2.6])
    if b1.button("+ Start Creating", type="primary", use_container_width=True):
        nav.go("Career Quiz")
    if b2.button("Practice Interviews", use_container_width=True):
        nav.go("Mock Interview")

    # ---------- Dashboard (after a resume is added) ----------
    if state.resume_text():
        st.write("")
        st.write("")
        name = first_name()
        st.markdown(f"""<div class="cc-welcome"><h2>👋 Welcome{', ' + theme.esc(name) if name else ''}!</h2>
            <p>What do you want to create today?</p></div>""", unsafe_allow_html=True)
        st.write("")
        cols = st.columns(4)
        for col, (icon, title, desc) in zip(cols, TOOLS):
            with col:
                st.markdown(f"""<div class="cc-tool"><div class="ic">{icon}</div><div class="t">{title}</div>
                    <div class="d">{desc}</div></div>""", unsafe_allow_html=True)
                if st.button("Open", key=f"open_{title}", use_container_width=True):
                    nav.go(title)
        st.write("")
        left, right = st.columns([2, 1])
        with left:
            label = "Trending Jobs for You" if state.suggested_titles() else "Trending Jobs"
            st.markdown(theme.job_rows_html(trending_jobs(), label), unsafe_allow_html=True)
            st.caption("Apply opens a live LinkedIn search for that role. Take the quiz or Career Matches to personalize this list.")
        with right:
            st.markdown("""<div class="cc-promo"><div class="art">🗂️</div>
                <div class="t">Create your own job application</div>
                <div class="d">Turn any job posting into a tailored cover letter and interview prep in minutes.</div>
                </div>""", unsafe_allow_html=True)
            if st.button("Start an application", type="primary", use_container_width=True):
                nav.go("Cover Letter")

    # ---------- Get started: steps + blue panel ----------
    theme.section("Create a job-ready profile quickly and easily.",
                  "Your resume and goals give every tool context. Everything stays private to your browser session.",
                  eyebrow="Get started")
    p = state.profile()
    has_resume = bool(state.resume_text())
    steps = [("01", "Add your resume", "Upload a PDF or Word file, or paste the text."),
             ("02", "Tell us your goals", "Your major and the jobs you're aiming for."),
             ("03", "Take the career quiz", "See where your strengths are most valuable."),
             ("04", "Practice and apply", "Resume feedback, cover letters, and mock interviews.")]
    left, right = st.columns([1, 1.25], gap="large")
    with left:
        active = 0 if not has_resume else (1 if not p.get("targets") else 2)
        st.markdown("".join(
            f"""<div class="cc-step {'active' if i == active else ''}"><span class="num">{n}</span>
            <div class="t">{t}</div><div class="d">{d}</div></div>""" for i, (n, t, d) in enumerate(steps)),
            unsafe_allow_html=True)
        st.write("")
        if st.button("+ Take the Career Quiz", type="primary"):
            nav.go("Career Quiz")
    with right:
        with st.container(key="bluepanel"):
            with st.container(key="inner_resume"):
                st.markdown("**📄 Resume**")
                up = st.file_uploader("Upload your resume (PDF, Word, or text)", type=["pdf", "docx", "txt", "md"])
                if up is not None and st.session_state.get("_uploaded_name") != up.name:
                    try:
                        txt = documents.read_upload(up)
                        if len(txt) < 100:
                            st.warning("We couldn't read much text. If it's a scanned PDF, paste the text instead.")
                        st.session_state.resume_text = txt
                        st.session_state._uploaded_name = up.name
                        gamify.award("upload_resume")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Couldn't read that file: {e}")
                pasted = st.text_area("…or paste your resume text", value=state.resume_text(), height=140)
                if pasted != state.resume_text():
                    st.session_state.resume_text = pasted
                    if pasted.strip():
                        gamify.award("upload_resume")
                    st.rerun()
                if has_resume:
                    st.success(f"Resume loaded: {len(state.resume_text().split())} words, "
                               f"split into {len(state.resume_index().chunks)} searchable section(s) for RAG.")
            st.write("")
            with st.container(key="inner_goals"):
                st.markdown("**🎯 Goals**")
                c1, c2 = st.columns(2)
                p["major"] = c1.text_input("Major(s)", p.get("major", ""), placeholder="e.g., MIS and Finance")
                p["grad_year"] = c2.text_input("Graduation year", p.get("grad_year", ""), placeholder="e.g., 2027")
                p["targets"] = st.text_input("Jobs or industries you're targeting", p.get("targets", ""),
                                             placeholder="e.g., technology consulting, IT audit")
                p["notes"] = st.text_input("Anything else? (locations, goals)", p.get("notes", ""))

    # ---------- Stats ----------
    st.write("")
    st.write("")
    stats = [("13", "Careers with real BLS pay data"), ("50", "States mapped by pay & jobs"),
             ("8", "AI-powered career tools"), ("2", "Autonomous AI agents")]
    cols = st.columns(4)
    for col, (n, l) in zip(cols, stats):
        col.markdown(f'<div class="cc-stat"><div class="n">{n}</div><div class="l">{l}</div></div>', unsafe_allow_html=True)

    st.write("")
    with st.expander("How this app uses AI (RAG, agents, speech, real data)"):
        st.markdown("""
- **RAG (retrieval-augmented generation):** A curated knowledge base (interview question bank, recruiting timelines,
  resume and cover letter guides, career paths by major, interview rubric) and *your resume* are split into chunks and
  embedded as vectors. Each feature retrieves the most relevant chunks and gives them to Claude, so answers are grounded
  in our sources instead of generic.
- **Agents:** *Career Matches* and *Mock Interview* use a Claude agent that chooses its own tools (search the knowledge
  base, search your resume, look up BLS job data, fetch a job posting) over several steps. Each page shows the agent's trace.
- **Real data:** Pay percentiles, state-by-state wages, and employment come from the U.S. Bureau of Labor Statistics.
- **Speech-to-text:** The mock interview records your spoken answer and transcribes it with OpenAI Whisper.
- **AI-assisted coding:** The app itself was built with AI coding tools.
""")
        if has_resume:
            st.markdown("**Extracted resume text:**")
            st.text(state.resume_text()[:3000])
    gamify.render_footer()
