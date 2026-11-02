"""A small tool-using agent built on Claude's tool-use API.

The agent receives a goal, decides which tools to call (search the knowledge base, look up job market
data, read the student's resume, fetch a job posting), observes the results, and repeats until it can
answer. Every step is recorded in a trace that the UI shows, so the class can see the agent "thinking".
"""
from __future__ import annotations

import json

from core import config, data, documents, llm, rag

TOOL_SPECS = [
    {
        "name": "search_knowledge_base",
        "description": "Semantic search over the curated career knowledge base: interview question bank, "
                       "recruiting timelines, resume guide, cover letter guide, career paths by major, interview rubric.",
        "input_schema": {"type": "object", "properties": {
            "query": {"type": "string"}, "k": {"type": "integer", "default": 4}}, "required": ["query"]},
    },
    {
        "name": "search_resume",
        "description": "Search the student's uploaded resume for experiences relevant to a query.",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
    },
    {
        "name": "list_occupations",
        "description": "List occupations that have real BLS pay and education data in this app.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_occupation_data",
        "description": "Get BLS pay percentiles, U.S. employment, growth, education, experience, career ladder, "
                       "and example employers for an occupation.",
        "input_schema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]},
    },
    {
        "name": "fetch_job_posting",
        "description": "Download and read the text of a job posting from a URL.",
        "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
    },
]


class Toolbox:
    def __init__(self, kb_index: rag.VectorIndex, resume_index: rag.VectorIndex | None):
        self.kb = kb_index
        self.resume = resume_index

    def run(self, name: str, args: dict) -> str:
        try:
            if name == "search_knowledge_base":
                return rag.format_context(self.kb.search(args["query"], int(args.get("k", 4))))
            if name == "search_resume":
                if not self.resume:
                    return "No resume uploaded."
                return rag.format_context(self.resume.search(args["query"], 3))
            if name == "list_occupations":
                return "\n".join(f"- {o['title']} ({o['aka']}; family: {o['family']})" for o in data.occupations())
            if name == "get_occupation_data":
                o = data.get_occupation(args["title"])
                return data.occupation_summary_text(o) if o else f"No data for '{args['title']}'."
            if name == "fetch_job_posting":
                return documents.fetch_url_text(args["url"])
            return f"Unknown tool {name}"
        except Exception as e:  # tool errors go back to the agent so it can adapt
            return f"Tool error: {e}"


def run_agent(system: str, goal: str, toolbox: Toolbox, max_steps: int = 8, max_tokens: int = 4000):
    """Returns (final_text, trace). trace = list of {tool, input, output_preview}."""
    trace: list[dict] = []
    if config.fake_mode():
        from core import fake
        return fake.agent(system, goal, toolbox, trace)

    messages = [{"role": "user", "content": goal}]
    for _ in range(max_steps):
        resp = llm.create_message(max_tokens=max_tokens, system=system,
                                  tools=TOOL_SPECS, messages=messages)
        messages.append({"role": "assistant", "content": resp.content})
        tool_calls = [b for b in resp.content if b.type == "tool_use"]
        if resp.stop_reason != "tool_use" or not tool_calls:
            return "".join(b.text for b in resp.content if b.type == "text"), trace
        results = []
        for call in tool_calls:
            out = toolbox.run(call.name, call.input)
            trace.append({"tool": call.name, "input": call.input, "output": out[:600]})
            results.append({"type": "tool_result", "tool_use_id": call.id, "content": out})
        messages.append({"role": "user", "content": results})

    # Out of steps: ask for the final answer without tools
    messages.append({"role": "user", "content": "Stop using tools and give your final answer now in the required format."})
    resp = llm.create_message(max_tokens=max_tokens, system=system, messages=messages)
    return "".join(b.text for b in resp.content if b.type == "text"), trace


def run_agent_json(system: str, goal: str, toolbox: Toolbox, **kw):
    text, trace = run_agent(system + "\n\nYour FINAL message must be ONLY valid JSON (no markdown).", goal, toolbox, **kw)
    try:
        return llm.extract_json(text), trace
    except ValueError:
        fixed = llm.ask("Convert this into the requested valid JSON only.", text)
        return llm.extract_json(fixed), trace


def trace_markdown(trace: list[dict]) -> str:
    if not trace:
        return "_The agent answered without needing tools._"
    lines = []
    for i, t in enumerate(trace, 1):
        lines.append(f"**Step {i}: `{t['tool']}`** — input: `{json.dumps(t['input'])}`")
        preview = t["output"].replace("\n", " ")[:220]
        lines.append(f"> {preview}…")
    return "\n\n".join(lines)
