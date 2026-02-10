# An Intelligent Cyber Defense Framework for Behavior-Based Intrusion Detection and Automated Attack Mitigation

## Project Concept
This project is a production-style Flask web application for academic cyber-defense demonstration. The framework inspects user-entered website keywords, classifies behavior with **strict rule-based logic** (no AI/ML), and performs automated redirection:

- **Normal behavior** -> real websites (Google, YouTube, Amazon)
- **Abnormal behavior** -> realistic internal fake clones

Once a session is marked abnormal, all later navigation is contained in the fake website environment.

## Key Features
- Rule-based behavior detection from `dataset.json`
- Session-level abnormal-user containment
- Realistic dark-theme fake website clones:
  - Google-like search
  - YouTube-like video listing
  - Amazon-like product listing
  - Generic modern dark landing for unknown abnormal inputs
- File-based logging in `logs.txt`
- No external APIs, no machine learning, no database

## Project Structure
```text
/project
 ├── app.py
 ├── dataset.json
 ├── logs.txt
 ├── templates/
 │    ├── index.html
 │    ├── fake_google.html
 │    ├── fake_youtube.html
 │    ├── fake_amazon.html
 │    └── fake_generic.html
 ├── static/
 │    ├── main.css
 │    ├── fake_google.css
 │    ├── fake_youtube.css
 │    └── fake_amazon.css
 └── README.md
```

## Behavior Rules
Rules are loaded from `dataset.json`.

### Normal examples
- `google`
- `youtube`
- `amazon`

### Abnormal examples
- `google/`
- `admin`
- `login`
- `..//`
- Inputs with symbols like `?`, `%`, `=`

### Evaluation logic
Input is abnormal when any of the following is true:
1. Contains special/suspicious characters
2. Contains restricted keywords
3. Fails allowed regex pattern
4. Not in allowed keyword list
5. Repeated suspicious attempts in session exceed threshold

## How Deception Works
1. User submits keyword from the index page.
2. Flask evaluates keyword against JSON rules.
3. If normal: user is redirected to the real site.
4. If abnormal: user is routed to a matching fake clone.
5. Session flag (`is_abnormal`) is set.
6. `before_request` enforces containment inside fake routes.

## Logging
`logs.txt` stores entries with:
- timestamp
- entered keyword
- classification (`normal`/`abnormal`)
- destination route/URL

Sample format:
```text
[2026-03-06 14:30:11] keyword=google/ classification=abnormal destination=fake_google
```

## Run Instructions
1. (Optional) Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install Flask:
```bash
pip install Flask
```

3. Run app:
```bash
python app.py
```

4. Open:
```text
http://localhost:5000
```

## Notes for Academic Demonstration
- All detection logic is transparent and easy to explain in viva/demo.
- UI is dark cyber-themed and polished for project screenshots.
- Code is modular and commented for readability.
