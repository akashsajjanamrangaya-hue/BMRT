from datetime import datetime
from pathlib import Path
from uuid import uuid4

from flask import Flask, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "logs.txt"

app = Flask(__name__)
app.secret_key = "research-prototype-cyber-defense-key"


def ensure_session_id() -> str:
    """Create a short stable session id for each visitor."""
    if "session_id" not in session:
        session["session_id"] = str(uuid4())[:8]
    return session["session_id"]


def now() -> datetime:
    return datetime.now()


def timestamp_str(ts: datetime | None = None) -> str:
    if ts is None:
        ts = now()
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def extract_special_characters(text: str) -> str:
    """Return unique special characters used in input for behavior analytics."""
    chars = sorted({char for char in text if not char.isalnum() and not char.isspace()})
    return "".join(chars)


def calculate_risk_score(user_input: str, request_frequency: int) -> tuple[float, dict]:
    """
    Risk Score formula:
    RS = (0.4 × special_characters)
       + (0.3 × request_frequency)
       + (0.3 × suspicious_pattern_flag)
    """
    special_count = sum(1 for c in user_input if not c.isalnum() and not c.isspace())
    suspicious_pattern_flag = 1 if any(token in user_input for token in ("//", "..", "@@", "\\")) else 0

    risk_score = (0.4 * special_count) + (0.3 * request_frequency) + (0.3 * suspicious_pattern_flag)

    features = {
        "length": len(user_input),
        "special_count": special_count,
        "special_chars": extract_special_characters(user_input),
        "request_frequency": request_frequency,
        "suspicious_pattern_flag": suspicious_pattern_flag,
    }
    return round(risk_score, 2), features


def classify_request(risk_score: float) -> str:
    return "Abnormal" if risk_score > 3 else "Normal"


def append_log(
    *,
    session_id: str,
    user_input: str,
    length: int,
    special_chars: str,
    time_delta: str,
    interaction_count: int,
    context: str,
    timestamp: datetime | None = None,
) -> None:
    """
    Required format:
    [Timestamp] | SessionID | Input | Length | SpecialChars | TimeDelta | InteractionCount | Context
    """
    line = (
        f"[{timestamp_str(timestamp)}] | {session_id} | {user_input} | {length} | {special_chars} | "
        f"{time_delta} | {interaction_count} | {context}\n"
    )
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(line)


def get_time_delta_seconds() -> float:
    """Seconds between current interaction and previous interaction in session."""
    current_ts = now().timestamp()
    previous_ts = session.get("last_input_ts")
    session["last_input_ts"] = current_ts

    if previous_ts is None:
        return 0.0
    return round(current_ts - previous_ts, 3)


def increment_interaction_count() -> int:
    session["interaction_count"] = session.get("interaction_count", 0) + 1
    return session["interaction_count"]


def increment_decoy_search_count() -> int:
    session["decoy_search_count"] = session.get("decoy_search_count", 0) + 1
    return session["decoy_search_count"]


def build_fake_results(query: str, page: int) -> list[dict]:
    """Generate pagination-style decoy results for the deception interface."""
    start = (page - 1) * 5 + 1
    results = []
    for idx in range(start, start + 5):
        results.append(
            {
                "title": f"{query.title()} Knowledge Node {idx}",
                "url": f"https://node-{idx}.{query.lower().replace(' ', '-')}.lab",
                "summary": "Indexed reference entry with archived notes, cross-links, and behavior intelligence metadata.",
            }
        )
    return results


def parse_logs() -> list[dict]:
    """Read structured logs into dictionaries for dashboard rendering."""
    if not LOG_FILE.exists():
        return []

    records = []
    for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 8:
            continue

        records.append(
            {
                "timestamp": parts[0].strip("[]"),
                "session_id": parts[1],
                "input": parts[2],
                "length": parts[3],
                "special_chars": parts[4],
                "time_delta": parts[5],
                "interaction_count": parts[6],
                "context": parts[7],
                "raw": line,
            }
        )

    return list(reversed(records))


@app.route("/")
def index():
    ensure_session_id()
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    session_id = ensure_session_id()

    user_input = request.form.get("keyword", "").strip()
    if not user_input:
        return redirect(url_for("index"))

    session["request_frequency"] = session.get("request_frequency", 0) + 1
    request_frequency = session["request_frequency"]
    interaction_count = increment_interaction_count()
    time_delta = get_time_delta_seconds()

    risk_score, features = calculate_risk_score(user_input, request_frequency)
    classification = classify_request(risk_score)

    context = f"ANALYZE_{classification.upper()}|RS={risk_score}|FREQ={request_frequency}|FLAG={features['suspicious_pattern_flag']}"
    append_log(
        session_id=session_id,
        user_input=user_input,
        length=features["length"],
        special_chars=features["special_chars"] or "none",
        time_delta=str(time_delta),
        interaction_count=interaction_count,
        context=context,
    )

    if classification == "Normal":
        return redirect(f"https://example.org/search?q={user_input}")

    session["in_decoy"] = True
    return redirect(url_for("decoy"))


@app.route("/decoy", methods=["GET", "POST"])
def decoy():
    session_id = ensure_session_id()
    page = int(request.args.get("page", 1))
    if page < 1:
        page = 1

    query = ""
    results = []

    if request.method == "POST":
        query = request.form.get("decoy_input", "").strip()
        if query:
            decoy_search_count = increment_decoy_search_count()
            interaction_count = increment_interaction_count()
            time_delta = get_time_delta_seconds()
            special_chars = extract_special_characters(query) or "none"

            append_log(
                session_id=session_id,
                user_input=query,
                length=len(query),
                special_chars=special_chars,
                time_delta=str(time_delta),
                interaction_count=interaction_count,
                context=f"DECOY_SEARCH|SEARCH_COUNT={decoy_search_count}|PAGE={page}",
            )

            results = build_fake_results(query, page)

    return render_template(
        "decoy.html",
        query=query,
        results=results,
        page=page,
        has_next=True,
        has_prev=page > 1,
    )


@app.route("/dashboard")
def dashboard():
    records = parse_logs()

    analyze_records = [r for r in records if r["context"].startswith("ANALYZE_")]
    abnormal_records = [r for r in analyze_records if "ANALYZE_ABNORMAL" in r["context"]]

    total_requests = len(analyze_records)
    abnormal_percentage = round((len(abnormal_records) / total_requests) * 100, 2) if total_requests else 0.0

    sessions = {}
    for rec in records:
        sid = rec["session_id"]
        sessions[sid] = sessions.get(sid, 0) + 1

    session_behavior = sorted(sessions.items(), key=lambda x: x[1], reverse=True)[:8]

    return render_template(
        "dashboard.html",
        total_requests=total_requests,
        abnormal_percentage=abnormal_percentage,
        session_behavior=session_behavior,
        records=records,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
