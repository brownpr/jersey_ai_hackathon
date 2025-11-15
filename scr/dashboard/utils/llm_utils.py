import os
import requests

import pandas as pd
import streamlit as st

from utils.llm_tools import parse_intent, get_basic_stats, get_latest_value, get_sensor_overview

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

def _call_ollama(prompt: str) -> str:
    """Call the Ollama chat API and return the model's reply."""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant inside a Streamlit dashboard. "
                            "If the user asks about metrics, explain conceptually, but the actual "
                            "numeric values may be provided by the app itself."
                        ),
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
            f"Error calling Ollama: `{e}`. "
            "Check that the `ollama` container is running and reachable."
        )


def get_llm_answer(prompt: str, df) -> str:
    """
    Decide whether to answer via a dataframe tool (latest value / stats)
    or to fall back to the LLM.
    """
    # df is expected to be a pandas DataFrame with the columns you described.
    intent = parse_intent(prompt, df)

    # 1. Help
    if intent["type"] == "help":
        available_vars = ", ".join(
            sorted(str(v) for v in df["variable"].dropna().unique())
        )
        available_sensors = ", ".join(
            sorted(str(v) for v in df["sensor_name"].dropna().unique())
        )
        return (
            "I can interact with the loaded metrics data.\n\n"
            "**Examples:**\n"
            "- `latest Journey Time`\n"
            "- `latest PM10 for BR3_SJB2`\n"
            "- `average Plates In`\n"
            "- `stats for Humidity`\n\n"
            "- `info about PER_AIRMON_MESH306245`\n\n"
            "Available variables are:\n\n"
            f"{available_vars}\n\n"
            "Available sensors are:\n\n"
            f"{available_sensors}\n\n"
            "If I don't recognise your request, I'll just try to answer it normally."
        )

    # 2. Latest value tool
    if intent["type"] == "latest_value":
        variable = intent.get("variable")
        sensor = intent.get("sensor")

        if variable is None:
            available_vars = ", ".join(
                sorted(str(v) for v in df["variable"].dropna().unique())
            )
            return (
                "I couldn't figure out which variable you meant. "
                "Try something like `latest Journey Time` or `latest PM10`.\n\n"
                f"Known variables are: {available_vars}"
            )

        row = get_latest_value(df, variable=variable, sensor=sensor)
        if row is None:
            if sensor:
                return f"I couldn't find any data for variable **'{variable}'** and sensor containing **'{sensor}'**."
            return f"I couldn't find any data for variable **'{variable}'**."

        sensor_name = row["sensor_name"]
        value = row["value"]
        ts = row["timestamp"]

        extra = f" (sensor filtered by `{sensor}`)" if sensor else ""
        return (
            f"The latest **{variable}**{extra} is **{value}** at **{ts}** "
            f"(sensor: `{sensor_name}`)."
        )

    # 3. Stats tool
    if intent["type"] == "stats":
        variable = intent.get("variable")
        sensor = intent.get("sensor")

        if variable is None:
            available_vars = ", ".join(
                sorted(str(v) for v in df["variable"].dropna().unique())
            )
            return (
                "I couldn't figure out which variable you meant for stats. "
                "Try `average Journey Time` or `stats for Plates Out`.\n\n"
                f"Known variables are: {available_vars}"
            )

        stats = get_basic_stats(df, variable=variable, sensor=sensor)
        if stats is None:
            if sensor:
                return f"No data found for **'{variable}'** with sensor containing **'{sensor}'**."
            return f"No data found for **'{variable}'**."

        extra = f" (sensor filtered by `{sensor}`)" if sensor else ""
        return (
            f"Stats for **{variable}**{extra}:\n\n"
            f"- Count: {stats['count']}\n"
            f"- Mean: {stats['mean']:.2f}\n"
            f"- Min: {stats['min']}\n"
            f"- Max: {stats['max']}\n"
        )

    # 4. Sensor overview tool
    if intent["type"] == "sensor_overview":
        sensor = intent.get("sensor")
        if not sensor:
            return "I couldn't figure out which sensor you meant."

        overview = get_sensor_overview(df, sensor)
        if overview is None or overview.empty:
            return f"I couldn't find any data for sensor containing **'{sensor}'**."

        max_rows = 20
        sub = overview.head(max_rows)

        header_sensor = sub["sensor_name"].iloc[0]

        lines = [
            f"Here is an overview of variables for sensor `{header_sensor}`:",
            "",
            "| Variable | Latest | Timestamp | Mean | Max | Min |",
            "|----------|--------:|-----------:|------:|------:|------|",
        ]

        for _, row in sub.iterrows():
            # Convert values safely
            latest_val = f"{row['latest_value']:.3f}" if pd.notna(row['latest_value']) else "—"
            ts_val     = row['timestamp']
            mean_val   = f"{row['mean']:.3f}"         if pd.notna(row['mean'])         else "—"
            min_val    = f"{row['min']:.3f}"          if pd.notna(row['min'])          else "—"
            max_val    = f"{row['max']:.3f}"          if pd.notna(row['max'])          else "—"


            lines.append(
                f"| {row['variable']} | {latest_val} | {mean_val} | {min_val} | {max_val} | {ts_val} |"
            )


        if len(overview) > max_rows:
            lines.append("")
            lines.append(f"_Showing first {max_rows} variables out of {len(overview)}._")

        return "\n".join(lines)


    # 5. Fallback: normal LLM answer
    return _call_ollama(prompt)