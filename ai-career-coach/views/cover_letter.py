import streamlit as st

from core import documents, gamify, llm, rag, state, theme

SYSTEM = """You write tailored cover letters for college students. Follow the COVER LETTER GUIDE context exactly
(structure, 250-400 words, specific "why this company", no clichés). Use ONLY facts found in the student's resume
or LinkedIn text; never invent experience, numbers, or names. Pick the 2-3 resume experiences that best match the
job description's top requirements. Output only the letter text (with greeting and sign-off using the student's
name from the resume if available). No commentary."""


def render():
    theme.page_header("Cover Letter Generator", "Combines your resume, the job description, and optionally your LinkedIn profile into a tailored draft.", eyebrow="Improve")
    state.need_resume()

    c1, c2 = st.columns(2)
    company = c1.text_input("Company")
    role = c2.text_input("Role")
    url = st.text_input("Job description link")
    jd = st.text_area("…or paste the job description (use this if the link doesn't load)", height=150)
    linkedin = st.text_area("Paste your LinkedIn 'About' and experience sections (optional)", height=100,
                            help="LinkedIn blocks automated access, so paste the text rather than the link.")
    c3, c4 = st.columns(2)
    manager = c3.text_input("Hiring manager / recruiter name (optional)")
    tone = c4.selectbox("Tone", ["Professional (Big 4, banks, government)", "Warm & enthusiastic (startups, agencies, consumer brands)", "Concise & direct"])

    if st.button("Write my cover letter", type="primary", disabled=not (company and role)):
        if not state.ai_ready():
            return
        jd_text = jd
        if not jd_text and url:
            try:
                with st.spinner("Reading the job posting…"):
                    jd_text = documents.fetch_url_text(url)
            except Exception as e:
                st.warning(f"Couldn't read the link ({e}). Paste the description for best results; continuing without it.")
                jd_text = ""
        kb = state.kb_index()
        guide = rag.format_context(kb.search("cover letter structure style rules", 3))
        res_idx = state.resume_index()
        best = rag.format_context(res_idx.search(jd_text[:1500] or role, 4)) if res_idx else ""
        prompt = (f"COMPANY: {company}\nROLE: {role}\nADDRESS TO: {manager or 'Hiring Team'}\nTONE: {tone}\n\n"
                  f"JOB DESCRIPTION:\n{jd_text[:6000] or 'not provided: infer typical requirements for this role'}\n\n"
                  f"COVER LETTER GUIDE:\n{guide}\n\nMOST RELEVANT RESUME SECTIONS (retrieved):\n{best}\n\n"
                  f"FULL RESUME:\n{state.resume_text()[:6000]}\n\nLINKEDIN:\n{linkedin[:3000] or 'not provided'}")
        with st.spinner("Writing your draft…"):
            try:
                st.session_state.cover_letter = llm.ask(SYSTEM, prompt, max_tokens=1500, temperature=0.6)
                st.session_state.cover_letter_name = f"Cover_Letter_{company.replace(' ', '_')}"
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                return
        gamify.award("cover_letter")

    if st.session_state.get("cover_letter"):
        st.subheader("Your draft")
        txt = st.text_area("Edit freely", st.session_state.cover_letter, height=420, key=f"cl_edit_{hash(st.session_state.cover_letter)}")
        st.caption(f"{len(txt.split())} words · Always proofread and personalize before sending.")
        name = st.session_state.get("cover_letter_name", "Cover_Letter")
        d1, d2 = st.columns(2)
        d1.download_button("Download Word (.docx)", documents.make_docx(txt), f"{name}.docx",
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        d2.download_button("Download text (.txt)", txt, f"{name}.txt")
    gamify.render_footer()
