import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


class SupportClassification(BaseModel):
    category: str      # e.g. "billing", "technical", "account", "general"
    priority: str       # "low", "medium", "high", "urgent"
    sentiment: str       # "positive", "neutral", "negative"
    needs_human: bool    # True if this needs a human agent, not a bot


CLASSIFY_PROMPT = """You are a support ticket triage system. Classify the following support message.

- category: one of "billing", "technical", "account", "general"
- priority: one of "low", "medium", "high", "urgent" based on how time-sensitive/severe the issue is
- sentiment: one of "positive", "neutral", "negative"
- needs_human: true if this requires a human agent (angry customer, complex issue, refund request, legal/security concern), false if a bot could plausibly resolve it

Support message: {message}
"""


def classify(message: str, model="gemini-3.5-flash-lite", max_retries=3):
    prompt = CLASSIFY_PROMPT.format(message=message)
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=SupportClassification,
                ),
            )
            data = json.loads(response.text)
            return SupportClassification.model_validate(data), None
        except Exception as e:
            if attempt == max_retries:
                return None, str(e)
    return None, "Unknown failure"


TEST_MESSAGES = [
    "I've been charged twice for my subscription this month and no one has responded to my last two emails!",
    "How do I reset my password?",
    "Your app keeps crashing every time I try to upload a file.",
    "Can you tell me what plans you offer?",
    "This is the third time I've contacted support about the same bug. I'm extremely frustrated.",
    "Just wanted to say thanks, your support team fixed my issue super fast!",
    "I need to update my billing address.",
    "The website is down for me, is there an outage?",
    "I think I was overcharged, can someone check my invoice?",
    "How do I export my data before closing my account?",
    "My account got locked after I tried logging in from a new device.",
    "I love how easy this tool is to use, just a quick question about integrations.",
    "This is unacceptable, I want a full refund immediately.",
    "Is there a mobile app available?",
    "I suspect someone accessed my account without permission.",
    "Can I change my subscription plan mid-cycle?",
    "The dashboard is loading really slowly today.",
    "I accidentally deleted an important file, can it be recovered?",
    "What are your support hours?",
    "I've emailed twice about a legal/compliance concern and gotten no response.",
]


def run_batch_test():
    results = []
    for i, msg in enumerate(TEST_MESSAGES, 1):
        result, error = classify(msg)
        if error:
            print(f"{i}. FAILED: {error}")
            results.append({"message": msg, "error": error})
        else:
            print(f"{i}. {result.category} | {result.priority} | {result.sentiment} | needs_human={result.needs_human}")
            results.append({"message": msg, **result.model_dump()})
    return results


if __name__ == "__main__":
    run_batch_test()
    test_message = "I've been charged twice for my subscription this month and no one has responded to my last two emails!"
    result, error = classify(test_message)
    if error:
        print("Error:", error)
    else:
        print(result.model_dump())