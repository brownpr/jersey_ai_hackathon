import os
import re
from typing import Literal, Optional, Dict, Any

import pandas as pd
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

def _filter_df(
    df: pd.DataFrame,
    variable: Optional[str] = None,
    sensor: Optional[str] = None,
) -> pd.DataFrame:
    """Filter dataframe by variable and/or sensor substring."""
    result = df.copy()

    if variable:
        result = result[result["variable"].str.lower() == variable.lower()]

    if sensor:
        result = result[result["sensor_name"].str.contains(sensor, case=False, na=False)]

    return result

def get_latest_value(
    df: pd.DataFrame,
    variable: Optional[str] = None,
    sensor: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Return latest row for given variable/sensor combo, or None."""
    filtered = _filter_df(df, variable=variable, sensor=sensor)
    if filtered.empty:
        return None

    # Ensure Timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(filtered["timestamp"]):
        filtered = filtered.copy()
        filtered["timestamp"] = pd.to_datetime(filtered["timestamp"])

    latest_row = filtered.sort_values("timestamp").iloc[-1]
    return latest_row.to_dict()


def get_basic_stats(
    df: pd.DataFrame,
    variable: Optional[str] = None,
    sensor: Optional[str] = None,
) -> Optional[Dict[str, float]]:
    """Return basic stats (count, mean, min, max) for Value column."""
    filtered = _filter_df(df, variable=variable, sensor=sensor)
    if filtered.empty:
        return None

    s = filtered["value"].astype(float)
    return {
        "count": int(s.count()),
        "mean": float(s.mean()),
        "min": float(s.min()),
        "max": float(s.max()),
    }

IntentType = Literal["latest_value", "stats", "help", "fallback"]


def _extract_variable(text: str) -> Optional[str]:
    """Map phrases in the question to known Variable names."""
    text = text.lower()

    if "journey time" in text:
        return "Journey Time"
    if "plates in" in text:
        return "Plates In"
    if "plates out" in text:
        return "Plates Out"
    if "plates matching" in text:
        return "Plates Matching"

    return None


def _extract_sensor(text: str) -> Optional[str]:
    """
    Try to find something like BR3_SJB2, BR3- SJB2, etc.
    Adjust the regex if your sensor naming pattern changes.
    """
    match = re.search(r"(br\d+[_\-]?[a-z0-9]+)", text, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def parse_intent(user_input: str) -> Dict[str, Any]:
    text = user_input.lower().strip()

    # Help
    if text == "help" or "what can you do" in text:
        return {"type": "help"}

    # Latest value: "latest journey time", "last plates in", etc.
    if "latest" in text or "last" in text:
        variable = _extract_variable(text)
        sensor = _extract_sensor(text)
        return {"type": "latest_value", "variable": variable, "sensor": sensor}

    # Stats: "average / mean / stats / min / max journey time"
    if any(w in text for w in ["average", "avg", "mean", "min", "max", "stats", "summary"]):
        variable = _extract_variable(text)
        sensor = _extract_sensor(text)
        return {"type": "stats", "variable": variable, "sensor": sensor}

    # Fallback to normal model
    return {"type": "fallback"}


# ─────────────────────────────────────────────────────────────
# LLM call + tool routing
# ─────────────────────────────────────────────────────────────

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
            f"⚠️ Error calling Ollama: `{e}`. "
            "Check that the `ollama` container is running and reachable."
        )


def get_llm_answer(prompt: str, df) -> str:
    """
    Decide whether to answer via a dataframe tool (latest value / stats)
    or to fall back to the LLM.
    """
    # df is expected to be a pandas DataFrame with the columns you described.
    intent = parse_intent(prompt)

    # 1. Help
    if intent["type"] == "help":
        return (
            "I can interact with the loaded metrics data.\n\n"
            "**Examples:**\n"
            "- `latest journey time`\n"
            "- `latest journey time for BR3_SJB2`\n"
            "- `average plates in`\n"
            "- `stats for plates matching`\n\n"
            "If I don't recognise your request, I'll just try to answer it normally."
        )

    # 2. Latest value tool
    if intent["type"] == "latest_value":
        variable = intent.get("variable")
        sensor = intent.get("sensor")

        if variable is None:
            return (
                "I couldn't figure out which variable you meant. "
                "Try something like `latest Journey Time` or `latest Plates In`."
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
            return (
                "I couldn't figure out which variable you meant for stats. "
                "Try `average Journey Time` or `stats for Plates Out`."
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

    # 4. Fallback: normal LLM answer
    return _call_ollama(prompt)