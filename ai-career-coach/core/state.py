"""Shared session helpers used by every page."""
import streamlit as st

from core import config, data, rag
from core.agent import Toolbox


@st.cache_resource(show_spinner="Building the knowledge base index…")
def kb_index() -> rag.VectorIndex:
    return rag.build_knowledge_index()


def resume_text() -> str:
    return st.session_state.get("resume_text", "")


def resume_index():
    txt = resume_text()
    if not txt:
        return None
    if st.session_state.get("_resume_idx_src") != txt:
        st.session_state._resume_idx = rag.build_resume_index(txt, kb_index())
        st.session_state._resume_idx_src = txt
    return st.session_state._resume_idx


def toolbox() -> Toolbox:
    return Toolbox(kb_index(), resume_index())


def profile() -> dict:
    return st.session_state.setdefault("profile", {"major": "", "grad_year": "", "targets": "", "notes": ""})


def profile_context(include_resume: bool = True, resume_chars: int = 6000) -> str:
    p = profile()
    parts = [f"Major: {p.get('major') or 'not given'}", f"Graduation year: {p.get('grad_year') or 'not given'}",
             f"Target jobs/industries: {p.get('targets') or 'not given'}"]
    if p.get("notes"):
        parts.append(f"Other notes: {p['notes']}")
    q = st.session_state.get("quiz_answers")
    if q:
        parts.append(f"Career quiz — interested in: {', '.join(q['interested']) or 'none'}; maybe: "
                     f"{', '.join(q['maybe']) or 'none'}; not interested: {', '.join(q['not_interested']) or 'none'}; "
                     f"motivations: {', '.join(q['motivations'])}; RIASEC scores: {q['riasec']}")
    if include_resume and resume_text():
        parts.append("RESUME:\n" + resume_text()[:resume_chars])
    elif include_resume:
        parts.append("RESUME: (none uploaded)")
    return "\n".join(parts)


def suggested_titles() -> list[str]:
    """Dataset occupations suggested by the quiz or career-match agent (used to pre-fill the dashboard)."""
    titles = st.session_state.get("suggested_titles") or []
    return [t for t in titles if data.get_occupation(t)]


def ai_ready(show: bool = True) -> bool:
    ok = bool(config.anthropic_key()) or config.fake_mode()
    if not ok and show:
        st.error("This feature needs an Anthropic API key. Add `ANTHROPIC_API_KEY` in the app's Secrets (see README).")
    return ok


def need_resume(msg: str = "Upload your resume on the **My Profile** page first for personalized results.") -> bool:
    if not resume_text():
        st.info(msg, icon="📄")
        return False
    return True
