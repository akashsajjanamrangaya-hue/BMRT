# An Intelligent Cyber Defense Framework with High-Interaction Deception and Behavioral Monitoring

## Overview
This Flask application is a research-grade, defensive cyber deception framework for academic projects.
It uses **rule-based behavior analysis** (no AI/ML, no database) to classify user input and then:

- Redirects normal behavior to real external destinations.
- Redirects abnormal behavior to high-interaction local simulated environments.
- Tracks abnormal-session behavior events in detail for monitoring and analysis.

## Core Behavior Logic
### Normal Behavior
Input is treated as normal when it:
- contains letters/numbers/spaces/hyphens,
- does not include suspicious symbols (`/`, `..`, `?`, `%`, `=`, `#`),
- does not include restricted keywords (`admin`, `login`, `root`, `config`, etc.).

### Abnormal Behavior
Input is treated as abnormal when it includes:
- slash/path traversal patterns,
- restricted administrative words,
- special control/query symbols,
- repeated suspicious attempts in the same session.

## Redirection Rules
- **Normal -> real website**
  - tries `https://www.<keyword>.com`
  - falls back to `https://www.google.com/search?q=<keyword>` if domain is not resolvable
- **Abnormal -> local high-interaction simulated clone**
  - Search-like environment (`/fake/google`)
  - Video-like environment (`/fake/youtube`)
  - Shopping-like environment (`/fake/amazon`)
  - Generic hub (`/fake/generic`)
  - Dynamic brand-like clone (`/fake/site/<site_name>`) for other abnormal website intents

## High-Interaction Deception Features
Inside abnormal flow, the system simulates:
- search interactions,
- navigation actions,
- clickable content,
- login form attempts,
- product and video interactions,
- local-only route transitions.

No copyrighted assets or external site resources are used.

## Full Behavioral Monitoring
For abnormal sessions, frontend JavaScript sends interaction events to Flask using AJAX (`/interaction`).
Tracked actions include:
- page visits,
- button/link clicks,
- typed search terms,
- form submissions,
- navigation changes,
- timing between actions,
- session duration progression.

## Log Format (`logs.txt`)
Each log line stores:
- timestamp
- session ID
- entered keyword
- page
- action
- input value
- time between actions
- session duration
- classification

Example:
```text
2025-01-19 14:32:10 | Session_4839 | google/ | fake_search | typed | admin panel | between=1.44s | session=18.23s | abnormal
```

## Analytics Page (`/analytics`)
Read-only analytics dashboard includes:
- total abnormal sessions,
- interactions per abnormal session,
- most searched keywords (top aggregated terms),
- monthly abnormal trend graph (Canvas chart).

The analytics view avoids exposing raw full sensitive input traces.

## Project Structure
```text
/project
  app.py
  dataset.json
  logs.txt
  templates/
    index.html
    fake_google.html
    fake_youtube.html
    fake_amazon.html
    fake_generic.html
    analytics.html
    fake_dynamic.html
  static/
    main.css
    fake_google.css
    fake_youtube.css
    fake_amazon.css
    analytics.css
    fake_dynamic.css
    tracker.js
  README.md
```

## Run Instructions
```bash
python -m venv .venv
source .venv/bin/activate
pip install Flask
python app.py
```
Open: `http://localhost:5000`

## Notes
- Defensive deception research use only.
- No ML/AI libraries.
- No database.
- Modular code with separated detection, routing, monitoring, and analytics responsibilities.
