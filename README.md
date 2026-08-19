# VaultX AI Internship — Week 01: AI Foundations & Environment

Summer Internship Program 2026 — VaultX Cyber Tech, Artificial Intelligence Track

## Overview

This week's objective: get a working development environment, understand what a language model actually is, and ship a first program that calls one.

**Note on SDK substitution:** the brief specifies the Anthropic or OpenAI SDK. This submission uses the **Gemini API** (`google-genai` SDK) instead, with the `gemini-2.5-flash` model. All required functionality (API calls, token usage, error handling, retries) is implemented equivalently.

## Tech Stack

- Python 3.11+
- VS Code (Python extension)
- Git / GitHub
- `venv` for environment isolation
- `google-genai` (Gemini API SDK)
- `python-dotenv`

## Project Structure

```
vaultx-ai-internship/
└── week-01/
    ├── README.md
    ├── requirements.txt
    ├── .gitignore
    ├── .env.example
    ├── glossary.md              # Task 02 deliverable
    ├── first_call.py            # Task 03 deliverable
    ├── temperature_test.py      # Task 04 script
    ├── temperature_comparison.md # Task 04 deliverable
    ├── gemini_wrapper.py        # Task 05 deliverable
    └── summarizer_cli.py        # Task 06 deliverable
```

## Setup (Git Bash on Windows)

1. **Clone the repo**
   ```bash
   git clone https://github.com/<your-username>/vaultx-ai-internship.git
   cd vaultx-ai-internship/week-01
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/Scripts/activate
   ```
   You should see `(venv)` appear at the start of your prompt. If `python` isn't found, try `python3`.

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API key**
   - Get a key from [Google AI Studio](https://aistudio.google.com/apikey).
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Open `.env` and paste your key:
     ```
     GEMINI_API_KEY=your_key_here
     ```
   - `.env` is git-ignored and will never be committed.

## Running Each Task

**Task 03 — First API call**
```bash
python first_call.py
```
Prints the model's response, token usage, and estimated cost of the call.

**Task 04 — Generation parameters**
```bash
python temperature_test.py
```
Runs the same prompt at temperature 0, 0.7, and 1.0 (three times each) and prints all outputs for comparison.

**Task 05 — Reusable wrapper**
```bash
python gemini_wrapper.py
```
Runs a self-test of the `GeminiWrapper` class (retry, timeout, and token-tracking logic). Imported by `summarizer_cli.py`.

**Task 06 — CLI summarizer tool**
```bash
python summarizer_cli.py --text "Paste any paragraph here..."
python summarizer_cli.py --file sample_article.txt
```
Returns a summary, key points, and sentiment for the given input.

## Deliverables

| # | Deliverable | File |
|---|---|---|
| 1 | GitHub repo with venv, requirements.txt, .gitignore | this repo |
| 2 | AI terminology glossary (9 terms, own words) | `glossary.md` |
| 3 | First API call script with token & cost output | `first_call.py` |
| 4 | Temperature comparison table with analysis | `temperature_comparison.md` |
| 5 | Reusable API wrapper with error handling | `gemini_wrapper.py` |
| 6 | CLI summarizer tool + demo video | `summarizer_cli.py` + demo recording |

## Secrets Policy

No API keys are committed to this repository. `.env` is listed in `.gitignore`; `.env.example` documents the required variable name only.

## Git Log

Commits were made incrementally throughout the week (environment setup → glossary → first API call → temperature experiment → wrapper → CLI tool), rather than as a single end-of-week commit.
