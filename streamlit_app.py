import streamlit as st
from database import setup_database
from agent import run

st.set_page_config(page_title="Fashion Retail Assistant")

# Build DB from CSV once per session
if "db_ready" not in st.session_state:
    setup_database()
    st.session_state.db_ready = True
st.title("Chatbot Agent on Catalog Data")
st.caption("Ask questions about the product catalog — pricing, rankings, colors, discounts, and more.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if question := st.chat_input("Ask a question about the catalog..."):

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            output = run(question, history=st.session_state.messages)

        st.markdown(output["answer"])

        with st.expander("Stage 1 — Answerability check"):
            st.json(output["sanity"])

        if output["plan"]:
            with st.expander("Stage 2 — Query plan"):
                st.json(output["plan"])

            with st.expander("Generated SQL"):
                st.code(output["sql"], language="sql")

            with st.expander(f"Raw results ({len(output['results'])} rows)"):
                st.json(output["results"])

    st.session_state.messages.append({"role": "assistant", "content": output["answer"]})