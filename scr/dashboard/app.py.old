import streamlit as st
import pandas as pd
import numpy as np
import os
import requests
from datetime import datetime, timedelta


# ----------------- CONFIG -----------------
st.set_page_config(
    page_title="Demo Dashboard with Chatbot",
    layout="wide",
)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")  # or whatever model you're using


# ----------------- DATA GENERATION -----------------
@st.cache_data
def generate_time_series(days: int = 30):
    """Generate simple synthetic time-series data for the demo."""
    now = datetime.now()
    dates = [now - timedelta(days=i) for i in range(days)][::-1]
    data = {
        "date": dates,
        "metric_a": np.random.normal(loc=50, scale=10, size=days).cumsum(),
        "metric_b": np.random.normal(loc=30, scale=5, size=days).cumsum(),
        "metric_c": np.random.normal(loc=10, scale=3, size=days).cumsum(),
    }
    df = pd.DataFrame(data)
    return df

df = generate_time_series(60)

# ----------------- CHATBOT LOGIC -----------------
def get_llm_answer(prompt: str) -> str:
    """Call the Ollama chat API and return the model's reply."""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant inside a Streamlit dashboard."},
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
        return f"⚠️ Error calling Ollama: `{e}`. Check that the `ollama` container is running and reachable."


def init_chat_state():
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi! I'm the demo chatbot. Ask me about the metrics or say 'help'.",
            }
        ]

# ----------------- PAGES -----------------
def page_overview():
    st.title("📊 Overview")

    st.write("Basic overview of synthetic metrics over time.")

    col1, col2, col3 = st.columns(3)
    last_row = df.iloc[-1]

    col1.metric("Metric A (latest)", f"{last_row['metric_a']:.2f}")
    col2.metric("Metric B (latest)", f"{last_row['metric_b']:.2f}")
    col3.metric("Metric C (latest)", f"{last_row['metric_c']:.2f}")

    st.subheader("Metric A vs Metric B (line chart)")
    chart_df = df.set_index("date")[["metric_a", "metric_b"]]
    st.line_chart(chart_df)

    st.subheader("Raw data")
    st.dataframe(df.tail(10), use_container_width=True)


def page_analytics():
    st.title("📈 Analytics")

    st.write("Some extra plots to show different visualizations.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Metric A distribution")
        st.bar_chart(df["metric_a"])

    with col2:
        st.subheader("Metric B distribution")
        st.bar_chart(df["metric_b"])

    st.subheader("Metric A vs Metric B (scatter-like using data frame)")
    st.write(
        "Streamlit doesn't have a direct scatter shortcut, "
        "but plotting a dataframe still gives a nice exploratory view."
    )

    scatter_df = df[["metric_a", "metric_b"]]
    st.line_chart(scatter_df)

def page_prediction():
    st.title("🤖 Prediction demo")

    st.write(
        "This is a **fake prediction model** just to demonstrate the UI. "
        "We combine a few sliders into a simple linear formula."
    )

    col1, col2 = st.columns(2)

    with col1:
        feature_1 = st.slider("Feature 1 (e.g. temperature)", 0.0, 100.0, 50.0)
        feature_2 = st.slider("Feature 2 (e.g. pH)", 0.0, 14.0, 7.0)
        feature_3 = st.slider("Feature 3 (e.g. agitation speed)", 0, 1000, 500)

    with col2:
        st.write("Model parameters (for demo)")
        weight_1 = st.number_input("Weight for Feature 1", value=0.5)
        weight_2 = st.number_input("Weight for Feature 2", value=2.0)
        weight_3 = st.number_input("Weight for Feature 3", value=0.01)
        bias = st.number_input("Bias", value=10.0)

    if st.button("Run prediction"):
        prediction = (
            weight_1 * feature_1
            + weight_2 * feature_2
            + weight_3 * feature_3
            + bias
        )
        st.success(f"Predicted value: **{prediction:.2f}**")
    else:
        st.info("Adjust the sliders/weights and click **Run prediction**.")


def page_chatbot():
    st.title("💬 Chatbot")

    st.write(
        "This page shows a simple chat interface using `st.chat_input` and `st.chat_message`. "
        "The bot has very basic logic over the synthetic data."
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


# ----------------- MAIN -----------------
def main():
    st.sidebar.title("Demo Navigation")
    page = st.sidebar.radio(
        "Go to",
        ("Overview", "Analytics", "Prediction", "Chatbot"),
    )

    if page == "Overview":
        page_overview()
    elif page == "Analytics":
        page_analytics()
    elif page == "Prediction":
        page_prediction()
    elif page == "Chatbot":
        page_chatbot()

if __name__ == "__main__":
    main()
