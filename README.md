# 🐇 The Rabbit Hole Generator

An AI agent for curious people who love learning through pop culture.
Give it a topic, character, film, book or cultural phenomenon, and it turns it into a
connected mini research adventure.

> *"I love Gossip Girl. Take me down a rabbit hole about gossip, social status, misogyny, and reputation."*

## What it does

- Generates **five connected questions**, from accessible to intellectually challenging
- Explains the **connections between psychology, history, sociology, art and culture**
- Gives **search terms** and **suggested sources** for further exploration
- Uses a **web search tool** to attach real links, so sources are not hallucinated
- Works in **English, French and Arabic**
- Exports the whole trail as **Markdown**

## How it works

1. The LLM builds a trail of five questions, each growing out of the previous one.
2. The agent calls a free web-search tool (DuckDuckGo) for each question to find real links.
3. The Streamlit app displays everything as expandable steps.

## Free stack

| Part | Tool |
|------|------|
| LLM | Groq or Google Gemini free tier, or Ollama (local) |
| Search tool | DuckDuckGo via `ddgs` (no key) |
| UI | Streamlit |
| Hosting (optional) | Streamlit Community Cloud |

## Run it locally

```bash
git clone https://github.com/<your-username>/rabbit-hole-generator.git
cd rabbit-hole-generator
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env     # then add your free API key
streamlit run app.py
```

## Choosing an LLM provider

Everything goes through one OpenAI-compatible client, so switching provider only means
changing three variables in `.env` (see `.env.example` for Groq, Gemini and Ollama).

## Project structure

```
app.py            # Streamlit interface
rabbit_hole.py    # prompt, LLM call, web-search tool, Markdown export
requirements.txt
.env.example
```

## Limitations

- Suggested sources come from the LLM and may occasionally be imprecise: always check them.
  The attached links come from a real web search.
- Free tiers have rate limits.

## Ideas for next steps

- Let the user pick a difficulty or number of steps
- Add a "go deeper" button that starts a new trail from any question
- Save and share favorite rabbit holes
