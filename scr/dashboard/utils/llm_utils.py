import os
import requests
import streamlit as st


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")  # or whatever model you're using

def init_chat_state():
    """Initialize chat state with a default assistant message."""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi! I'm the demo chatbot. Ask me about the metrics or say 'help'.",
            }
        ]


def get_llm_answer(prompt: str) -> str:
    """Call the Ollama chat API and return the model's reply."""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant inside a Streamlit dashboard.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        # Ollama's /api/chat returns: {"message": {"role": "...", "content": "..."}}
        return data["message"]["content"]
    except Exception as e:
        return (
            f"⚠️ Error calling Ollama: `{e}`. "
            "Check that the `ollama` container is running and reachable."
        )
