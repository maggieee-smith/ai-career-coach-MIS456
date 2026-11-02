import json

import plotly.graph_objects as go
import streamlit as st

from core import data, gamify, llm, rag, state, theme

MAJOR_CAREERS = {
    "Management Information Systems (MIS)": ["Technology Consultant", "IT Auditor / Technology Assurance", "Business Analyst",
                                             "Data Analyst", "Cybersecurity Analyst", "Database Administrator", "Product Analyst"],
    "Finance": ["Financial Analyst (FP&A)", "Investment Banking Analyst", "Wealth Management Advisor", "Credit / Risk Analyst",
                "Corporate Treasury", "Management Consultant"],
    "Accounting": ["Audit Associate", "Tax Associate", "Risk Advisory Consultant", "Forensic Accountant", "Corporate Accountant"],
    "Marketing": ["Marketing Analyst", "Brand Assistant", "Digital Marketing Specialist", "Market Research Analyst",
                  "Social Media Manager", "Sales Representative"],
    "Communications / Journalism": ["PR Specialist", "Communications Coordinator", "Content Strategist",
                                    "Social Media Specialist", "Corporate Communications"],
    "Management / Business Administration": ["Management Consultant", "Operations Analyst", "HR Specialist",
                                             "Project Coordinator", "Sales"],
    "Economics": ["Economic Consultant", "Financial Analyst", "Data Analyst", "Policy Analyst"],
    "Computer Science": ["Software Engineer", "Data Engineer", "Machine Learning Engineer", "Cybersecurity Engineer"],
    "Data Science / Statistics": ["Data Scientist", "Data Analyst", "Actuarial Analyst", "BI Analyst"],
    "Psychology": ["HR Specialist / Recruiter", "Market Research Analyst", "UX Researcher", "Counselor (grad degree)"],
    "Nursing": ["Registered Nurse", "Specialty Nurse", "Nurse Informatics"],
    "Engineering": ["Design Engineer", "Test Engineer", "Systems Engineer", "Technical Consultant"],
}

MOTIVATIONS = ["High earning potential", "Work-life balance", "Helping people directly", "Creativity",
               "Stability & structure", "Variety & travel", "Building things / technical mastery",
               "Prestige & fast advancement", "Remote / flexible work", "Social impact"]

# Scenario questions in the style of the O*NET Interest Profiler (Holland RIASEC model).
SCENARIOS = [
    ("Your group project is due Friday and nobody has started. You…", [
        ("Draft a plan, assign roles, and run the check-ins", "E"),
        ("Dive into the research and analysis no one else wants to do", "I"),
        ("Make the slides look great and write the story", "A"),
        ("Check in on teammates to see what's going on and keep morale up", "S"),
        ("Set up a shared tracker with deadlines so nothing slips", "C"),
        ("Build the actual model, prototype, or spreadsheet", "R")]),
    ("A manager hands you a messy dataset. Your first instinct is to…", [
        ("Find the patterns and figure out *why* they happen", "I"),
        ("Clean it and organize it into a clear, reliable system", "C"),
        ("Turn it into a compelling visual story", "A"),
        ("Use it to convince leadership to make a decision", "E"),
        ("Ask who is affected by it and how to help them", "S"),
        ("Build a tool that automates the whole process", "R")]),
    ("On a free Saturday you'd most enjoy…", [
        ("Fixing, building, or working with your hands", "R"), ("Going down a rabbit hole on a complex topic", "I"),
        ("Creating art, music, videos, or content", "A"), ("Volunteering or helping a friend with something big", "S"),
        ("Planning an event or working on a side hustle", "E"), ("Organizing your space, calendar, or finances", "C")]),
    ("Your ideal work environment is…", [
        ("Hands-on: a lab, field site, or workshop", "R"), ("Quiet and focused, solving hard problems", "I"),
        ("Creative and flexible, with room for new ideas", "A"), ("Collaborative, working closely with people I help", "S"),
        ("Fast-paced and competitive with big goals", "E"), ("Structured, with clear expectations and processes", "C")]),
    ("Which compliment would mean the most to you?", [
        ("“You're so dependable and precise.”", "C"), ("“You're a natural leader.”", "E"),
        ("“You really care about people.”", "S"), ("“That's so creative!”", "A"),
        ("“You're brilliant at figuring things out.”", "I"), ("“You can fix anything.”", "R")]),
    ("Two teammates strongly disagree. You…", [
        ("Listen to both and help them find common ground", "S"), ("Make the call so the team can move forward", "E"),
        ("Look at the evidence to decide who's right", "I"), ("Go back to the agreed rules and process", "C"),
        ("Propose a creative third option", "A"), ("Suggest testing both ideas quickly and seeing what works", "R")]),
    ("Which class assignment sounds best?", [
        ("Pitching a strategy in a case competition", "E"), ("Building a working app or device", "R"),
        ("Researching an unsolved problem", "I"), ("Designing a brand campaign", "A"),
        ("Running a peer mentoring program", "S"), ("Auditing a company's financial records", "C")]),
    ("Which job offer sounds most appealing?", [
        ("Stable salary and predictable hours", "C"), ("High commission/bonus upside", "E"),
        ("A meaningful mission helping my community", "S"), ("Creative freedom on every project", "A"),
        ("Cutting-edge technical problems", "I"), ("Hands-on work out in the field", "R")]),
    ("When you learn a new software tool, you…", [
        ("Explore how it works under the hood", "I"), ("Follow a structured tutorial step by step", "C"),
        ("Just start building something with it", "R"), ("Teach it to a friend once you get it", "S"),
        ("Figure out how it can give you an edge", "E"), ("Use it to make something original", "A")]),
    ("In 10 years, you want to be known as…", [
        ("The expert people bring their hardest questions to", "I"), ("A leader who built a team or business", "E"),
        ("A creator with a recognizable body of work", "A"), ("A mentor who changed people's lives", "S"),
        ("The reliable go-to who keeps everything running", "C"), ("A builder who made real things", "R")]),
]
RIASEC_NAMES = {"R": "Realistic (Doer)", "I": "Investigative (Thinker)", "A": "Artistic (Creator)",
                "S": "Social (Helper)", "E": "Enterprising (Persuader)", "C": "Conventional (Organizer)"}

SYSTEM = """You are an expert college career counselor scoring a career quiz.
Use the student's major, career interest ratings, motivations, RIASEC interest scores (Holland codes), resume, and the
retrieved knowledge-base context. Respect careers they marked "not interested" (don't recommend them unless the
evidence is overwhelming, and say so). Strength ratings (0-100) reflect how valuable the student's skills, interests,
and experience would be in that career.

Return JSON:
{"profile_summary": "2-3 sentences, second person",
 "riasec_code": "top 3 letters",
 "careers": [{"title": str, "dataset_title": one of the DATASET OCCUPATIONS that best matches or null, "strength": int,
   "why": "1-2 sentences citing their quiz answers/resume", "positions": [3 entry-level job titles],
   "companies": [4-6 companies that hire for this]}],   // 5-6 careers sorted by strength
 "skills_to_build": [4-5 specific skills or certifications]}"""


def render():
    theme.page_header("Career Quiz", "Find where your skills and interests would make you most valuable. Questions follow the Holland RIASEC interest model used by the U.S. Department of Labor's O*NET Interest Profiler.", eyebrow="Discover")

    p = state.profile()
    st.subheader("1. Your major")
    majors = list(MAJOR_CAREERS) + ["Other"]
    major = st.selectbox("Major", majors, index=None, placeholder="Choose your major")
    if major == "Other":
        major = st.text_input("Type your major")
    if major:
        p["major"] = p.get("major") or major

    careers = MAJOR_CAREERS.get(major, [])
    ratings = {}
    if careers:
        st.subheader("2. Careers associated with your major")
        st.write("How do you feel about each one right now?")
        for c in careers:
            col1, col2 = st.columns([2, 3])
            col1.markdown(f"**{c}**")
            with col2:
                ratings[c] = st.segmented_control(c, ["Interested", "Maybe", "Not interested"], key=f"rate_{c}",
                                                  label_visibility="collapsed")
    extra = st.text_input("Any other careers you're curious about? (comma separated)")

    st.subheader("3. What motivates you?")
    motivations = st.multiselect("Pick up to 3", MOTIVATIONS, max_selections=3)

    st.subheader("4. Scenarios")
    answers = []
    for i, (q, opts) in enumerate(SCENARIOS):
        choice = st.radio(f"**{i + 1}. {q}**", [o for o, _ in opts], index=None, key=f"scn_{i}")
        if choice:
            answers.append(dict(opts)[choice])

    done = len(answers)
    st.progress(done / len(SCENARIOS), text=f"{done}/{len(SCENARIOS)} scenarios answered")

    if st.button("See my results", type="primary", disabled=done < len(SCENARIOS) or not major):
        if not state.ai_ready():
            return
        counts = {k: answers.count(k) for k in "RIASEC"}
        riasec = {k: round(100 * v / len(answers)) for k, v in counts.items()}
        interested = [c for c, r in ratings.items() if r == "Interested"] + [e.strip() for e in extra.split(",") if e.strip()]
        st.session_state.quiz_answers = {
            "major": major, "interested": interested,
            "maybe": [c for c, r in ratings.items() if r == "Maybe"],
            "not_interested": [c for c, r in ratings.items() if r == "Not interested"],
            "motivations": motivations, "riasec": riasec}
        kb = state.kb_index()
        ctx = rag.format_context(kb.search(f"careers for {major} {' '.join(motivations)}", 3) +
                                 kb.search("RIASEC interest model careers", 2))
        prompt = (f"STUDENT:\n{state.profile_context()}\n\nDATASET OCCUPATIONS: {json.dumps(data.occupation_titles())}"
                  f"\n\nKNOWLEDGE BASE CONTEXT:\n{ctx}")
        with st.spinner("Analyzing your answers…"):
            try:
                st.session_state.quiz_result = llm.ask_json(SYSTEM, prompt)
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                return
        res = st.session_state.quiz_result
        st.session_state.suggested_titles = [c.get("dataset_title") for c in res.get("careers", []) if c.get("dataset_title")]
        gamify.award("complete_quiz")

    if st.session_state.get("quiz_result"):
        show_results(st.session_state.quiz_result, st.session_state.quiz_answers["riasec"])
    gamify.render_footer()


def show_results(res, riasec):
    st.divider()
    st.header("Your results")
    left, right = st.columns([2, 3])
    with left:
        cats = list(RIASEC_NAMES)
        fig = go.Figure(go.Scatterpolar(r=[riasec[c] for c in cats] + [riasec[cats[0]]],
                                        theta=[RIASEC_NAMES[c] for c in cats] + [RIASEC_NAMES[cats[0]]],
                                        fill="toself", line_color="#1F2BFF"))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(riasec.values()) + 10])),
                          showlegend=False, height=340, margin=dict(l=40, r=40, t=30, b=30))
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown(f"### Interest code: **{res.get('riasec_code', '')}**")
        st.write(res.get("profile_summary", ""))
        if res.get("skills_to_build"):
            st.markdown("**Skills to build:** " + ", ".join(res["skills_to_build"]))

    st.subheader("Career strength ratings")
    for c in res.get("careers", []):
        with st.container(border=True):
            a, b = st.columns([3, 1])
            a.markdown(f"#### {c['title']}")
            b.metric("Strength", f"{c['strength']}/100")
            st.progress(min(max(c["strength"], 0), 100) / 100)
            st.write(c.get("why", ""))
            st.markdown(f"**Positions:** {', '.join(c.get('positions', []))}  \n"
                        f"**Companies hiring:** {', '.join(c.get('companies', []))}")
    st.info("Next: open **Career Matches** for a deeper agent-based analysis, or **Market Dashboard** to compare pay and locations.")
