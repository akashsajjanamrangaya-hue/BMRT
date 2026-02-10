# An Intelligent Cyber Defense Framework for Behavior-Based Intrusion Detection and Automated Attack Mitigation

## Project Concept
This Flask application demonstrates a behavior-driven cyber defense gateway for academic research.
It classifies user-entered keywords with **rule-based logic only** (no AI/ML), then applies automated mitigation:

- **Normal behavior** -> redirect to real external websites.
- **Abnormal behavior** -> route into realistic internal cloned websites.

Once abnormal behavior is detected, the user session is contained in fake routes.

## Core Design Goals
- Do not rely on a hardcoded whitelist for normal users.
- Accept natural everyday keywords (for example: `weather`, `music`, `student portal`).
- Trigger deception only when clear malicious/suspicious patterns are detected.
- Keep logging silent and never show logs on the UI.

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

## Behavior Classification Rules (No AI/ML)
Rules are stored in `dataset.json`.

### Normal input
Input is considered normal when it:
- Uses letters/numbers/spaces/hyphens only.
- Does not contain suspicious symbols like `/`, `..`, `?`, `%`, `=`.
- Does not include restricted terms such as `admin`, `login`, `root`, `config`.

### Abnormal input
Input is considered abnormal when it:
- Contains path/query symbols (`/`, `..`, `//`, `?`, `%`, `=`, `#`).
- Includes restricted administrative words.
- Violates the allowed text pattern.
- Appears after repeated suspicious attempts in the same session.

## Redirection Logic
For **normal** input:
1. If input is domain-like and DNS resolves, redirect to:
   `https://www.<keyword>.com`
2. Otherwise fallback to:
   `https://www.google.com/search?q=<keyword>`

For **abnormal** input:
- Redirect to one of the internal realistic clones:
  - `/fake/google`
  - `/fake/youtube`
  - `/fake/amazon`
  - `/fake/generic`

## Session Containment
- Flask session flag: `is_abnormal`
- `before_request` guard ensures trapped users remain inside fake routes.
- Normal users are not impacted.

## Logging
`logs.txt` stores silent audit records with:
- timestamp
- entered keyword
- classification (`normal` / `abnormal`)
- redirection target

Example:
```text
[2026-03-06 14:30:11] keyword=google/ classification=abnormal target=fake_google
```

## How to Run
1. (Optional) Create venv:
```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependency:
```bash
pip install Flask
```

3. Start app:
```bash
python app.py
```

4. Open:
```text
http://localhost:5000
```

## Notes for Academic Demonstration
- The code is modular and commented for report/viva explanation.
- Deception behavior is realistic and invisible to normal users.
- No external APIs or databases are used.
