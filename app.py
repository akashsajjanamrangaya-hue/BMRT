import json
import re
from datetime import datetime
from pathlib import Path

from flask import Flask, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset.json"
LOG_PATH = BASE_DIR / "logs.txt"

app = Flask(__name__)
app.secret_key = "intelligent-cyber-defense-framework"


def load_rules() -> dict:
    """Read and return the rule dataset from JSON."""
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def classify_input(keyword: str, rules: dict) -> tuple[str, list[str]]:
    """
    Rule-based classifier (no AI/ML).
    Returns: (classification, reasons)
    classification in {"normal", "abnormal"}
    """
    cleaned = keyword.strip().lower()
    reasons: list[str] = []

    if not cleaned:
        reasons.append("empty_input")

    # Detect restricted/sensitive terms.
    if any(term in cleaned for term in rules["restricted_keywords"]):
        reasons.append("restricted_keyword")

    # Detect suspicious characters and symbols.
    if any(symbol in cleaned for symbol in rules["abnormal_symbols"]):
        reasons.append("suspicious_symbol")

    # Pattern mismatch check.
    if not re.fullmatch(rules["allowed_pattern"], cleaned):
        reasons.append("pattern_mismatch")

    # Explicit allowed keyword check for strict behavior profile.
    if cleaned not in rules["allowed_keywords"]:
        reasons.append("keyword_not_whitelisted")

    if reasons:
        return "abnormal", reasons
    return "normal", []


def get_destination(keyword: str) -> str:
    """Map keyword to fake destination route name."""
    lowered = keyword.strip().lower()
    if "google" in lowered:
        return "fake_google"
    if "youtube" in lowered:
        return "fake_youtube"
    if "amazon" in lowered:
        return "fake_amazon"
    return "fake_generic"


def log_event(keyword: str, classification: str, destination: str) -> None:
    """Append behavior event to logs.txt."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = (
        f"[{timestamp}] keyword={keyword} classification={classification} "
        f"destination={destination}\n"
    )
    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(entry)


@app.before_request
def keep_abnormal_users_trapped():
    """
    Session guard: once abnormal, user stays in decoy environment.
    This prevents escape to real destinations via index or other routes.
    """
    if not session.get("abnormal"):
        return None

    allowed_endpoints = {
        "fake_google",
        "fake_youtube",
        "fake_amazon",
        "fake_generic",
        "fake_google_results",
        "analyze",
        "static",
    }
    if request.endpoint in allowed_endpoints:
        return None

    return redirect(url_for("fake_generic"))


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    rules = load_rules()
    keyword = request.form.get("keyword", "").strip()

    # Already trapped users are always routed to fake environments.
    if session.get("abnormal"):
        destination = get_destination(keyword)
        log_event(keyword, "abnormal", destination)
        return redirect(url_for(destination))

    classification, _ = classify_input(keyword, rules)

    if classification == "normal":
        if keyword.lower() == "google":
            destination = "https://www.google.com"
            log_event(keyword, "normal", destination)
            return redirect(destination)
        if keyword.lower() == "youtube":
            destination = "https://www.youtube.com"
            log_event(keyword, "normal", destination)
            return redirect(destination)
        if keyword.lower() == "amazon":
            destination = "https://www.amazon.com"
            log_event(keyword, "normal", destination)
            return redirect(destination)

    # Anything else is treated as abnormal and trapped.
    session["abnormal"] = True
    destination_name = get_destination(keyword)
    log_event(keyword, "abnormal", destination_name)
    return redirect(url_for(destination_name))


@app.route("/fake/google", methods=["GET", "POST"])
def fake_google():
    # Local result simulation stays inside fake environment.
    if request.method == "POST":
        query = request.form.get("query", "").strip()
        return redirect(url_for("fake_google_results", q=query))
    return render_template("fake_google.html")


@app.route("/fake/google/results", methods=["GET"])
def fake_google_results():
    query = request.args.get("q", "")
    return render_template("fake_google_results.html", query=query)


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
