import os

import streamlit as st
from dotenv import load_dotenv

from rabbit_hole import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    LEVEL_LABELS,
    add_real_links,
    generate_rabbit_hole,
    make_client,
    to_markdown,
)

load_dotenv()

st.set_page_config(page_title="Rabbit Hole Generator", page_icon="🐇", layout="centered")

st.title("🐇 The Rabbit Hole Generator")
st.caption("Turn a pop-culture interest into a five-step research adventure.")

EXAMPLES = [
    "I love Gossip Girl. Take me down a rabbit hole about gossip, social status, misogyny, and reputation.",
    "Squid Game and what it says about debt and inequality.",
    "Barbie: feminism, play, and the history of dolls.",
    "Sherlock Holmes and the birth of modern detective culture.",
]

with st.sidebar:
    st.header("Settings")
    language = st.selectbox("Language", ["English", "French", "Arabic"])
    use_links = st.checkbox("Attach real links (web search)", value=True)
    st.markdown("---")
    st.caption(
        f"Model: `{os.getenv('LLM_MODEL', DEFAULT_MODEL)}`  \n"
        f"Provider: `{os.getenv('LLM_BASE_URL', DEFAULT_BASE_URL)}`"
    )

if "topic" not in st.session_state:
    st.session_state.topic = ""

st.write("**Need inspiration?**")
cols = st.columns(2)
for i, example in enumerate(EXAMPLES):
    if cols[i % 2].button(example[:45] + "…", key=f"ex{i}", use_container_width=True):
        st.session_state.topic = example

topic = st.text_area(
    "What do you want to fall into?",
    key="topic",
    height=100,
    placeholder="A topic, character, film, book or cultural phenomenon, plus any themes you care about.",
)

if st.button("Take me down the rabbit hole", type="primary", disabled=not topic.strip()):
    try:
        client = make_client()
        with st.spinner("Digging the tunnel…"):
            data = generate_rabbit_hole(topic.strip(), language=language, client=client)
        if use_links:
            with st.spinner("Looking for real sources…"):
                data = add_real_links(data)
        st.session_state.result = data
    except Exception as e:
        st.error(f"Something went wrong: {e}")

data = st.session_state.get("result")
if data:
    st.header(data.get("title", "Your rabbit hole"))
    st.write(data.get("intro", ""))

    for q in data["questions"]:
        label = LEVEL_LABELS.get(q["level"], "")
        with st.expander(f"{q['level']}. {q['question']}  ·  {label}", expanded=q["level"] == 1):
            if q.get("connection_to_previous"):
                st.info(q["connection_to_previous"])
            st.write(q["explanation"])
            if q["disciplines"]:
                st.markdown("**Disciplines:** " + " · ".join(q["disciplines"]))
            if q["search_terms"]:
                st.markdown("**Search terms**")
                for term in q["search_terms"]:
                    st.code(term, language=None)
            if q["source_suggestions"]:
                st.markdown("**Suggested sources**")
                for s in q["source_suggestions"]:
                    st.markdown(f"- {s}")
            if q.get("links"):
                st.markdown("**Links to start with**")
                for link in q["links"]:
                    st.markdown(f"- [{link['title']}]({link['url']})")

    if data.get("where_next"):
        st.success("**Where next?** " + data["where_next"])

    st.download_button(
        "Download as Markdown",
        to_markdown(data),
        file_name="rabbit_hole.md",
        mime="text/markdown",
    )
