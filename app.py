import json
import re
import socket
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset.json"
LOG_PATH = BASE_DIR / "logs.txt"

app = Flask(__name__)
app.secret_key = "research-deception-framework-key"


def load_rules() -> dict:
    """Load rule-based detection settings."""
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def now_utc() -> datetime:
    return datetime.utcnow()


def ensure_abnormal_session() -> str:
    """Create and store a unique session identifier for abnormal sessions."""
    sid = session.get("abnormal_session_id")
    if not sid:
        sid = f"Session_{uuid.uuid4().hex[:8]}"
        session["abnormal_session_id"] = sid
        session["abnormal_started_at"] = now_utc().isoformat()
        session["last_action_at"] = now_utc().isoformat()
    return sid


def parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def timing_metrics() -> tuple[float, float]:
    """Return (seconds_between_actions, session_duration_seconds)."""
    current = now_utc()
    last = parse_iso(session.get("last_action_at"))
    started = parse_iso(session.get("abnormal_started_at"))

    between = (current - last).total_seconds() if last else 0.0
    duration = (current - started).total_seconds() if started else 0.0

    session["last_action_at"] = current.isoformat()
    return round(max(between, 0.0), 3), round(max(duration, 0.0), 3)


def log_entry(
    session_id: str,
    entered_keyword: str,
    page: str,
    action: str,
    input_value: str,
    classification: str,
) -> None:
    """Write structured monitoring line to logs.txt."""
    timestamp = now_utc().strftime("%Y-%m-%d %H:%M:%S")
    between, duration = timing_metrics() if classification == "abnormal" else (0.0, 0.0)
    line = (
        f"{timestamp} | {session_id} | {entered_keyword} | {page} | {action} | "
        f"{input_value} | between={between}s | session={duration}s | {classification}\n"
    )
    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(line)


def looks_like_domain_keyword(keyword: str) -> bool:
    """Domain-like keyword: letters/numbers/hyphen with no spaces."""
    return bool(re.fullmatch(r"[a-z0-9-]+", keyword))


def domain_exists(hostname: str) -> bool:
    try:
        socket.gethostbyname(hostname)
        return True
    except OSError:
        return False


def normal_redirect_target(keyword: str) -> str:
    """Redirect normal traffic to real websites with search fallback."""
    cleaned = keyword.strip().lower()
    if looks_like_domain_keyword(cleaned):
        host = f"www.{cleaned}.com"
        if domain_exists(host):
            return f"https://{host}"
    return f"https://www.google.com/search?q={quote_plus(cleaned)}"


def resolve_fake_site(keyword: str) -> str:
    """Map suspicious intent to realistic high-interaction clone."""
    k = keyword.strip().lower()
    if "google" in k or "search" in k:
        return "fake_google"
    if "youtube" in k or "video" in k:
        return "fake_youtube"
    if "amazon" in k or "shop" in k:
        return "fake_amazon"
    return "fake_dynamic"


def extract_site_hint(keyword: str) -> str:
    """Extract a safe site-like token for dynamic clone rendering."""
    cleaned = re.sub(r"[^a-zA-Z0-9 -]", " ", keyword).strip().lower()
    if not cleaned:
        return "Web"
    token = cleaned.split()[0]
    return token[:24].title()


def classify_keyword(keyword: str, rules: dict) -> tuple[str, list[str]]:
    """Rule-based classification: only clear suspicious patterns become abnormal."""
    cleaned = keyword.strip().lower()
    reasons: list[str] = []

    if not cleaned:
        reasons.append("empty_input")

    if any(token in cleaned for token in rules["abnormal_patterns"]["special_characters"]):
        reasons.append("special_characters")

    if any(word in cleaned for word in rules["abnormal_patterns"]["restricted_keywords"]):
        reasons.append("restricted_keyword")

    if not re.fullmatch(rules["allowed_pattern"], cleaned):
        reasons.append("pattern_mismatch")

    if session.get("suspicious_count", 0) >= rules["thresholds"]["repeat_suspicious_count"]:
        reasons.append("repeated_suspicious_inputs")

    return ("abnormal", reasons) if reasons else ("normal", [])


@app.before_request
def trap_abnormal_sessions():
    """Once abnormal, keep session inside local high-interaction environment."""
    if not session.get("is_abnormal"):
        return None

    allowed = {
        "analyze",
        "interaction_log",
        "analytics",
        "fake_google",
        "fake_youtube",
        "fake_amazon",
        "fake_generic",
        "fake_dynamic",
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
    session["entered_keyword"] = keyword

    if session.get("is_abnormal"):
        sid = ensure_abnormal_session()
        destination = resolve_fake_site(keyword)
        log_entry(sid, keyword, destination, "navigation", "post_analyze", "abnormal")
        if destination == "fake_dynamic":
            return redirect(url_for("fake_dynamic", site_name=extract_site_hint(keyword)))
        return redirect(url_for(destination))

    classification, reasons = classify_keyword(keyword, rules)
    if classification == "normal":
        target = normal_redirect_target(keyword)
        session["suspicious_count"] = 0
        log_entry("Session_Normal", keyword, "gateway", "redirect", target, "normal")
        return redirect(target)

    session["is_abnormal"] = True
    session["suspicious_count"] = session.get("suspicious_count", 0) + 1
    session["abnormal_reasons"] = reasons
    sid = ensure_abnormal_session()
    destination = resolve_fake_site(keyword)
    log_entry(sid, keyword, destination, "classification", ",".join(reasons), "abnormal")
    if destination == "fake_dynamic":
        return redirect(url_for("fake_dynamic", site_name=extract_site_hint(keyword)))
    return redirect(url_for(destination))


@app.route("/interaction", methods=["POST"])
def interaction_log():
    """Receive frontend interaction events via AJAX and store behavior trace."""
    if not session.get("is_abnormal"):
        return jsonify({"status": "ignored"})

    payload = request.get_json(silent=True) or {}
    sid = ensure_abnormal_session()
    entered_keyword = session.get("entered_keyword", "-")

    page = str(payload.get("page", "unknown"))[:80]
    action = str(payload.get("action", "unknown"))[:120]
    value = str(payload.get("value", ""))[:120]

    log_entry(sid, entered_keyword, page, action, value, "abnormal")
    return jsonify({"status": "ok"})


@app.route("/analytics", methods=["GET"])
def analytics():
    """Read-only aggregated analytics for abnormal behavior monitoring."""
    session_counts: Counter[str] = Counter()
    keyword_counts: Counter[str] = Counter()
    month_counts: Counter[str] = Counter()

    for line in LOG_PATH.read_text(encoding="utf-8").splitlines() if LOG_PATH.exists() else []:
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 9:
            continue
        timestamp, sid, keyword, *_rest, classification = parts
        if classification != "abnormal":
            continue

        session_counts[sid] += 1
        if keyword and keyword != "-":
            keyword_counts[keyword.lower()] += 1

        try:
            month_counts[datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m")] += 1
        except ValueError:
            continue

    top_terms = [term for term, _ in keyword_counts.most_common(5)]
    month_labels = sorted(month_counts.keys())
    month_values = [month_counts[m] for m in month_labels]

    return render_template(
        "analytics.html",
        total_abnormal_sessions=len(session_counts),
        interactions_by_session=dict(session_counts),
        top_terms=top_terms,
        month_labels=month_labels,
        month_values=month_values,
    )


@app.route("/fake/google", methods=["GET"])
def fake_google():
    return render_template("fake_google.html")


@app.route("/fake/youtube", methods=["GET"])
def fake_youtube():
    video = request.args.get("video", "")
    return render_template("fake_youtube.html", video=video)


@app.route("/fake/amazon", methods=["GET"])
def fake_amazon():
    product = request.args.get("product", "")
    return render_template("fake_amazon.html", product=product)


@app.route("/fake/site/<site_name>", methods=["GET"])
def fake_dynamic(site_name: str):
    safe = re.sub(r"[^a-zA-Z0-9 -]", "", site_name).strip()[:24] or "Web"
    return render_template("fake_dynamic.html", brand_name=safe.title())


@app.route("/fake/generic", methods=["GET"])
def fake_generic():
    return render_template("fake_generic.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
