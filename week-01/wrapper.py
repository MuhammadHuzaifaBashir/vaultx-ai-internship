# gemini_wrapper.py
import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError

load_dotenv()


class GeminiWrapper:
    def __init__(self, model="gemini-3.5-flash-lite", max_retries=3, timeout=30):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment. Check your .env file.")

        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.total_tokens_used = 0

    def send_message(self, prompt, temperature=0.7, system_instruction=None):
        """Send a prompt to Gemini with retry, timeout, and token tracking.
        Returns (text, error) — exactly one will be None."""
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction,
            http_options=types.HttpOptions(timeout=self.timeout * 1000),  # ms
        )

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config,
                )
                if response.usage_metadata:
                    self.total_tokens_used += response.usage_metadata.total_token_count
                return response.text, None

            except APIError as e:
                last_error = e
                status = getattr(e, "code", None)

                if status == 429:  # rate limit
                    wait = 2 ** attempt
                    print(f"Rate limited. Retrying in {wait}s... (attempt {attempt}/{self.max_retries})")
                    time.sleep(wait)
                elif status == 401 or status == 403:  # invalid key / auth
                    return None, f"Authentication error — check your API key: {e}"
                else:
                    wait = 2 ** attempt
                    print(f"API error ({status}). Retrying in {wait}s...")
                    time.sleep(wait)

            except Exception as e:
                # never crash the caller — always return a handled error
                last_error = e
                time.sleep(1)

        return None, f"Failed after {self.max_retries} attempts. Last error: {last_error}"


if __name__ == "__main__":
    wrapper = GeminiWrapper()
    text, error = wrapper.send_message("Say hello in five words.")
    if error:
        print("Error:", error)
    else:
        print("Response:", text)
        print("Total tokens used so far:", wrapper.total_tokens_used)