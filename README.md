# An Intelligent Cyber Defense Framework for Behavior-Based Intrusion Detection and Automated Attack Mitigation

## 1) Project Overview
This project is a complete Flask-based cyber deception framework for academic demonstration.
It performs **rule-based behavior analysis** (no AI/ML), then:
- Redirects normal users to real websites.
- Redirects abnormal users to realistic decoy environments.
- Keeps abnormal users trapped inside internal fake websites.
- Logs all activities to `logs.txt`.

## 2) Folder Structure
```text
app.py
dataset.json
logs.txt
README.md

templates/
  index.html
  fake_google.html
  fake_google_results.html
  fake_youtube.html
  fake_amazon.html
  fake_generic.html

static/
  style.css
  fake_google.css
  fake_youtube.css
  fake_amazon.css
```

## 3) Installation & Setup
1. Create and activate virtual environment (optional but recommended):
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

2. Install dependency:
```bash
pip install Flask
```

3. Run the application:
```bash
python app.py
```

4. Open in browser:
```text
http://localhost:5000
```

## 4) Behavior Rules (dataset.json)
`dataset.json` defines all rule logic:
- `allowed_keywords`: approved keywords (`google`, `youtube`, `amazon`)
- `abnormal_symbols`: suspicious symbols (`/`, `..`, `?`, etc.)
- `restricted_keywords`: sensitive terms (`admin`, `config`, `password`, etc.)
- `allowed_pattern`: alphanumeric regex
- `suspicious_behavior_rules`: human-readable rule descriptions

### Classification Logic
Input is **abnormal** if at least one condition is true:
1. Contains suspicious symbols.
2. Contains restricted keyword.
3. Fails allowed regex pattern.
4. Not in allowed keyword list.

Otherwise input is **normal**.

## 5) Application Modules (Flow Description)
1. **Input Module** (`index.html`)
   - User enters a website keyword.
2. **Analysis Module** (`/analyze` in `app.py`)
   - Loads JSON rules and classifies input.
3. **Decision Module**
   - Normal -> real site redirect.
   - Abnormal -> fake destination routing.
4. **Session Control Module** (`before_request`)
   - If abnormal once, user remains trapped in fake environment.
5. **Decoy Interface Module** (`templates/fake_*.html`)
   - Realistic fake Google/YouTube/Amazon/generic pages.
   - Local JavaScript simulation only.
6. **Logging Module** (`logs.txt`)
   - Records timestamp, keyword, classification, destination.

## 6) High-Level Architecture
- **Frontend Layer**: HTML + CSS + JavaScript for index and decoy UIs.
- **Flask Controller Layer**: routes, behavior classification, routing logic.
- **Rule Layer**: static JSON policy dataset (`dataset.json`).
- **Persistence Layer**: file-based logs (`logs.txt`) for behavior traces.

This architecture is lightweight, reproducible, and ideal for major-project demos.

## 7) Fake Website Behavior
- **Fake Google**: search home + internal results page.
- **Fake YouTube**: dynamic video list and local "Now Playing" simulation.
- **Fake Amazon**: dynamic product cards and local search filtering.
- **Fake Generic**: fallback decoy portal with internal navigation links.

No page calls external APIs. Navigation remains local for trapped sessions.

## 8) Logging Format
Example log entry:
```text
[2026-01-01 14:20:11] keyword=google/ classification=abnormal destination=fake_google
```

Fields:
- timestamp
- keyword
- classification (normal/abnormal)
- destination

## 9) Academic Notes
- No machine learning or AI libraries used.
- No database used.
- Fully rule-driven behavior analysis.
- Suitable for classroom demo, viva, and report documentation.
