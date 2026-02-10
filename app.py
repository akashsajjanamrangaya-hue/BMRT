import json
import re
import socket
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

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


def looks_like_domain_keyword(keyword: str) -> bool:
    """
    Domain-like keyword: letters/numbers/hyphen with no spaces.
    Example: netflix, studentportal, flipkart, my-site
    """
    return bool(re.fullmatch(r"[a-z0-9-]+", keyword))


def resolve_fake_site(keyword: str) -> str:
    """Map suspicious input to the most realistic internal fake route."""
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

    NORMAL:
      - letters, numbers, spaces, hyphens
      - no suspicious symbols
      - no restricted attack words

    ABNORMAL:
      - slashes, traversal markers, query/control symbols
      - restricted terms (admin/login/root/config etc.)
      - repeated suspicious attempts in a session
    """
    cleaned = keyword.strip().lower()
    reasons: list[str] = []

    if not cleaned:
        reasons.append("empty_input")

    if any(symbol in cleaned for symbol in rules["abnormal_patterns"]["special_characters"]):
        reasons.append("contains_special_characters")

    if any(word in cleaned for word in rules["abnormal_patterns"]["restricted_keywords"]):
        reasons.append("contains_restricted_keyword")

    # Normal text can include letters, numbers, spaces, and hyphens only.
    if not re.fullmatch(rules["allowed_pattern"], cleaned):
        reasons.append("pattern_mismatch")

    suspicious_count = session.get("suspicious_count", 0)
    if suspicious_count >= rules["thresholds"]["repeat_suspicious_count"]:
        reasons.append("repeated_suspicious_inputs")

    if reasons:
        return "abnormal", reasons
    return "normal", []


def domain_exists(hostname: str) -> bool:
    """Best-effort DNS resolution to decide direct domain redirect vs search fallback."""
    try:
        socket.gethostbyname(hostname)
        return True
    except OSError:
        return False


def normal_redirect_target(keyword: str) -> str:
    """
    Real-site target for normal input.
    - If domain-like and resolvable -> https://www.<keyword>.com
    - Otherwise -> Google search fallback.
    """
    cleaned = keyword.strip().lower()

    if looks_like_domain_keyword(cleaned):
        host = f"www.{cleaned}.com"
        if domain_exists(host):
            return f"https://{host}"

    return f"https://www.google.com/search?q={quote_plus(cleaned)}"


def log_event(keyword: str, classification: str, target: str) -> None:
    """Write a silent audit line to logs.txt."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(
            f"[{timestamp}] keyword={keyword} classification={classification} target={target}\n"
        )


@app.before_request
def trap_abnormal_sessions():
    """Once marked abnormal, keep all navigation inside internal fake routes."""
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

    # Already trapped users always stay internal.
    if session.get("is_abnormal"):
        destination = resolve_fake_site(keyword)
        log_event(keyword, "abnormal", destination)
        return redirect(url_for(destination))

    classification, reasons = classify_keyword(keyword, rules)

    if classification == "normal":
        session["suspicious_count"] = 0
        target = normal_redirect_target(keyword)
        log_event(keyword, "normal", target)
        return redirect(target)

    # First abnormal detection -> trap session.
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
