"""XP, levels, badges, and unlockable insights. Progress lives in the browser session."""
import streamlit as st

XP_RULES = {
    "upload_resume": (50, "Uploaded your resume"),
    "complete_quiz": (100, "Completed the career quiz"),
    "career_matches": (75, "Generated career matches"),
    "resume_review": (75, "Got resume feedback"),
    "job_explore": (25, "Explored a career"),
    "dashboard": (25, "Studied the job market"),
    "interview_answer": (40, "Answered an interview question"),
    "interview_strong": (60, "Scored 4+ on an interview answer"),
    "interview_complete": (150, "Finished a full mock interview"),
    "cover_letter": (75, "Drafted a cover letter"),
}
# Actions that can earn XP more than once
REPEATABLE = {"interview_answer", "interview_strong", "job_explore", "interview_complete"}

LEVELS = [
    (0, "Career Explorer"),
    (150, "Career Builder"),
    (350, "Interview Ready"),
    (600, "Offer Hunter"),
    (900, "Career Pro"),
    (1300, "Career Coach Legend"),
]

BADGES = {
    "First Steps": lambda s: "upload_resume" in s["done"],
    "Self-Aware": lambda s: "complete_quiz" in s["done"],
    "Polished": lambda s: "resume_review" in s["done"],
    "Data Driven": lambda s: "dashboard" in s["done"],
    "Wordsmith": lambda s: "cover_letter" in s["done"],
    "Mic Drop": lambda s: s["counts"].get("interview_strong", 0) >= 1,
    "Interview Marathon": lambda s: s["counts"].get("interview_answer", 0) >= 10,
    "Full Toolkit": lambda s: len(set(XP_RULES) & s["done"] - {"interview_strong"}) >= 8,
}

# Hidden insights unlocked by level
INSIGHTS = {
    1: ("Salary negotiation 101",
        "For entry-level offers, it is usually reasonable to ask politely whether there is flexibility on base pay, "
        "signing bonus, or start date. Anchor with market data (see the Dashboard tab) and always express enthusiasm first."),
    2: ("The follow-up email",
        "Send a short thank-you within 24 hours that references one specific thing from the conversation. "
        "It keeps you memorable when interviewers compare candidates."),
    3: ("Recruiting insider tip",
        "At many large firms most full-time hires come from the intern class. Treat your internship as a 10-week interview: "
        "ask for feedback at the midpoint and act on it."),
    4: ("Career capital",
        "Early-career moves compound. A role that builds rare, in-demand skills (data + domain expertise, AI fluency) "
        "often beats a slightly higher starting salary."),
    5: ("Legend status",
        "You've used every tool here. Your next step: book a mock interview with your career center or a mentor "
        "and compare their feedback to the AI's."),
}


def _state():
    if "gamify" not in st.session_state:
        st.session_state.gamify = {"xp": 0, "done": set(), "counts": {}, "log": []}
    return st.session_state.gamify


def award(action: str):
    s = _state()
    if action in s["done"] and action not in REPEATABLE:
        return
    pts, label = XP_RULES[action]
    old_level = level_info()[0]
    s["xp"] += pts
    s["done"].add(action)
    s["counts"][action] = s["counts"].get(action, 0) + 1
    s["log"].append(f"+{pts} XP — {label}")
    st.toast(f"+{pts} XP — {label}", icon="⭐")
    new_level = level_info()[0]
    if new_level > old_level:
        st.toast(f"Level up! You're now a {LEVELS[new_level][1]}", icon="🏆")
        st.balloons()


def level_info():
    xp = _state()["xp"]
    idx = max(i for i, (need, _) in enumerate(LEVELS) if xp >= need)
    cur_need = LEVELS[idx][0]
    nxt_need = LEVELS[idx + 1][0] if idx + 1 < len(LEVELS) else None
    progress = 1.0 if nxt_need is None else (xp - cur_need) / (nxt_need - cur_need)
    return idx, LEVELS[idx][1], xp, nxt_need, progress


def earned_badges():
    s = _state()
    return [name for name, rule in BADGES.items() if rule(s)]


def render_footer():
    from core import theme
    idx, name, xp, nxt, progress = level_info()
    badges = earned_badges()
    st.markdown(f"""<div class="cc-footer"><div class="lv">🏆 Level {idx + 1}: {name}</div>
        <div class="bar"><div style="width:{int(progress * 100)}%"></div></div>
        <div class="badges">{xp} XP{f' · {nxt - xp} to next level' if nxt else ' · max level'}</div>
        <div class="badges">{theme.chips(badges) if badges else 'No badges yet. Keep going!'}</div></div>""",
                unsafe_allow_html=True)
