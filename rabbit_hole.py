"""Core logic for the Rabbit Hole Generator.

Pipeline (a small agent with one tool):
  1. The LLM turns a topic into five connected questions, from accessible to challenging.
  2. For each question, the agent calls a web-search tool (DuckDuckGo, free, no key)
     to attach REAL links, so the sources are not hallucinated.
  3. The result can be exported as Markdown.
"""

from __future__ import annotations

import json
import os
import re

from openai import OpenAI

# --- LLM configuration (any OpenAI-compatible provider works) -----------------
# Defaults to Groq's free tier. See .env.example for Gemini and Ollama settings.
DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "llama-3.3-70b-versatile"

LEVEL_LABELS = {
    1: "Entry point",
    2: "Going deeper",
    3: "Making connections",
    4: "Critical lens",
    5: "Big question",
}

SYSTEM_PROMPT = """You are a curious, warm and rigorous guide who builds "rabbit holes":
short research adventures that start from pop culture and lead to real ideas in
psychology, history, sociology, art and cultural studies.

Given a starting point and optional themes, produce EXACTLY five connected questions.
Rules:
- Difficulty rises from 1 (accessible, fun) to 5 (intellectually challenging).
- Each question must grow out of the previous one, so the five form a trail, not a list.
- Each explanation (3-5 sentences) must explain WHY the question matters and how it
  connects psychology, history, sociology, art or culture. Name real concepts, theorists
  or movements when you are confident they exist. Never invent studies, quotes or books.
- search_terms: 3 precise queries a person could type into a search engine or Google Scholar.
- source_suggestions: 2-3 types or well-known works/authors to look for (only if you are
  confident they are real), e.g. "Erving Goffman, The Presentation of Self in Everyday Life".
- Write all text in the requested language.

Return ONLY a JSON object with this exact shape:
{
  "title": "catchy title for the rabbit hole",
  "intro": "2 sentences that hook the reader",
  "questions": [
    {
      "level": 1,
      "question": "...",
      "explanation": "...",
      "disciplines": ["psychology", "history"],
      "connection_to_previous": "how this question follows from the previous one (empty for level 1)",
      "search_terms": ["...", "...", "..."],
      "source_suggestions": ["...", "..."]
    }
  ],
  "where_next": "1-2 sentences suggesting where the reader could go after question 5"
}"""


def make_client(api_key: str | None = None, base_url: str | None = None) -> OpenAI:
    api_key = api_key or os.getenv("LLM_API_KEY")
    if not api_key:
        raise ValueError("No API key found. Set LLM_API_KEY (see .env.example).")
    return OpenAI(api_key=api_key, base_url=base_url or os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL))


def _extract_json(text: str) -> dict:
    """Parse JSON even if the model wrapped it in markdown fences or extra text."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("The model did not return valid JSON.")
        return json.loads(match.group(0))


def _validate(data: dict) -> dict:
    questions = data.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError("The model returned no questions.")
    for i, q in enumerate(questions[:5], start=1):
        q["level"] = i
        q.setdefault("disciplines", [])
        q.setdefault("connection_to_previous", "")
        q.setdefault("search_terms", [])
        q.setdefault("source_suggestions", [])
    data["questions"] = questions[:5]
    return data


def generate_rabbit_hole(
    topic: str,
    language: str = "English",
    client: OpenAI | None = None,
    model: str | None = None,
) -> dict:
    """Ask the LLM for the five-question trail."""
    client = client or make_client()
    model = model or os.getenv("LLM_MODEL", DEFAULT_MODEL)
    response = client.chat.completions.create(
        model=model,
        temperature=0.8,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Language: {language}\nStarting point: {topic}"},
        ],
        response_format={"type": "json_object"},
    )
    return _validate(_extract_json(response.choices[0].message.content))


# --- Tool: web search ---------------------------------------------------------
def web_search(query: str, max_results: int = 3) -> list[dict]:
    """Free web search (DuckDuckGo). Returns [{'title', 'url'}]; empty list on failure."""
    try:
        from ddgs import DDGS

        results = DDGS().text(query, max_results=max_results)
        return [
            {"title": r.get("title", "Link"), "url": r.get("href", "")}
            for r in results
            if r.get("href")
        ]
    except Exception:
        return []


def add_real_links(data: dict, links_per_question: int = 3) -> dict:
    """Use the search tool on each question's first search term to attach real links."""
    for q in data["questions"]:
        terms = q.get("search_terms") or [q["question"]]
        q["links"] = web_search(terms[0], max_results=links_per_question)
    return data


# --- Export -------------------------------------------------------------------
def to_markdown(data: dict) -> str:
    lines = [f"# {data.get('title', 'Rabbit Hole')}", "", data.get("intro", ""), ""]
    for q in data["questions"]:
        label = LEVEL_LABELS.get(q["level"], "")
        lines += [f"## {q['level']}. {q['question']}", f"*{label}*", ""]
        if q.get("connection_to_previous"):
            lines += [f"**Link to the previous question:** {q['connection_to_previous']}", ""]
        lines += [q["explanation"], ""]
        if q["disciplines"]:
            lines += [f"**Disciplines:** {', '.join(q['disciplines'])}", ""]
        if q["search_terms"]:
            lines += ["**Search terms:**"] + [f"- `{t}`" for t in q["search_terms"]] + [""]
        if q["source_suggestions"]:
            lines += ["**Suggested sources:**"] + [f"- {s}" for s in q["source_suggestions"]] + [""]
        if q.get("links"):
            lines += ["**Links to start with:**"] + [f"- [{l['title']}]({l['url']})" for l in q["links"]] + [""]
    if data.get("where_next"):
        lines += ["## Where next?", data["where_next"], ""]
    return "\n".join(lines)
