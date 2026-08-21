import os
import json
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


class InvoiceData(BaseModel):
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    total_amount: Optional[float] = None
    due_date: Optional[str] = None
    line_items: Optional[list[str]] = None


EXTRACT_PROMPT = """Extract the following fields from this text if present. If a field is not mentioned, omit it or set it to null — do not guess or invent values.

Fields: vendor_name, invoice_number, total_amount, due_date, line_items (list of item descriptions)

Text:
{text}
"""


def extract_invoice(text: str, model="gemini-3.5-flash-lite"):
    prompt = EXTRACT_PROMPT.format(text=text)
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=InvoiceData,
            ),
        )
        data = json.loads(response.text)
        return InvoiceData.model_validate(data), None
    except Exception as e:
        return None, str(e)


TEST_TEXTS = [
    """
    Hey team, quick note — got the bill from Acme Supplies, invoice #INV-2291,
    total came out to $432.50. Not sure when it's due, they didn't mention a date this time.
    Items were: office chairs, desk lamps, and a whiteboard.
    """,
    """
    INVOICE
    Vendor: Bright Cleaning Co.
    Invoice #: BC-1042
    Due: 2026-09-15
    Amount Due: $150.00
    Services: Weekly office cleaning (August)
    """,
    """
    Hi, just forwarding this — no invoice number on it, but it's from GreenLeaf Catering
    for the team lunch, $89.99 total. They said pay whenever, no rush.
    """,
]


def run_batch_test():
    md_lines = ["# Task 04 — Extraction Tool Results\n", f"**Model:** gemini-3.5-flash-lite\n"]

    for i, text in enumerate(TEST_TEXTS, 1):
        result, error = extract_invoice(text)
        print(f"\n--- Sample {i} ---")
        md_lines.append(f"## Sample {i}\n")
        md_lines.append(f"**Input:**\n```\n{text.strip()}\n```\n")

        if error:
            print("Error:", error)
            md_lines.append(f"**Result:** ERROR — {error}\n")
        else:
            print(result.model_dump())
            md_lines.append(f"**Extracted:**\n```json\n{json.dumps(result.model_dump(), indent=2)}\n```\n")

    with open("extractor.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print("\nResults written to extractor.md")


if __name__ == "__main__":
    run_batch_test()