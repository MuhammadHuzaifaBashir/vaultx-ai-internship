import argparse
from wrapper import GeminiWrapper


def summarise(text, client):
    prompt = f"""Analyze the following text and return exactly three sections:
1. Summary (2-3 sentences)
2. Key Points (bulleted list)
3. Sentiment (positive/negative/neutral, with a one-sentence reason)

Text:
{text}"""

    result = client.send_message(prompt, max_tokens=500)

    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print(result["text"])
    print(f"\n[Model used: {result['model_used']}]")
    print(f"[Tokens used — input: {result['input_tokens']}, output: {result['output_tokens']}]")


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