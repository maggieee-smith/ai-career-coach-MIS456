import pandas as pd
import streamlit as st

from core import gamify, llm, rag, state, theme

SYSTEM = """You are an expert resume reviewer for college students (campus recruiter perspective).
Review the resume using the RESUME GUIDE context retrieved from our knowledge base. Be specific: quote the exact
original text for every edit. Check formatting, wording (action verbs, no "responsible for"), tense (present for
current roles, past for past roles), quantification, consistency, grammar/typos, and relevance to the target role.
Never invent accomplishments; where a number is missing, suggest a placeholder like [X%] for the student to fill in.

Return JSON:
{"overall_score": int 0-100, "summary": "2-3 sentences",
 "scores": {"Formatting": int, "Impact & Quantification": int, "Wording": int, "Tense & Consistency": int, "Relevance to Target": int},
 "strengths": [3 short strings],
 "edits": [{"category": "Wording|Tense|Quantify|Formatting|Grammar|Relevance", "original": "exact text",
            "suggested": "rewritten text", "reason": "short reason"}],   // 6-12 edits, most impactful first
 "missing_keywords": [keywords from the target role/description missing from the resume],
 "formatting_tips": [2-5 layout/format tips]}"""


def render():
    theme.page_header("Resume Review", "Line-by-line suggestions on wording, tense, formatting, and impact, grounded in our resume guide (RAG).", eyebrow="Improve")
    if not state.need_resume():
        gamify.render_footer()
        return

    target = st.text_input("Target role (optional)", value=state.profile().get("targets", ""))
    jd = st.text_area("Paste a job description to check keyword match (optional)", height=120)

    if st.button("Review my resume", type="primary"):
        if not state.ai_ready():
            return
        kb = state.kb_index()
        hits = []
        for q in ["resume bullet points action verbs quantify", "resume tense and wording",
                  "resume format layout ATS", f"resume tailoring for {target or 'business'}"]:
            hits += kb.search(q, 2)
        seen, uniq = set(), []
        for c, s in hits:
            if c.text not in seen:
                seen.add(c.text)
                uniq.append((c, s))
        prompt = (f"RESUME GUIDE CONTEXT:\n{rag.format_context(uniq)}\n\nTARGET ROLE: {target or 'not specified'}\n"
                  f"JOB DESCRIPTION: {jd[:5000] or 'not provided'}\n\nRESUME:\n{state.resume_text()[:8000]}")
        with st.spinner("Reviewing your resume…"):
            try:
                st.session_state.resume_review = llm.ask_json(SYSTEM, prompt, max_tokens=4000)
                st.session_state.resume_review_sources = sorted({c.source + " › " + c.section for c, _ in uniq})
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                return
        gamify.award("resume_review")

    r = st.session_state.get("resume_review")
    if r:
        a, b = st.columns([1, 3])
        a.metric("Overall score", f"{r.get('overall_score', 0)}/100")
        b.write(r.get("summary", ""))
        cols = st.columns(len(r.get("scores", {})) or 1)
        for col, (k, v) in zip(cols, r.get("scores", {}).items()):
            col.metric(k, v)
            col.progress(min(max(int(v), 0), 100) / 100)

        if r.get("strengths"):
            st.markdown("**✅ What's working:** " + " · ".join(r["strengths"]))

        st.subheader("Suggested edits")
        cats = sorted({e.get("category", "Other") for e in r.get("edits", [])})
        pick = st.pills("Filter", cats, selection_mode="multi", default=cats)
        for e in r.get("edits", []):
            if e.get("category") not in (pick or cats):
                continue
            with st.container(border=True):
                st.caption(e.get("category", ""))
                c1, c2 = st.columns(2)
                c1.markdown(f"**Before**  \n:red[{e.get('original', '')}]")
                c2.markdown(f"**After**  \n:green[{e.get('suggested', '')}]")
                st.caption(f"Why: {e.get('reason', '')}")

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Missing keywords")
            st.write(", ".join(r.get("missing_keywords", [])) or "None found.")
        with c2:
            st.subheader("Formatting tips")
            for t in r.get("formatting_tips", []):
                st.markdown(f"- {t}")

        edits_df = pd.DataFrame(r.get("edits", []))
        if not edits_df.empty:
            st.download_button("Download edits (CSV)", edits_df.to_csv(index=False), "resume_edits.csv", "text/csv")
        with st.expander("📚 Knowledge base sections retrieved (RAG)"):
            for s in st.session_state.get("resume_review_sources", []):
                st.markdown(f"- {s}")
    gamify.render_footer()
