"""Output formatting utilities for pytrends CLI harness."""

import json
import sys
from typing import Any

import pandas as pd


def df_to_json(df: pd.DataFrame) -> str:
    """Convert a DataFrame to JSON string."""
    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        return json.dumps({"data": [], "rows": 0})

    result = {
        "data": json.loads(df.to_json(orient="table", date_format="iso")),
        "rows": len(df),
    }
    return json.dumps(result, indent=2)


def series_to_json(series: pd.Series) -> str:
    """Convert a Series to JSON string."""
    if series is None or (isinstance(series, pd.Series) and series.empty):
        return json.dumps({"data": [], "rows": 0})

    result = {
        "data": series.tolist(),
        "rows": len(series),
    }
    return json.dumps(result, indent=2)


def dict_to_json(data: dict) -> str:
    """Convert a dict to JSON, handling DataFrames within."""
    def _serialize(obj):
        if isinstance(obj, pd.DataFrame):
            if obj.empty:
                return None
            return json.loads(obj.to_json(orient="records"))
        elif isinstance(obj, pd.Series):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: _serialize(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [_serialize(item) for item in obj]
        return obj

    return json.dumps(_serialize(data), indent=2)


def list_to_json(data: list) -> str:
    """Convert a list to JSON string."""
    return json.dumps({"data": data, "count": len(data)}, indent=2)


def format_output(data: Any, output_format: str = "table") -> str:
    """Format data according to the specified output format.

    Args:
        data: The data to format (DataFrame, Series, dict, list)
        output_format: One of 'table', 'json', 'csv'

    Returns:
        Formatted string representation
    """
    if output_format == "json":
        if isinstance(data, pd.DataFrame):
            return df_to_json(data)
        elif isinstance(data, pd.Series):
            return series_to_json(data)
        elif isinstance(data, dict):
            return dict_to_json(data)
        elif isinstance(data, list):
            return list_to_json(data)
        else:
            return json.dumps(data, indent=2, default=str)

    elif output_format == "csv":
        if isinstance(data, pd.DataFrame):
            return data.to_csv()
        elif isinstance(data, pd.Series):
            return data.to_csv()
        elif isinstance(data, dict):
            parts = []
            for key, value in data.items():
                parts.append(f"# {key}")
                if isinstance(value, dict):
                    for sub_key, sub_val in value.items():
                        parts.append(f"## {sub_key}")
                        if isinstance(sub_val, pd.DataFrame) and not sub_val.empty:
                            parts.append(sub_val.to_csv())
                        elif isinstance(sub_val, pd.DataFrame):
                            parts.append("(no data)")
                        else:
                            parts.append(str(sub_val))
                else:
                    parts.append(str(value))
            return "\n".join(parts)
        elif isinstance(data, list):
            return pd.DataFrame(data).to_csv(index=False)
        else:
            return str(data)

    else:  # table (default)
        if isinstance(data, pd.DataFrame):
            if data.empty:
                return "(no data)"
            return data.to_string()
        elif isinstance(data, pd.Series):
            if data.empty:
                return "(no data)"
            return data.to_string()
        elif isinstance(data, dict):
            parts = []
            for key, value in data.items():
                if isinstance(value, pd.DataFrame):
                    parts.append(f"\n=== {key} ===")
                    if not value.empty:
                        parts.append(value.to_string())
                    else:
                        parts.append("(no data)")
                elif isinstance(value, dict):
                    parts.append(f"\n=== {key} ===")
                    for sub_key, sub_val in value.items():
                        if isinstance(sub_val, pd.DataFrame):
                            parts.append(f"\n--- {sub_key} ---")
                            if not sub_val.empty:
                                parts.append(sub_val.to_string())
                            else:
                                parts.append("(no data)")
                        else:
                            parts.append(f"  {sub_key}: {sub_val}")
                else:
                    parts.append(f"{key}: {value}")
            return "\n".join(parts)
        elif isinstance(data, list):
            if not data:
                return "(no data)"
            return pd.DataFrame(data).to_string(index=False)
        else:
            return str(data)
