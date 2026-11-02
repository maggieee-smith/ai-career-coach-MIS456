import streamlit as st

from core import gamify, theme


def render():
    theme.page_header("My Progress", "Earn XP by using each tool, level up, collect badges, and unlock hidden career insights.", eyebrow="Your journey")
    idx, name, xp, nxt, progress = gamify.level_info()
    c1, c2, c3 = st.columns(3)
    c1.metric("Level", f"{idx + 1}: {name}")
    c2.metric("Total XP", xp)
    c3.metric("Badges", f"{len(gamify.earned_badges())}/{len(gamify.BADGES)}")
    st.progress(progress, text=f"{nxt - xp} XP to Level {idx + 2}" if nxt else "Max level!")

    st.subheader("Milestones")
    s = gamify._state()
    for action, (pts, label) in gamify.XP_RULES.items():
        done = action in s["done"]
        st.markdown(f"{'✅' if done else '⬜'} {label} (**+{pts} XP**)" + (" · repeatable" if action in gamify.REPEATABLE else ""))

    st.subheader("Badges")
    cols = st.columns(4)
    earned = set(gamify.earned_badges())
    for i, b in enumerate(gamify.BADGES):
        cols[i % 4].markdown(f"{'🎖️' if b in earned else '🔒'} **{b}**")

    st.subheader("Unlocked insights")
    for lvl, (title, body) in gamify.INSIGHTS.items():
        if idx >= lvl:
            st.success(f"**{title}**: {body}")
        else:
            st.markdown(f"🔒 *Reach Level {lvl + 1} to unlock: {title}*")

    if s["log"]:
        with st.expander("XP history"):
            for line in reversed(s["log"]):
                st.markdown(f"- {line}")
    st.caption("Progress is saved for this browser session.")
