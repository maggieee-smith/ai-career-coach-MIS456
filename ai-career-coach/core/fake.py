"""Canned responses for offline UI testing (set CAREER_COACH_FAKE=1). Never used when deployed with keys."""


def text(system, prompt):
    return ("Dear Hiring Team,\n\nI am excited to apply for the Technology Assurance Associate role. As VP of Finance "
            "for my Panhellenic council I manage a large budget and built automated tracking that cut reconciliation "
            "time in half.\n\nSincerely,\nTest Student")


def json_for(system, prompt):
    s = system.lower()
    if "career quiz" in s:
        return {"profile_summary": "You lean Enterprising and Conventional: you like leading and organizing.",
                "riasec_code": "ECI",
                "careers": [{"title": "Technology Consultant", "dataset_title": "Management Analysts", "strength": 88,
                             "why": "Blends leadership with analysis.", "positions": ["Technology Consulting Analyst"],
                             "companies": ["Deloitte", "Accenture"]},
                            {"title": "IT Auditor", "dataset_title": "Accountants and Auditors", "strength": 81,
                             "why": "Structured, detail-oriented.", "positions": ["Technology Assurance Associate"],
                             "companies": ["KPMG", "EY"]}],
                "skills_to_build": ["SQL", "Power BI"]}
    if "resume reviewer" in s:
        return {"overall_score": 78, "summary": "Solid resume; quantify more.",
                "scores": {"Formatting": 85, "Impact & Quantification": 65, "Wording": 75, "Tense & Consistency": 80,
                           "Relevance to Target": 80},
                "strengths": ["Clear education section"],
                "edits": [{"category": "Wording", "original": "Responsible for budget",
                           "suggested": "Managed a $120K budget across 12 chapters", "reason": "Lead with action and numbers"}],
                "missing_keywords": ["SQL", "ITGC"], "formatting_tips": ["Right-align dates"]}
    if "job overview" in s:
        return {"overview": "Analysts help clients solve problems.", "day_to_day": ["Client meetings", "Data analysis"],
                "key_skills": ["Excel", "Communication"],
                "recruiting_timeline": [{"when": "Aug–Oct junior year", "what": "Internship recruiting"}],
                "application_tips": ["Network early"], "entry_titles": ["Analyst"],
                "companies": [{"name": "Deloitte", "why": "Large analyst class", "notes": "Apply via campus"}]}
    if "interview coach evaluating" in s:
        return {"scores": {"Structure": 4, "Relevance": 4, "Specificity": 3, "Impact": 4, "Communication": 4},
                "overall": 3.8, "strengths": ["Clear result"], "improvements": ["Add more detail on your actions"],
                "improved_answer": "Situation… Task… Action… Result…", "follow_up_question": "What would you do differently?"}
    return {}


def agent(system, goal, toolbox, trace):
    import json
    out = toolbox.run("search_knowledge_base", {"query": goal[:200]})
    trace.append({"tool": "search_knowledge_base", "input": {"query": goal[:60]}, "output": out[:600]})
    if "mock interview" in system.lower():
        res = {"interview_style": "Behavioral first round with light technical questions.",
               "questions": [{"type": "Behavioral", "question": "Tell me about a time you led a team.",
                              "why_asked": "Leadership", "source": "interview_questions.md"},
                             {"type": "Technical", "question": "What are ITGCs?", "why_asked": "Core concept",
                              "source": "interview_questions.md"}]}
    else:
        res = {"summary": "Strong fit for analytical business roles.",
               "matches": [{"title": "Technology Consultant", "dataset_title": "Management Analysts", "fit_score": 90,
                            "why_fit": "MIS + leadership", "gaps": ["SQL"], "next_steps": ["Get a cert"],
                            "example_roles": ["Tech Consulting Analyst"]},
                           {"title": "Data Analyst", "dataset_title": "Data Scientists", "fit_score": 80,
                            "why_fit": "Data skills", "gaps": ["Python"], "next_steps": ["Build a project"],
                            "example_roles": ["Business Data Analyst"]}]}
    return json.dumps(res), trace
