import json
import re
from datetime import datetime
from pathlib import Path

from flask import Flask, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset.json"
LOG_PATH = BASE_DIR / "logs.txt"

app = Flask(__name__)
app.secret_key = "academic-cyber-defense-framework-key"


def load_rules() -> dict:
    """Load behavior rules from dataset.json."""
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def resolve_fake_site(keyword: str) -> str:
    """Map keyword to fake clone route names."""
    k = keyword.strip().lower()
    if "google" in k:
        return "fake_google"
    if "youtube" in k:
        return "fake_youtube"
    if "amazon" in k:
        return "fake_amazon"
    return "fake_generic"


def classify_keyword(keyword: str, rules: dict) -> tuple[str, list[str]]:
    """
    Rule-based classification only (no AI/ML).
    Returns: (classification, reasons)
    """
    cleaned = keyword.strip().lower()
    reasons: list[str] = []

    # Empty input is abnormal
    if not cleaned:
        reasons.append("empty_input")

    # Explicit special character checks
    if any(symbol in cleaned for symbol in rules["abnormal_patterns"]["special_characters"]):
        reasons.append("contains_special_characters")

    # Restricted terms
    if any(word in cleaned for word in rules["abnormal_patterns"]["restricted_keywords"]):
        reasons.append("contains_restricted_keyword")

    # Pattern mismatch
    if not re.fullmatch(rules["allowed_pattern"], cleaned):
        reasons.append("pattern_mismatch")

    # Whitelist-based normal behavior
    if cleaned not in rules["allowed_keywords"]:
        reasons.append("not_in_allowed_keywords")

    # Repeated suspicious input count in the same session
    suspicious_count = session.get("suspicious_count", 0)
    if suspicious_count >= rules["thresholds"]["repeat_suspicious_count"]:
        reasons.append("repeated_suspicious_inputs")

    if reasons:
        return "abnormal", reasons
    return "normal", []


def log_event(keyword: str, classification: str, destination: str) -> None:
    """Write log line to logs.txt."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(
            f"[{timestamp}] keyword={keyword} classification={classification} destination={destination}\n"
        )


@app.before_request
def trap_abnormal_sessions():
    """Once abnormal, keep all navigation inside fake-site routes."""
    if not session.get("is_abnormal"):
        return None

    allowed = {
        "analyze",
        "fake_google",
        "fake_youtube",
        "fake_amazon",
        "fake_generic",
        "static",
    }

    if request.endpoint in allowed:
        return None

    return redirect(url_for("fake_generic"))


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    rules = load_rules()
    keyword = request.form.get("keyword", "").strip()

    # If already abnormal, keep logging and trapping.
    if session.get("is_abnormal"):
        destination = resolve_fake_site(keyword)
        log_event(keyword, "abnormal", destination)
        return redirect(url_for(destination))

    classification, reasons = classify_keyword(keyword, rules)

    if classification == "normal":
        session["suspicious_count"] = 0
        if keyword.lower() == "google":
            log_event(keyword, "normal", "https://www.google.com")
            return redirect("https://www.google.com")
        if keyword.lower() == "youtube":
            log_event(keyword, "normal", "https://www.youtube.com")
            return redirect("https://www.youtube.com")
        if keyword.lower() == "amazon":
            log_event(keyword, "normal", "https://www.amazon.com")
            return redirect("https://www.amazon.com")

    # Mark abnormal, increment suspicious counter and trap user.
    session["is_abnormal"] = True
    session["suspicious_count"] = session.get("suspicious_count", 0) + 1
    session["last_reasons"] = reasons

    destination = resolve_fake_site(keyword)
    log_event(keyword, "abnormal", destination)
    return redirect(url_for(destination))


@app.route("/fake/google", methods=["GET"])
def fake_google():
    return render_template("fake_google.html")


@app.route("/fake/youtube", methods=["GET"])
def fake_youtube():
    return render_template("fake_youtube.html")


@app.route("/fake/amazon", methods=["GET"])
def fake_amazon():
    return render_template("fake_amazon.html")


@app.route("/fake/generic", methods=["GET"])
def fake_generic():
    return render_template("fake_generic.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
