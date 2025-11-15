import re
from typing import Literal, Optional, Dict, Any

import pandas as pd


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


def get_sensor_overview(df: pd.DataFrame, sensor: str) -> Optional[pd.DataFrame]:
    """
    For a given sensor (substring match), return:
      - variable
      - latest value
      - latest timestamp
      - mean
      - min
      - max
      - sensor_name
    One row per variable.
    """
    # Filter by sensor name (contains)
    filtered = df[df["sensor_name"].str.contains(sensor, case=False, na=False)].copy()
    if filtered.empty:
        return None

    # Ensure timestamps are datetime
    if not pd.api.types.is_datetime64_any_dtype(filtered["timestamp"]):
        filtered["timestamp"] = pd.to_datetime(filtered["timestamp"])

    results = []

    for var, group in filtered.groupby("variable"):
        # Convert values to float where possible
        g = group.copy()
        g["value"] = pd.to_numeric(g["value"], errors="coerce")

        # Latest value
        g_sorted = g.sort_values("timestamp")
        latest_row = g_sorted.iloc[-1]

        results.append({
            "variable": var,
            "latest_value": latest_row["value"],
            "timestamp": latest_row["timestamp"],
            "mean": g["value"].mean(),
            "min": g["value"].min(),
            "max": g["value"].max(),
            "sensor_name": latest_row["sensor_name"],
        })

    return pd.DataFrame(results)


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