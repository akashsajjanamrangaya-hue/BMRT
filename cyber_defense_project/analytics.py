from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "logs.txt"
OUTPUT = BASE_DIR / "monthly_abnormal_interaction_attempts.png"


def load_log_dataframe() -> pd.DataFrame:
    if not LOG_FILE.exists():
        return pd.DataFrame()

    rows = []
    for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 8:
            continue

        rows.append(
            {
                "timestamp": parts[0].strip("[]"),
                "session_id": parts[1],
                "input": parts[2],
                "length": parts[3],
                "special_chars": parts[4],
                "time_delta": parts[5],
                "interaction_count": parts[6],
                "context": parts[7],
            }
        )

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df.dropna(subset=["timestamp"])


def generate_chart() -> None:
    df = load_log_dataframe()
    if df.empty:
        print("No valid log entries found.")
        return

    abnormal_df = df[df["context"].str.contains("ABNORMAL", case=False, na=False)].copy()
    if abnormal_df.empty:
        print("No abnormal behavior entries found in logs.")
        return

    abnormal_df["month"] = abnormal_df["timestamp"].dt.to_period("M").astype(str)
    grouped = abnormal_df.groupby("month").size().reset_index(name="count")

    plt.figure(figsize=(10, 5))
    plt.bar(grouped["month"], grouped["count"], color="#00bfff")
    plt.title("Monthly Abnormal Interaction Attempts")
    plt.xlabel("Month")
    plt.ylabel("Count")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(OUTPUT)

    print(f"Saved chart: {OUTPUT}")


if __name__ == "__main__":
    generate_chart()
