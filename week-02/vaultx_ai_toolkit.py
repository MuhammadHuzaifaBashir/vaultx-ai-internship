"""
structured_ai.py — VaultX Week 02, Task 06
Reusable, logged module for structured LLM output. Import this in future weeks
instead of rewriting API-calling logic from scratch.
"""

import os
import json
import logging
import time
from typing import Type, TypeVar
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from google import genai
from google.genai import types

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("structured_ai.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("structured_ai")

T = TypeVar("T", bound=BaseModel)

MODEL = "gemini-3.5-flash-lite"
_client = None


def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment.")
        _client = genai.Client(api_key=api_key)
    return _client


def get_structured_output(
    prompt: str,
    schema: Type[T],
    model: str = MODEL,
    max_retries: int = 3,
    system_instruction: str | None = None,
    rate_limit_delay: float = 4.0,
) -> tuple[T | None, str | None]:
    """
    Send a prompt to Gemini and get back validated structured output matching `schema`.
    Returns (validated_object, None) on success, or (None, error_message) on failure.
    Never raises — always returns a handled result.
    """
    client = get_client()
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
        system_instruction=system_instruction,
    )

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_retries} — model={model}")
            response = client.models.generate_content(model=model, contents=prompt, config=config)
            data = json.loads(response.text)
            validated = schema.model_validate(data)
            logger.info("Success — validated output received")
            time.sleep(rate_limit_delay)
            return validated, None

        except (json.JSONDecodeError, ValidationError) as e:
            last_error = f"Validation error: {e}"
            logger.warning(last_error)

        except Exception as e:
            last_error = str(e)
            if "RESOURCE_EXHAUSTED" in last_error or "429" in last_error:
                logger.warning(f"Rate limited. Waiting before retry... ({last_error[:100]})")
                time.sleep(20)
            else:
                logger.error(last_error)

        time.sleep(rate_limit_delay)

    logger.error(f"Failed after {max_retries} attempts: {last_error}")
    return None, last_error


def batch_process(items: list[str], schema: Type[T], prompt_builder, rate_limit_delay: float = 4.0) -> list[dict]:
    """
    Run get_structured_output across a list of raw inputs.
    prompt_builder: function that takes a raw input string and returns the full prompt.
    """
    results = []
    for i, item in enumerate(items, 1):
        prompt = prompt_builder(item)
        result, error = get_structured_output(prompt, schema, rate_limit_delay=rate_limit_delay)
        if error:
            results.append({"input": item, "error": error})
        else:
            results.append({"input": item, **result.model_dump()})
        logger.info(f"Processed {i}/{len(items)}")
    return results


if __name__ == "__main__":
    # Self-test
    from pydantic import BaseModel

    class QuickTest(BaseModel):
        sentiment: str
        confidence: float

    result, error = get_structured_output(
        "Analyze sentiment of: 'This module makes Week 3 so much easier.'",
        QuickTest,
    )
    if error:
        print("Error:", error)
    else:
        print(result.model_dump())
