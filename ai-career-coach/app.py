"""AI Career Coach: MIS 456 Generative AI for Business group project.

Run locally:  streamlit run app.py
"""
import streamlit as st

from core import config, gamify, nav, state, theme
from views import cover_letter, dashboard, home, interview, job_explorer, matches, progress, quiz, resume_review

st.set_page_config(page_title="AI Career Coach", page_icon="assets/icon.svg", layout="wide", initial_sidebar_state="expanded")
theme.apply()

P = {
    "Dashboard": st.Page(home.render, title="Dashboard", icon=":material/home:", url_path="home", default=True),
    "Career Quiz": st.Page(quiz.render, title="Career Quiz", icon=":material/explore:", url_path="quiz"),
    "Career Matches": st.Page(matches.render, title="Career Matches", icon=":material/target:", url_path="matches"),
    "Resume Review": st.Page(resume_review.render, title="Resume Review", icon=":material/description:", url_path="resume"),
    "Cover Letter": st.Page(cover_letter.render, title="Cover Letter", icon=":material/mail:", url_path="cover-letter"),
    "Job Explorer": st.Page(job_explorer.render, title="Job Explorer", icon=":material/work:", url_path="jobs"),
    "Market Dashboard": st.Page(dashboard.render, title="Market Dashboard", icon=":material/monitoring:", url_path="dashboard"),
    "Mock Interview": st.Page(interview.render, title="Mock Interview", icon=":material/mic:", url_path="interview"),
    "My Progress": st.Page(progress.render, title="My Progress", icon=":material/emoji_events:", url_path="progress"),
}
nav.PAGES.update(P)
pg = st.navigation({
    "": [P["Dashboard"]],
    "Discover": [P["Career Quiz"], P["Career Matches"]],
    "Improve": [P["Resume Review"], P["Cover Letter"]],
    "Research": [P["Job Explorer"], P["Market Dashboard"]],
    "Practice": [P["Mock Interview"], P["My Progress"]],
})
pg.run()

# Sidebar is drawn after the page so XP earned on this run shows immediately.
with st.sidebar:
    st.divider()
    idx, name, xp, nxt, prog = gamify.level_info()
    st.markdown(f"**🏆 Level {idx + 1}: {name}**  \n<span style='color:#6B7080;font-size:.85rem'>{xp} XP</span>",
                unsafe_allow_html=True)
    st.progress(prog)
    st.markdown("<span style='font-size:.88rem'>" + ("✅ Resume loaded" if state.resume_text() else "⚠️ No resume yet")
                + "</span>", unsafe_allow_html=True)
    with st.expander("System status"):
        kb = state.kb_index()
        st.markdown(f"- Claude: {'✅' if config.anthropic_key() else '❌ add ANTHROPIC_API_KEY'}")
        st.markdown(f"- OpenAI (voice + embeddings): {'✅' if config.openai_key() else '⚠️ add OPENAI_API_KEY'}")
        st.markdown(f"- Knowledge base: {len(kb.chunks)} chunks · {kb.embedder.backend} embeddings")
        if config.fake_mode():
            st.warning("Offline test mode")
