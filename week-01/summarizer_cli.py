# summarizer_cli.py
import sys
import argparse
from wrapper import GeminiWrapper

PROMPT_TEMPLATE = """Analyze the following text and return exactly three sections:

SUMMARY: (2-3 sentence summary)
KEY POINTS: (3-5 bullet points)
SENTIMENT: (one word: Positive, Negative, or Neutral, plus a one-sentence justification)

Text to analyze:
---
{text}
---
"""


def read_input(args):
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            return f.read()
    elif args.text:
        return args.text
    else:
        print("Error: provide --file or --text")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Summarize text using Gemini.")
    parser.add_argument("--file", help="Path to a text file to summarize")
    parser.add_argument("--text", help="Raw text to summarize (as a command-line argument)")
    args = parser.parse_args()

    text = read_input(args)
    wrapper = GeminiWrapper()

    result, error = wrapper.send_message(PROMPT_TEMPLATE.format(text=text), temperature=0.3)

    if error:
        print(f"Failed to summarize: {error}")
        sys.exit(1)

    print(result)


if __name__ == "__main__":
    main()