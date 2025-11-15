import streamlit as st

from utils.llm_utils import get_llm_answer, init_chat_state


def render():
    st.title("💬 Chatbot")

    st.write(
        "This page shows a simple chat interface using `st.chat_input` and "
        "`st.chat_message`. The bot has very basic logic over the synthetic data."
    )

    init_chat_state()

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User input
    user_input = st.chat_input("Ask something about the metrics or type 'help'...")
    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Generate answer
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                answer = get_llm_answer(user_input)
                st.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})
