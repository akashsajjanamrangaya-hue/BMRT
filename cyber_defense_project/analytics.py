from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "logs.txt"
OUTPUT_CHART = BASE_DIR / "monthly_abnormal_attempts.png"


def parse_primary_log_lines(lines: list[str]) -> pd.DataFrame:
    """Parse primary behavior-analysis entries from logs file."""
    records = []
    for line in lines:
        if "|" not in line or "Decoy Search" in line:
            continue

        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 5:
            continue

        timestamp = parts[0].strip("[]")
        records.append(
            {
                "timestamp": timestamp,
                "keyword": parts[1],
                "risk_score": parts[2],
                "classification": parts[3],
                "action": parts[4],
            }
        )

    if not records:
        return pd.DataFrame(columns=["timestamp", "keyword", "risk_score", "classification", "action"])

    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df.dropna(subset=["timestamp"])


def generate_monthly_abnormal_chart() -> None:
    if not LOG_FILE.exists():
        print("logs.txt not found. Run app.py first to generate logs.")
        return

    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    df = parse_primary_log_lines(lines)

    abnormal_df = df[df["classification"] == "Abnormal"].copy()
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

    print(f"Chart generated successfully: {OUTPUT_CHART}")


if __name__ == "__main__":
    generate_monthly_abnormal_chart()
