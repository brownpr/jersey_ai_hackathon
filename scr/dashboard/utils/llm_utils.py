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

def get_sensor_overview(
    df: pd.DataFrame,
    sensor: str,
) -> Optional[pd.DataFrame]:
    """
    For a given sensor name/pattern, return one latest row per variable.
    Result: DataFrame with columns: variable, value, timestamp, sensor_name.
    """
    # Filter by sensor substring (case-insensitive)
    filtered = df[df["sensor_name"].str.contains(sensor, case=False, na=False)].copy()
    if filtered.empty:
        return None

    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(filtered["timestamp"]):
        filtered["timestamp"] = pd.to_datetime(filtered["timestamp"])

    # Sort and take the latest row per variable
    filtered = filtered.sort_values("timestamp")
    latest_per_var = (
        filtered.groupby("variable", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )

    return latest_per_var[["variable", "value", "timestamp", "sensor_name"]]


IntentType = Literal["latest_value", "stats", "help", "fallback"]

def _extract_sensor_from_list(text: str, sensors) -> Optional[str]:
    """
    Try to find a known sensor name inside the user text, based on df['sensor_name'].
    Uses case-insensitive and normalized (no spaces/underscores/hyphens) matching.
    """
    text_lower = text.lower()
    normalized_text = re.sub(r"[\s_\-]", "", text_lower)

    # Unique, non-null sensor names
    candidates = sorted(
        [str(s) for s in sensors if pd.notna(s)],
        key=len,
        reverse=True,
    )

    for sensor in candidates:
        s_lower = sensor.lower()
        s_norm = re.sub(r"[\s_\-]", "", s_lower)

        if s_lower in text_lower or s_norm in normalized_text:
            return sensor

    return None


def _extract_variable(text: str, variables) -> Optional[str]:
    """
    Try to map phrases in the question to any known variable name
    coming from the dataframe (df['variable']).
    """
    text_lower = text.lower()
    # also a normalized version (no spaces/underscores/hyphens)
    normalized_text = re.sub(r"[\s_\-]", "", text_lower)

    # Sort by length so we match 'PM10' before 'PM1', etc.
    candidates = sorted(
        [str(v) for v in variables if pd.notna(v)],
        key=len,
        reverse=True,
    )

    for var in candidates:
        v_lower = var.lower()
        v_norm = re.sub(r"[\s_\-]", "", v_lower)

        # direct substring or normalized substring match
        if v_lower in text_lower or v_norm in normalized_text:
            return var

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


def parse_intent(user_input: str, df: pd.DataFrame) -> Dict[str, Any]:
    text = user_input.lower().strip()

    # All known variables from the dataframe
    variables = df["variable"].dropna().unique()
    sensors = df["sensor_name"].dropna().unique()

    # Help
    if text == "help" or "what can you do" in text:
        return {"type": "help"}

    # Latest value: "latest journey time", "last plates in", etc.
    if "latest" in text or "last" in text:
        variable = _extract_variable(user_input, variables)
        sensor = _extract_sensor_from_list(user_input, sensors) or _extract_sensor(user_input)
        return {"type": "latest_value", "variable": variable, "sensor": sensor}

    # Stats: "average / mean / stats / min / max journey time"
    if any(w in text for w in ["average", "avg", "mean", "min", "max", "stats", "summary"]):
        variable = _extract_variable(user_input, variables)
        sensor = _extract_sensor_from_list(user_input, sensors) or _extract_sensor(user_input)
        return {"type": "stats", "variable": variable, "sensor": sensor}
    
    # Sensor overview: if user mentions a known sensor but not latest/stats/help
    sensor = _extract_sensor_from_list(user_input, sensors)
    if sensor:
        # For queries like "info about PER_AIRMON_MESH306245" or just "PER_AIRMON_MESH306245"
        return {"type": "sensor_overview", "sensor": sensor}

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

        overview = get_sensor_overview(df, sensor=sensor)
        if overview is None or overview.empty:
            return f"I couldn't find any data for sensor containing **'{sensor}'**."

        # Build a markdown table
        # (cap at e.g. 20 variables just in case)
        max_rows = 20
        subset = overview.head(max_rows)

        lines = [
            f"Here is an overview of variables for sensor `{subset['sensor_name'].iloc[0]}`:",
            "",
            "| Variable | Latest value | Timestamp |",
            "|----------|-------------:|-----------|",
        ]
        for _, row in subset.iterrows():
            lines.append(
                f"| {row['variable']} | {row['value']} | {row['timestamp']} |"
            )

        if len(overview) > max_rows:
            lines.append("")
            lines.append(f"_Showing first {max_rows} variables out of {len(overview)}._")

        return "\n".join(lines)

    # 5. Fallback: normal LLM answer
    return _call_ollama(prompt)