from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "logs.txt"
OUTPUT_CHART = BASE_DIR / "monthly_abnormal_interaction_attempts.png"


def _parse_unified_log(parts: list[str]) -> dict | None:
    """Parse 8-column unified log format used by current app."""
    if len(parts) != 8:
        return None

    return {
        "timestamp": parts[0].strip("[]"),
        "context": parts[7],
        "is_abnormal": "ABNORMAL" in parts[7].upper(),
    }


def _parse_legacy_log(parts: list[str]) -> dict | None:
    """Parse legacy 5-column format for backward compatibility."""
    if len(parts) != 5:
        return None

    classification = parts[3]
    return {
        "timestamp": parts[0].strip("[]"),
        "context": f"LEGACY_{classification.upper()}",
        "is_abnormal": classification.strip().lower() == "abnormal",
    }


def load_log_dataframe() -> pd.DataFrame:
    """Load logs.txt and normalize both current + legacy structures."""
    if not LOG_FILE.exists():
        return pd.DataFrame(columns=["timestamp", "context", "is_abnormal"])

    records = []
    for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
        if "|" not in line:
            continue

        parts = [p.strip() for p in line.split("|")]
        record = _parse_unified_log(parts) or _parse_legacy_log(parts)
        if record:
            records.append(record)

    if not records:
        return pd.DataFrame(columns=["timestamp", "context", "is_abnormal"])

    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df.dropna(subset=["timestamp"])


def generate_monthly_abnormal_chart() -> None:
    df = load_log_dataframe()
    if df.empty:
        print("No valid log entries found.")
        return

    abnormal_df = df[df["is_abnormal"]].copy()
    if abnormal_df.empty:
        print("No abnormal behavior entries found in logs.")
        return

    abnormal_df["month"] = abnormal_df["timestamp"].dt.to_period("M").astype(str)
    grouped = abnormal_df.groupby("month").size().reset_index(name="count")

    plt.figure(figsize=(10, 5))
    plt.bar(grouped["month"], grouped["count"], color="#00bfff")
    plt.title("Monthly Abnormal Interaction Attempts")
    plt.xlabel("Month")
    plt.ylabel("Number of Attempts")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(OUTPUT_CHART)

    print(f"Chart generated successfully: {OUTPUT_CHART}")


if __name__ == "__main__":
    generate_monthly_abnormal_chart()
