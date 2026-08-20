import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


class SentimentResult(BaseModel):
    sentiment: str
    confidence: float
    reason: str


def get_structured_response(prompt: str, schema: type[BaseModel], model="gemini-3.5-flash-lite", max_retries=3):
    """Ask Gemini for JSON matching `schema`, validate it, retry on failure."""
    for attempt in range(1, max_retries + 1):
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        try:
            data = json.loads(response.text)
            validated = schema.model_validate(data)
            return validated, None
        except (json.JSONDecodeError, ValidationError) as e:
            print(f"Attempt {attempt} failed validation: {e}")
            if attempt == max_retries:
                return None, f"Failed after {max_retries} attempts: {e}"

    return None, "Unknown failure"


if __name__ == "__main__":
    result, error = get_structured_response(
        "Analyze the sentiment of: 'This internship has taught me so much in just two weeks.'",
        SentimentResult,
    )
    if error:
        print("Error:", error)
    else:
        print(result.model_dump())