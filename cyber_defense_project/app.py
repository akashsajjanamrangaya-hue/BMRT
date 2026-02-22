from datetime import datetime
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

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


def append_decoy_search_log(keyword: str) -> None:
    """Append decoy search log with session details."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session_id = ensure_session_id()
    entry = f"[{timestamp}] | Decoy Search | {keyword} | Session={session_id}\n"
    with LOG_FILE.open("a", encoding="utf-8") as log_file:
        log_file.write(entry)


def append_decoy_action_log(action: str, value: str = "") -> None:
    """Append detailed activity for user behavior inside decoy site."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session_id = ensure_session_id()
    entry = f"[{timestamp}] | Decoy Action | {action} | {value} | Session={session_id}\n"
    with LOG_FILE.open("a", encoding="utf-8") as log_file:
        log_file.write(entry)


def append_abnormal_step_log(step: str, value: str = "") -> None:
    """Store each minute step of abnormal behavior pipeline for analysis."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session_id = ensure_session_id()
    entry = f"[{timestamp}] | Abnormal Step | {step} | {value} | Session={session_id}\n"
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

    risk_score, features = calculate_risk_score(keyword, request_frequency)
    classification = classify_request(risk_score)

    if classification == "Normal":
        action = "Redirect: Real Website"
        append_log(keyword, risk_score, classification, action)
        return redirect(f"https://www.google.com/search?q={keyword}")

    # Each step of abnormal path is logged for cyber-forensic review.
    append_abnormal_step_log("received_keyword", keyword)
    append_abnormal_step_log(
        "calculated_features",
        f"len={features['keyword_length']},special={features['special_characters']},freq={features['request_frequency']},flag={features['suspicious_pattern_flag']}",
    )
    append_abnormal_step_log("calculated_risk_score", str(risk_score))
    append_abnormal_step_log("classified", classification)

    # Abnormal traffic is silently rerouted to deception environment.
    session["in_decoy"] = True
    action = "Redirect: Decoy Website"
    append_log(keyword, risk_score, classification, action)
    append_abnormal_step_log("redirected_to_decoy", url_for("decoy"))
    append_decoy_action_log("entered_decoy", keyword)
    return redirect(url_for("decoy"))


@app.route("/decoy", methods=["GET", "POST"])
def decoy():
    ensure_session_id()

    fake_results = []
    search_term = ""

    if session.get("in_decoy") and request.method == "GET":
        append_decoy_action_log("decoy_page_view", "home")

    if request.method == "POST":
        search_term = request.form.get("decoy_keyword", "").strip()
        if search_term:
            append_decoy_search_log(search_term)
            append_decoy_action_log("submitted_search", search_term)
            fake_results = [
                {
                    "title": f"{search_term.title()} - Google Search",
                    "url": f"https://www.{search_term.lower().replace(' ', '')}.com",
                    "summary": "Trusted pages, official resources, and web references related to your search query.",
                },
                {
                    "title": f"{search_term.title()} - Wikipedia",
                    "url": f"https://en.wikipedia.org/wiki/{search_term.lower().replace(' ', '_')}",
                    "summary": "Free encyclopedia article with background information, references, and related links.",
                },
                {
                    "title": f"Latest news on {search_term.title()}",
                    "url": f"https://news.google.com/search?q={search_term.lower().replace(' ', '%20')}",
                    "summary": "Recent news highlights, timeline events, and important updates from multiple publishers.",
                },
            ]

    return render_template("decoy.html", fake_results=fake_results, search_term=search_term)


@app.route("/decoy/action", methods=["POST"])
def decoy_action():
    """Receive asynchronous decoy interactions (keypress/click) from front-end."""
    ensure_session_id()

    payload = request.get_json(silent=True) or {}
    action = str(payload.get("action", "unknown_action"))[:80]
    value = str(payload.get("value", ""))[:200]
    append_decoy_action_log(action, value)
    return jsonify({"status": "ok"})


@app.route("/dashboard", methods=["GET"])
def dashboard():
    logs = read_logs()

    total_requests = 0
    total_normal = 0
    total_abnormal = 0
    total_decoy_actions = 0
    total_abnormal_steps = 0

    for entry in logs:
        if "| Decoy Action |" in entry:
            total_decoy_actions += 1
        if "| Abnormal Step |" in entry:
            total_abnormal_steps += 1
        if "|" in entry and "Decoy Search" not in entry and "Decoy Action" not in entry and "Abnormal Step" not in entry:
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
        total_decoy_actions=total_decoy_actions,
        total_abnormal_steps=total_abnormal_steps,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
