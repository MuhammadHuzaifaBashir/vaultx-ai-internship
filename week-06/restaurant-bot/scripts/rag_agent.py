"""
RAG Agent — Google Gemini integration for SpiceRoute Restaurant.
Retrieval-augmented knowledge base for answering customer
queries about the menu, prices, availability, and taking orders.
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Initialize Gemini client (exact week-05 pattern)
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.5-flash-lite"

# Paths
BASE_DIR = Path(__file__).parent.parent
CATALOG_PATH = BASE_DIR / "catalog" / "products.json"
KB_PATH = BASE_DIR / "catalog" / "knowledge_base.txt"


def load_catalog():
    with open(CATALOG_PATH) as f:
        return json.load(f)


def load_knowledge_base():
    with open(KB_PATH) as f:
        return f.read()


CATALOG = load_catalog()
KNOWLEDGE_BASE = load_knowledge_base()

SYSTEM_PROMPT = f"""You are the AI assistant for SpiceRoute Restaurant, a Pakistani restaurant in Lahore, Pakistan.

Your role is to help customers with the menu, check prices and availability, take food orders, and answer questions about the cuisine.

Always respond in a friendly, professional, and helpful tone. Use the menu information below to answer accurately.

Menu Information:
{KNOWLEDGE_BASE}

Rules:
- If an item is out of stock, tell the customer clearly.
- If the customer asks about a dish not on the menu, suggest similar alternatives.
- When taking an order, confirm: items, quantities, customer name, phone number, and delivery address.
- Always confirm the total price before finalizing.
- Ask if they want drinks or dessert after the main course.
- If they ask about spice level, mention which dishes are spicy.
- Keep responses concise but warm. Maximum 3-4 sentences per message unless the customer asks for details.
"""


def search_menu(query: str) -> list:
    """Search the menu for items matching the query."""
    results = []
    q = query.lower()
    for category in CATALOG["menu"].values():
        for item in category:
            if (q in item["name"].lower() or 
                q in item["description"].lower() or
                q in item["category"].lower()):
                results.append(item)
    return results


def format_product_info(item: dict) -> str:
    """Format a menu item for display."""
    spicy = " 🌶️" if item.get("spicy") else ""
    return (f"**{item['name']}**{spicy}\n"
            f"Price: PKR {item['price']}\n"
            f"Description: {item['description']}\n"
            f"Stock: {item['stock']}")


def parse_order_intent(message: str) -> dict:
    """Parse customer message to extract order intent."""
    intent = {"action": "chat", "items": [], "customer": None}
    
    # Check for order keywords
    order_keywords = ["order", "book", "reserve", "deliver", "want", "need", "get"]
    if any(kw in message.lower() for kw in order_keywords):
        intent["action"] = "order"
    
    # Extract customer name
    name_patterns = ["my name is", "i'm", "i am", "call me"]
    for pattern in name_patterns:
        if pattern in message.lower():
            parts = message.lower().split(pattern)
            if len(parts) > 1:
                name = parts[1].strip().split()[0].capitalize()
                intent["customer"] = {"name": name}
    
    # Extract phone
    phone_match = re.search(r'\+92\d{10}', message)
    if not phone_match:
        phone_match = re.search(r'03\d{10}', message)
    if phone_match:
        phone = phone_match.group()
        if not phone.startswith('+92'):
            phone = '+92' + phone[1:]
        if intent["customer"]:
            intent["customer"]["phone"] = phone
        else:
            intent["customer"] = {"phone": phone}
    
    # Find menu items mentioned
    for category in CATALOG["menu"].values():
        for item in category:
            if item["name"].lower() in message.lower():
                intent["items"].append(item["id"])
    
    return intent


def get_menu_summary() -> str:
    """Return a summary of all menu items."""
    summary = []
    for category_name, items in CATALOG["menu"].items():
        summary.append(f"\n### {category_name.replace('_', ' ').title()}:")
        for item in items:
            spicy = " 🌶️" if item.get("spicy") else ""
            summary.append(f"- {item['name']}{spicy} — PKR {item['price']}")
    return "\n".join(summary)