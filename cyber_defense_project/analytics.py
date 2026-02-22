from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Log file path
LOG_FILE = BASE_DIR / "logs.txt"

# Output chart path
OUTPUT_CHART = BASE_DIR / "monthly_abnormal_attempts.png"


def parse_log_file() -> pd.DataFrame:
    """
    Parse behavior-analysis entries from logs.txt.

    Expected log format:
    [Timestamp] | Keyword | Risk Score | Classification | Action

    Decoy-only interaction logs are ignored.
    """
    if not LOG_FILE.exists():
        return pd.DataFrame(columns=["timestamp", "classification"])

    records = []

    for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
        # Ignore invalid or decoy-only logs
        if "|" not in line or "Decoy Search" in line:
            continue

        parts = [part.strip() for part in line.split("|")]

        if len(parts) != 5:
            continue

        timestamp = parts[0].strip("[]")
        classification = parts[3]

        records.append(
            {
                "timestamp": timestamp,
                "classification": classification,
            }
        )

    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    return df.dropna(subset=["timestamp"])


def generate_monthly_abnormal_chart() -> None:
    """
    Generate a bar chart showing monthly abnormal access attempts.
    """
    df = parse_log_file()

    if df.empty:
        print("No valid log entries found.")
        return

    abnormal_df = df[df["classification"] == "Abnormal"]

    if abnormal_df.empty:
        print("No abnormal entries found in logs.")
        return

    abnormal_df["month"] = abnormal_df["timestamp"].dt.to_period("M").astype(str)
    grouped = abnormal_df.groupby("month").size().reset_index(name="count")

    plt.figure(figsize=(10, 5))
    plt.bar(grouped["month"], grouped["count"], color="#00bfff")
    plt.title("Monthly Abnormal Access Attempts")
    plt.xlabel("Month")
    plt.ylabel("Number of Attempts")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(OUTPUT_CHART)
    plt.close()

    print(f"Chart generated successfully: {OUTPUT_CHART}")


if __name__ == "__main__":
    generate_monthly_abnormal_chart()