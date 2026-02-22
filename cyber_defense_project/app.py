from datetime import datetime
from pathlib import Path
from uuid import uuid4

from flask import Flask, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "logs.txt"

app = Flask(__name__)
app.secret_key = "cyber-defense-final-year-project-key"


# -----------------------------
# Utility and behavior functions
# -----------------------------
def ensure_session_id() -> str:
    """Create and store a unique session id for each visitor."""
    if "session_id" not in session:
        session["session_id"] = str(uuid4())[:8]
    return session["session_id"]


def calculate_risk_score(keyword: str, request_frequency: int) -> tuple[float, dict]:
    """
    Calculate risk score using the weighted formula:
    RS = (0.4 × special_characters)
         + (0.3 × request_frequency)
         + (0.3 × suspicious_pattern_flag)
    """
    special_characters = sum(1 for char in keyword if not char.isalnum() and not char.isspace())
    suspicious_pattern_flag = 1 if ("//" in keyword or "\\\\" in keyword or "@@" in keyword or ".." in keyword) else 0

    risk_score = (
        (0.4 * special_characters)
        + (0.3 * request_frequency)
        + (0.3 * suspicious_pattern_flag)
    )

    features = {
        "keyword_length": len(keyword),
        "special_characters": special_characters,
        "request_frequency": request_frequency,
        "suspicious_pattern_flag": suspicious_pattern_flag,
    }
    return round(risk_score, 2), features


def classify_request(risk_score: float) -> str:
    """Classify request using project threshold."""
    return "Abnormal" if risk_score > 3 else "Normal"


def append_log(keyword: str, risk_score: float, classification: str, action: str) -> None:
    """Append primary behavior analysis log entry to logs.txt."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] | {keyword} | {risk_score} | {classification} | {action}\n"
    with LOG_FILE.open("a", encoding="utf-8") as log_file:
        log_file.write(entry)


def append_decoy_log(keyword: str) -> None:
    """Append decoy interaction log with session details."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session_id = ensure_session_id()
    entry = f"[{timestamp}] | Decoy Search | {keyword} | Session={session_id}\n"
    with LOG_FILE.open("a", encoding="utf-8") as log_file:
        log_file.write(entry)


def read_logs() -> list[str]:
    """Read all logs for dashboard presentation."""
    if not LOG_FILE.exists():
        return []
    return LOG_FILE.read_text(encoding="utf-8").splitlines()[::-1]


# -----------------------------
# Routes
# -----------------------------
@app.route("/", methods=["GET"])
def index():
    ensure_session_id()
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_keyword():
    ensure_session_id()

    keyword = request.form.get("keyword", "").strip()
    if not keyword:
        return redirect(url_for("index"))

    # Simple request-frequency tracking in session to model behavioral pressure.
    session["request_count"] = session.get("request_count", 0) + 1
    request_frequency = session["request_count"]

    risk_score, _ = calculate_risk_score(keyword, request_frequency)
    classification = classify_request(risk_score)

    if classification == "Normal":
        action = "Redirect: Real Website"
        append_log(keyword, risk_score, classification, action)
        return redirect(f"https://www.google.com/search?q={keyword}")

    # Abnormal traffic is silently rerouted to deception environment.
    session["in_decoy"] = True
    action = "Redirect: Decoy Website"
    append_log(keyword, risk_score, classification, action)
    return redirect(url_for("decoy"))


@app.route("/decoy", methods=["GET", "POST"])
def decoy():
    ensure_session_id()

    fake_results = []
    search_term = ""

    if request.method == "POST":
        search_term = request.form.get("decoy_keyword", "").strip()
        if search_term:
            append_decoy_log(search_term)
            fake_results = [
                {
                    "title": f"{search_term.title()} Security Overview",
                    "url": f"www.{search_term.lower().replace(' ', '')}-insights.net",
                    "summary": "Comprehensive report discussing latest behavior-based intrusion scenarios and mitigation guidance.",
                },
                {
                    "title": f"{search_term.title()} Technical Documentation",
                    "url": f"docs.{search_term.lower().replace(' ', '')}.org",
                    "summary": "Reference documents, white papers, and implementation templates for secure architecture workflows.",
                },
                {
                    "title": f"Top 10 {search_term.title()} Best Practices",
                    "url": f"cyber-journal.example/{search_term.lower().replace(' ', '-')}",
                    "summary": "Academic style article listing proven defensive controls used in educational and enterprise networks.",
                },
            ]

    return render_template("decoy.html", fake_results=fake_results, search_term=search_term)


@app.route("/dashboard", methods=["GET"])
def dashboard():
    logs = read_logs()

    total_requests = 0
    total_normal = 0
    total_abnormal = 0

    for entry in logs:
        if "|" in entry and "Decoy Search" not in entry:
            total_requests += 1
            if "| Normal |" in entry:
                total_normal += 1
            elif "| Abnormal |" in entry:
                total_abnormal += 1

    return render_template(
        "dashboard.html",
        logs=logs,
        total_requests=total_requests,
        total_normal=total_normal,
        total_abnormal=total_abnormal,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
