import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents="Explain what a context window is in one sentence."
)

print("--- Response ---")
print(response.text)

usage = response.usage_metadata
print("\n--- Token usage ---")
print(f"Input tokens:  {usage.prompt_token_count}")
print(f"Output tokens: {usage.candidates_token_count}")
print(f"Total tokens:  {usage.total_token_count}")

INPUT_RATE = 0.30 / 1_000_000
OUTPUT_RATE = 2.50 / 1_000_000

cost = (usage.prompt_token_count * INPUT_RATE) + (usage.candidates_token_count * OUTPUT_RATE)
print(f"Estimated cost: ${cost:.8f}")
