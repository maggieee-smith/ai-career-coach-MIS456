# 🎓 AI Career Coach
MIS 456 Generative AI for Business: Group Assignment 2

A web app that helps college students find careers that fit them, strengthen their resume, research the job
market, and practice interviews out loud. Built with Streamlit, Claude (Anthropic), and OpenAI Whisper.

---

## Features

| # | Feature | Page | AI technique |
|---|---------|------|--------------|
| 1A | Resume dropbox: upload PDF/Word or paste; becomes context for every feature | My Profile | RAG (resume is chunked + embedded) |
| 1B | Career quiz: major → associated careers (interested/maybe/not), motivations, 10 RIASEC behavioral scenarios → strength ratings, positions, companies | Career Quiz | RAG + structured LLM output |
| 2A | Career suggestions: agent researches resume + BLS data + knowledge base | Career Matches | **Agent** (tool use) |
| 2B | Resume suggestions: line-by-line before/after edits (wording, tense, formatting, quantification), keyword gaps | Resume Review | RAG (resume guide) |
| 3A | Job overview: description, recruiting timeline, companies to apply to | Job Explorer | RAG (recruiting timelines) + BLS data |
| 3B | Dashboard: pay ranges (10th/25th/median/mean/75th/90th), U.S. heat map, education & experience, career trajectory (stay vs. switch companies) | Market Dashboard | Real BLS data |
| 4A | Mock interview: company + job description → tailored behavioral & technical questions; answer by **microphone**; scored feedback (positive and negative), improved answer, follow-ups | Mock Interview | **Agent** + RAG + speech-to-text |
| 4B | Cover letter generator: resume + job link/description + optional LinkedIn → editable draft, Word download | Cover Letter | RAG |
| 3C | Live job postings: current openings, advertised salaries vs. BLS median, real Apply links | Market Dashboard (Live Job Postings tab) | Adzuna jobs API |
| Bonus | Gamification: XP, levels, badges, milestones, unlockable hidden insights | Every page + My Progress | — |

## How the AI works (talking points for grading criterion #1)

**RAG.** `knowledge/` holds our curated knowledge base: interview question bank, recruiting timelines, resume guide,
cover letter guide, career paths by major, interview scoring rubric. At startup each file is split into chunks and
embedded with OpenAI `text-embedding-3-small` (TF-IDF fallback if no OpenAI key). The student's resume is chunked and
embedded the same way. Each feature embeds its question, retrieves the most similar chunks (cosine similarity), and
puts them in Claude's prompt. Pages show which sources were retrieved. Code: `core/rag.py`.

**Agents.** `core/agent.py` implements a tool-using agent loop with Claude's tool-use API. The agent can call
`search_knowledge_base`, `search_resume`, `list_occupations`, `get_occupation_data`, `search_live_jobs` (Adzuna), and `fetch_job_posting`, observe
the results, and decide what to do next until it can answer. Used for **Career Matches** and **Mock Interview
preparation**. Both pages have an "Agent trace" expander showing each step, which is good to show in the demo.

**Speech-to-text.** The mock interview records the answer in the browser (`st.audio_input`) and transcribes it with
OpenAI Whisper (`core/speech.py`). Questions can be read aloud with the browser's built-in voice.

**AI-assisted coding.** The app was built with Claude as a coding assistant.

## Data sources
- Pay percentiles, U.S. employment, and state-by-state wages: U.S. Bureau of Labor Statistics, OEWS, May 2025,
  as republished by WageDex. Full 50-state tables are included for Management Analysts, Accountants & Auditors,
  Software Developers, and Registered Nurses; the other occupations have national data plus their top-paying states.
- Typical education and experience: BLS Occupational Outlook Handbook.
- Live job postings: Adzuna jobs API. The free trial allows only 25 calls, so postings load only when the user clicks **Load live postings** (exactly 1 call per search; results are kept for the session). With a paid plan, add `ADZUNA_FULL = "1"` to Secrets to also show live postings on the home page and let the Career Matches agent search them. Salaries marked "(est.)" are Adzuna estimates for postings that didn't list pay.
- Career trajectory chart: illustrative model. Salaries are anchored to real BLS percentiles; promotion years and
  the job-switching premium are labeled assumptions.
- BLS doesn't publish true minimum, maximum, or mode, so the dashboard uses the 10th and 90th percentiles as low and high.

## Deploy (about 15 minutes, free)

**1. Put the code on GitHub**
1. On github.com click **New repository**, name it `ai-career-coach`, make it **Public**, and click Create.
2. Click **uploading an existing file**, then drag in everything from the unzipped folder: `app.py`,
   `requirements.txt`, `README.md`, and the `core`, `views`, `data`, `knowledge`, `assets` folders. Commit.
3. Also upload the `.streamlit` folder (theme settings). It is hidden on Mac. Press **Cmd + Shift + .** in Finder to show it,
   then upload it too.
4. **Never upload API keys to GitHub.**

**2. Deploy on Streamlit Community Cloud**
1. Go to **share.streamlit.io** and sign in with GitHub.
2. Click **Create app → Deploy a public app from GitHub**. Pick your repo, branch `main`, main file `app.py`.
3. Open **Advanced settings**. Set Python version **3.12**. In **Secrets** paste:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   OPENAI_API_KEY = "sk-..."
   ADZUNA_APP_ID = "..."     # optional: live job postings
   ADZUNA_APP_KEY = "..."
   ```
4. Click **Deploy**. The first build takes 2–4 minutes. You get a public URL like `https://ai-career-coach.streamlit.app`.

**3. Before the presentation**
- Free Streamlit apps go to sleep after a period without visitors. Open the URL 10 minutes before presenting.
- The microphone needs the browser's permission the first time. Click Allow.
- If the Claude model name errors, add `CLAUDE_MODEL = "claude-sonnet-4-5"` (or another model your key supports) to Secrets.
  The app already falls back automatically if the default model isn't available.

## Run locally (optional)
```bash
pip install -r requirements.txt
mkdir -p .streamlit && cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then paste your keys
streamlit run app.py
```
Offline UI test with no keys: `CAREER_COACH_FAKE=1 streamlit run app.py` (canned responses).

## Project structure
```
app.py                 navigation + sidebar
core/rag.py            chunking, embeddings, vector search (RAG)
core/agent.py          tool-using agent loop + tools
core/llm.py            Claude API wrapper (JSON output, model fallback)
core/speech.py         Whisper transcription
core/jobs_api.py       Adzuna live job postings
core/data.py           BLS data + career trajectory model
core/gamify.py         XP, levels, badges, insights
core/theme.py          fonts, colors, CSS, hero/cards/job-row components
assets/                logo + icon
views/*.py             one file per page
knowledge/*.md         RAG knowledge base (add more .md files and they're indexed automatically)
data/                  BLS occupation + state wage data
```

## Group to-do list
- [ ] Deploy and test every page with the real API keys (about $1–3 of API usage in total).
- [ ] Add 10–20 **real** recent interview questions from Glassdoor/Reddit to `knowledge/interview_questions.md`
      (same format), so we can truthfully say the bank includes sourced questions.
- [ ] Test the microphone on the presentation laptop.
- [ ] Record a 60-second backup demo video in case the Wi-Fi fails.

## 5-minute presentation outline
1. **Problem (0:30):** students lack personalized, timely career guidance; the AI-era job market changes fast.
2. **Solution + live demo (2:30):** upload resume → quiz results → Career Matches (open the agent trace) →
   dashboard map and trajectory → mock interview answered out loud → feedback.
3. **How it works (1:15):** RAG diagram (knowledge base + resume → embeddings → retrieval → Claude), agent tool loop,
   Whisper, real BLS data.
4. **Practical value + next steps (0:45):** saving progress across sessions, more occupations, career center integration.
