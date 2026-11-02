import json

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from core import agent, documents, gamify, llm, rag, speech, state, theme

PLAN_SYSTEM = """You are a mock interview planning agent. Prepare a realistic interview for a college student.
Use your tools:
- If a job posting URL is given, call fetch_job_posting to read it.
- Call search_knowledge_base for questions for this field/role and for company/firm interview style notes
  (our bank is curated from questions candidates report on Glassdoor, Reddit, and career centers).
- Call search_resume to find experiences the interviewer would probe.
Then build the interview. Mix behavioral questions with technical questions appropriate for an entry-level candidate
in this field, following the requested mix. Tailor at least one question to the specific resume and one to the
company. Prefer questions from the knowledge base, adapted to the company; mark ones you wrote as "generated".

Final JSON:
{"interview_style": "2-3 sentences on what this company's interview for this role is typically like",
 "questions": [{"type": "Behavioral|Technical|Company/Fit|Resume", "question": str,
                "why_asked": "what the interviewer is assessing", "source": "knowledge base file name or 'generated'"}]}"""

EVAL_SYSTEM = """You are an interview coach evaluating a college student's spoken answer (transcribed, so ignore minor
transcription errors). Use the RUBRIC context from our knowledge base. Score each dimension 1-5. Be honest and
specific: give positive AND negative feedback. Use details from the student's resume context when suggesting what
example they could have used. Keep the improved answer in the student's voice and based only on facts they gave or
that appear in their resume (use [placeholders] for missing numbers).

Return JSON:
{"scores": {"Structure": int, "Relevance": int, "Specificity": int, "Impact": int, "Communication": int},
 "overall": float (average, 1 decimal),
 "strengths": [2-3 specific positives],
 "improvements": [2-3 specific, actionable fixes],
 "improved_answer": "a stronger version of their answer, ~150-220 words",
 "follow_up_question": "a realistic follow-up an interviewer might ask"}"""


def speak_button(text: str, key: str):
    """Reads the question aloud with the browser's built-in speech synthesis (no API needed)."""
    safe = json.dumps(text)
    components.html(f"""
      <button id="b" style="background:#0C234B;color:white;border:none;padding:6px 14px;border-radius:6px;cursor:pointer;
              font-family:sans-serif">🔊 Hear the interviewer</button>
      <script>
        document.getElementById('b').onclick = () => {{
          const u = new SpeechSynthesisUtterance({safe}); u.rate = 1.0;
          window.speechSynthesis.cancel(); window.speechSynthesis.speak(u);
        }};
      </script>""", height=45)


def render():
    theme.page_header("Mock Interview", "An AI agent builds a tailored interview from the company, job description, your resume, and our question bank. Answer out loud with your microphone and get scored feedback.", eyebrow="Practice")
    iv = st.session_state.get("iv")

    with st.expander("Set up interview", expanded=iv is None):
        c1, c2 = st.columns(2)
        company = c1.text_input("Company", placeholder="e.g., KPMG")
        role = c2.text_input("Role", placeholder="e.g., Technology Assurance Associate")
        url = st.text_input("Job posting link (optional)")
        jd = st.text_area("…or paste the job description (recommended)", height=140)
        c3, c4 = st.columns(2)
        n = c3.slider("Number of questions", 3, 8, 5)
        mix = c4.select_slider("Question mix", ["All behavioral", "Mostly behavioral", "Balanced", "Mostly technical"], "Balanced")
        if st.button("Prepare my interview", type="primary", disabled=not (company and role)):
            if not state.ai_ready():
                return
            state.need_resume("Tip: upload your resume on My Profile so questions are tailored to you.")
            goal = (f"Company: {company}\nRole: {role}\nJob posting URL: {url or 'none'}\n"
                    f"Pasted job description: {jd[:6000] or 'none'}\nNumber of questions: {n}\nMix: {mix}\n\n"
                    f"Student profile (resume is searchable with search_resume):\n{state.profile_context(include_resume=False)}")
            with st.status("Agent is preparing your interview…", expanded=True) as status:
                st.write("Reading the job posting, searching the question bank, scanning your resume…")
                try:
                    plan, trace = agent.run_agent_json(PLAN_SYSTEM, goal, state.toolbox())
                except Exception as e:
                    status.update(label="Agent failed", state="error")
                    st.error(f"Something went wrong: {e}")
                    return
                status.update(label=f"Interview ready: agent used {len(trace)} tool calls", state="complete", expanded=False)
            jd_text = jd
            if not jd_text and url:
                try:
                    jd_text = documents.fetch_url_text(url)
                except Exception:
                    jd_text = ""
            st.session_state.iv = {"company": company, "role": role, "jd": jd_text, "plan": plan, "trace": trace,
                                   "questions": plan.get("questions", [])[:n], "idx": 0, "results": [], "done": False}
            st.rerun()

    if not iv:
        gamify.render_footer()
        return

    st.info(f"**{iv['company']} · {iv['role']}**: {iv['plan'].get('interview_style', '')}")
    with st.expander("🔍 Agent trace: how this interview was built"):
        st.markdown(agent.trace_markdown(iv["trace"]))

    if iv["done"] or iv["idx"] >= len(iv["questions"]):
        summary(iv)
        gamify.render_footer()
        return

    i = iv["idx"]
    q = iv["questions"][i]
    st.progress(i / len(iv["questions"]), text=f"Question {i + 1} of {len(iv['questions'])}")
    with st.container(border=True):
        st.caption(f"{q.get('type', '')} · assesses: {q.get('why_asked', '')}")
        st.markdown(f"### {q['question']}")
        speak_button(q["question"], f"speak{i}")

    audio = st.audio_input("🎙️ Record your answer", key=f"audio_{i}_{len(iv['questions'])}")
    tkey = f"answer_{i}_{len(iv['questions'])}"
    if audio is not None and st.session_state.get(f"_tx_{tkey}") != audio.size:
        with st.spinner("Transcribing…"):
            try:
                st.session_state[tkey] = speech.transcribe(audio.getvalue())
                st.session_state[f"_tx_{tkey}"] = audio.size
            except Exception as e:
                st.error(str(e))
    answer = st.text_area("Your answer (transcribed automatically; you can edit or type instead)", key=tkey, height=160)

    c1, c2, c3 = st.columns([2, 2, 1])
    if c1.button("Submit answer for feedback", type="primary", disabled=not answer.strip()):
        if not state.ai_ready():
            return
        kb = state.kb_index()
        rubric = rag.format_context(kb.search("STAR method scoring rubric interview answer", 3))
        res_idx = state.resume_index()
        resume_ctx = rag.format_context(res_idx.search(q["question"], 3)) if res_idx else "No resume."
        prompt = (f"COMPANY: {iv['company']}\nROLE: {iv['role']}\nJOB DESCRIPTION: {iv['jd'][:3000] or 'n/a'}\n\n"
                  f"QUESTION ({q.get('type')}): {q['question']}\n\nSTUDENT ANSWER:\n{answer}\n\n"
                  f"RUBRIC CONTEXT:\n{rubric}\n\nRELEVANT RESUME SECTIONS:\n{resume_ctx}")
        with st.spinner("Evaluating your answer…"):
            try:
                ev = llm.ask_json(EVAL_SYSTEM, prompt)
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                return
        iv["results"].append({"question": q["question"], "type": q.get("type"), "answer": answer, "eval": ev})
        gamify.award("interview_answer")
        if float(ev.get("overall", 0)) >= 4:
            gamify.award("interview_strong")
        st.rerun()
    if c3.button("Skip"):
        iv["idx"] += 1
        st.rerun()

    last = iv["results"][-1] if iv["results"] and iv["results"][-1]["question"] == q["question"] else None
    if last:
        show_eval(last["eval"])
        b1, b2 = st.columns(2)
        if b1.button("Next question ➡️", type="primary"):
            iv["idx"] += 1
            st.rerun()
        fu = last["eval"].get("follow_up_question")
        if fu and b2.button("Answer the follow-up first"):
            iv["questions"].insert(i + 1, {"type": "Follow-up", "question": fu, "why_asked": "Interviewer follow-up", "source": "generated"})
            iv["idx"] += 1
            st.rerun()
    if st.button("End interview & see summary"):
        iv["done"] = True
        st.rerun()
    gamify.render_footer()


def show_eval(ev):
    scores = ev.get("scores", {})
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Overall", f"{ev.get('overall', 0)}/5")
        for k, v in scores.items():
            st.progress(min(max(int(v), 0), 5) / 5, text=f"{k}: {v}/5")
    with c2:
        st.markdown("**👍 Strengths**\n" + "\n".join(f"- {s}" for s in ev.get("strengths", [])))
        st.markdown("**🛠️ Improve**\n" + "\n".join(f"- {s}" for s in ev.get("improvements", [])))
    with st.expander("✨ See a stronger version of your answer"):
        st.write(ev.get("improved_answer", ""))


def summary(iv):
    st.header("Interview summary")
    res = iv["results"]
    if not res:
        st.write("No answers submitted.")
    else:
        if "_awarded_complete" not in iv:
            gamify.award("interview_complete")
            iv["_awarded_complete"] = True
        df = pd.DataFrame([{**r["eval"].get("scores", {})} for r in res])
        avg = df.mean().round(1).reset_index()
        avg.columns = ["Dimension", "Average score"]
        st.metric("Average overall score", f"{pd.Series([float(r['eval'].get('overall', 0)) for r in res]).mean():.1f}/5")
        fig = px.bar(avg, x="Dimension", y="Average score", range_y=[0, 5], color_discrete_sequence=["#1F2BFF"])
        fig.update_layout(height=320)
        st.plotly_chart(fig, use_container_width=True)
        for r in res:
            with st.expander(f"{r['type']}: {r['question']}  ({r['eval'].get('overall', '?')}/5)"):
                st.markdown(f"**Your answer:** {r['answer']}")
                show_eval(r["eval"])
        transcript = "\n\n".join(f"Q: {r['question']}\nA: {r['answer']}\nScore: {r['eval'].get('overall')}/5\n"
                                 f"Improve: {'; '.join(r['eval'].get('improvements', []))}" for r in res)
        st.download_button("Download transcript & feedback", transcript, "mock_interview.txt")
    if st.button("Start a new interview", type="primary"):
        del st.session_state["iv"]
        st.rerun()
