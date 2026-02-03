import json
import re
from datetime import datetime
from pathlib import Path

from flask import Flask, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset.json"
LOG_PATH = BASE_DIR / "logs.txt"

app = Flask(__name__)
app.secret_key = "bmrt-major-project-key"


def load_rules():
    with DATASET_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def is_abnormal_input(keyword: str, rules: dict) -> bool:
    keyword = keyword.strip().lower()
    if not keyword:
        return True

    if any(char in keyword for char in rules["special_characters"]):
        return True

    for sensitive in rules["sensitive_keywords"]:
        if sensitive in keyword:
            return True

    if not re.fullmatch(rules["allowed_pattern"], keyword):
        return True

    return False


def log_abnormal(keyword: str, destination: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] keyword={keyword} destination={destination}\n"
    with LOG_PATH.open("a", encoding="utf-8") as file:
        file.write(entry)


def get_destination(keyword: str) -> str:
    keyword = keyword.strip().lower()
    if "google" in keyword:
        return "fake_google"
    if "youtube" in keyword:
        return "fake_youtube"
    if "amazon" in keyword:
        return "fake_amazon"
    return "fake_generic"


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    rules = load_rules()
    keyword = request.form.get("keyword", "").strip()

    if session.get("abnormal"):
        destination = get_destination(keyword)
        return redirect(url_for(destination))

    if is_abnormal_input(keyword, rules):
        session["abnormal"] = True
        destination = get_destination(keyword)
        log_abnormal(keyword, destination)
        return redirect(url_for(destination))

    normalized = keyword.lower()
    if normalized == "google":
        return redirect("https://www.google.com")
    if normalized == "youtube":
        return redirect("https://www.youtube.com")
    if normalized == "amazon":
        return redirect("https://www.amazon.com")

    session["abnormal"] = True
    destination = "fake_generic"
    log_abnormal(keyword, destination)
    return redirect(url_for(destination))


@app.route("/fake/google", methods=["GET", "POST"])
def fake_google():
    if session.get("abnormal") and request.method == "POST":
        query = request.form.get("query", "")
        return redirect(url_for("fake_google_results", q=query))
    return render_template("fake_google.html")


@app.route("/fake/google/results", methods=["GET"])
def fake_google_results():
    query = request.args.get("q", "")
    results = [
        {
            "title": f"{query.title()} - Official Resources",
            "url": f"{query}.edu/resources",
            "description": "Find official resources, documentation, and trusted references in one place.",
        },
        {
            "title": f"{query.title()} Research Archive",
            "url": f"archive.{query}.org",
            "description": "Browse curated articles, research summaries, and academic reports.",
        },
        {
            "title": f"{query.title()} Community Hub",
            "url": f"community.{query}.net",
            "description": "Join discussions, explore guides, and connect with verified contributors.",
        },
        {
            "title": f"{query.title()} Tutorials",
            "url": f"learn.{query}.com",
            "description": "Step-by-step tutorials and learning paths tailored for professionals.",
        },
    ]
    return render_template("fake_google_results.html", query=query, results=results)


@app.route("/fake/youtube", methods=["GET"])
def fake_youtube():
    selected = request.args.get("video")
    videos = [
        {
            "id": "1",
            "title": "Behavior Analytics in Cyber Defense",
            "channel": "SecureLab",
            "views": "1.2M views",
            "duration": "18:42",
        },
        {
            "id": "2",
            "title": "Deception Techniques for Web Security",
            "channel": "Cyber Insight",
            "views": "856K views",
            "duration": "12:05",
        },
        {
            "id": "3",
            "title": "Threat Hunting with Rule-Based Signals",
            "channel": "Digital Shield",
            "views": "620K views",
            "duration": "22:11",
        },
        {
            "id": "4",
            "title": "Building Secure Sandboxed Environments",
            "channel": "NetAcademy",
            "views": "410K views",
            "duration": "15:09",
        },
    ]
    current_video = next((video for video in videos if video["id"] == selected), None)
    return render_template("fake_youtube.html", videos=videos, current_video=current_video)


@app.route("/fake/amazon", methods=["GET"])
def fake_amazon():
    products = [
        {
            "name": "SecureKey Mechanical Keyboard",
            "price": "$79.99",
            "rating": "4.7",
            "reviews": "2,140",
        },
        {
            "name": "Sentinel Pro Webcam",
            "price": "$59.50",
            "rating": "4.5",
            "reviews": "1,320",
        },
        {
            "name": "Guardian Noise-Cancel Headset",
            "price": "$129.00",
            "rating": "4.8",
            "reviews": "3,845",
        },
        {
            "name": "Vault USB Security Token",
            "price": "$45.25",
            "rating": "4.6",
            "reviews": "985",
        },
    ]
    return render_template("fake_amazon.html", products=products)


@app.route("/fake/generic", methods=["GET"])
def fake_generic():
    return render_template("fake_generic.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
