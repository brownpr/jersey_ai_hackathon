import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ----------------- CONFIG -----------------
st.set_page_config(
    page_title="Demo Dashboard with Chatbot",
    layout="wide",
)

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
def get_basic_answer(prompt: str) -> str:
    """Very simple, fake chatbot logic for demo purposes."""
    prompt_lower = prompt.lower()

    if "mean" in prompt_lower or "average" in prompt_lower:
        mean_a = df["metric_a"].mean()
        mean_b = df["metric_b"].mean()
        return (
            f"The average of Metric A is **{mean_a:.2f}** and "
            f"the average of Metric B is **{mean_b:.2f}** over the last {len(df)} points."
        )
    if "latest" in prompt_lower or "today" in prompt_lower:
        last_row = df.iloc[-1]
        return (
            "Here are the latest values:\n\n"
            f"- Metric A: **{last_row['metric_a']:.2f}**\n"
            f"- Metric B: **{last_row['metric_b']:.2f}**\n"
            f"- Metric C: **{last_row['metric_c']:.2f}**"
        )
    if "help" in prompt_lower:
        return (
            "I can answer simple questions about the demo data, like:\n"
            "- `What is the mean of the metrics?`\n"
            "- `Show me the latest values`\n"
            "Or just chat with me!"
        )

    # Fallback: simple echo
    return f"You said: `{prompt}`. I am a simple demo bot; ask me about mean or latest values."


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
        answer = get_basic_answer(user_input)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)

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
