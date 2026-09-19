import argparse
from wrapper import GeminiWrapper


def summarise(text, client):
    prompt = f"""Analyze the following text and return exactly three sections:
1. Summary (2-3 sentences)
2. Key Points (bulleted list)
3. Sentiment (positive/negative/neutral, with a one-sentence reason)

Text:
{text}"""

    text_result, error = client.send_message(prompt)

    if error:
        print(f"Error: {error}")
        return

    print(text_result)
    print(f"\n[Model used: {client.model}]")
    print(f"[Tokens used — total: {client.total_tokens_used}]")


def main():
    parser = argparse.ArgumentParser(
        description="Summarise text, extract key points, and detect sentiment using Gemini."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Text to analyze directly")
    group.add_argument("--file", type=str, help="Path to a text file to analyze")
    args = parser.parse_args()

    client = GeminiWrapper()

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Error: file '{args.file}' not found.")
            return
    else:
        content = args.text

    summarise(content, client)


if __name__ == "__main__":
    main()