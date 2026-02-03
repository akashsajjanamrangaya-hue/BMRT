# Behavior-Based Cyber Deception System with Automated Fake Website Cloning

This Flask application demonstrates a rule-based cyber deception workflow for academic research. It routes normal users to real websites while trapping abnormal behavior inside realistic, internal clone environments.

## Project Structure

```
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

## How to Run

1. Install dependencies:

```bash
pip install Flask
```

2. Start the server:

```bash
python app.py
```

3. Open your browser at:

```
http://localhost:5000
```

## Detection Logic (Rule-Based)

- Rules are stored in `dataset.json`.
- Inputs are marked abnormal when they:
  - Contain special characters such as `/`, `..`, or `?`.
  - Include sensitive keywords like `admin` or `config`.
  - Fail the allowed alphanumeric pattern.
- No machine learning or external services are used.

## Fake Website Behavior

- Once a user is marked abnormal, the session is locked into the fake environment.
- Fake Google includes a working search box and internal results pages.
- Fake YouTube shows video listings and opens internal video views.
- Fake Amazon shows professional product cards with pricing and add-to-cart buttons.
- All fake pages are internal, with no external escape links.

## Logging

Abnormal activity is recorded in `logs.txt` with timestamps, the submitted keyword, and the destination fake site.
