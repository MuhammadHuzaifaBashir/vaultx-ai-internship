"""
RAG Agent — Google Gemini integration for product knowledge.
Uses the boutique catalog as a retrieval-augmented knowledge base
to answer customer queries about products, stock, prices, sizes, and ordering.
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv("/home/huzaifa/dataa/huzaifabackup/vaultx-ai-internship/week-06/boutique-assistant/.env")

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
SYSTEM_PROMPT = f"""You are the AI assistant for Loom & Thread Boutique, a premium clothing boutique in Lahore, Pakistan.

Your role is to help customers with product inquiries, check stock availability, answer questions about prices, sizes, colors, materials, and help them place orders.

Always respond in a friendly, professional, and helpful tone. Use the product information below to answer accurately.

Product Catalog Information:
{KNOWLEDGE_BASE}

Rules:
- If a product is out of stock, tell the customer clearly.
- If the customer asks about a product not in the catalog, say so politely.
- When helping with an order, collect: full name, phone number, product ID/size/color, delivery address.
- Always confirm the total price before finalizing an order.
- If you cannot find the product they're looking for, suggest similar alternatives from the catalog.
- Respond in Urdu/English mix if the customer uses Urdu, otherwise respond in English.
- Keep responses concise but warm. Maximum 3-4 sentences per message unless the customer asks for details.
"""


def search_products(query: str) -> list:
    """Search the catalog for matching products based on keywords."""
    query_lower = query.lower()
    results = []

    for product in CATALOG["products"]:
        score = 0
        # Check name match
        if query_lower in product["name"].lower():
            score += 10
        # Check category match
        if query_lower in CATALOG["categories"][next((i for i, c in enumerate(CATALOG["categories"]) if c["id"] == product["category"]), 0)]["name"].lower():
            score += 5
        # Check description
        if query_lower in product["description"].lower():
            score += 3
        # Check features
        for feat in product["features"]:
            if query_lower in feat.lower():
                score += 2
        # Check color
        if any(query_lower in c.lower() for c in product["colors"]):
            score += 4
        # Check size
        if query_lower in " ".join(product["sizes"]).lower():
            score += 3

        if score > 0:
            results.append((product, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return [r[0] for r in results]


def format_product_info(product: dict) -> str:
    """Format a product's information into a readable string."""
    sizes = ", ".join(product["sizes"])
    colors = ", ".join(product["colors"])
    stock_status = f"{product['stock']} in stock" if product['stock'] > 0 else "OUT OF STOCK"
    return (
        f"*{product['name']}* (ID: {product['id']})\n"
        f"💰 PKR {product['price']:,}\n"
        f"📏 Sizes: {sizes}\n"
        f"🎨 Colors: {colors}\n"
        f"📦 Stock: {stock_status}\n"
        f"📝 {product['description']}"
    )


async def get_ai_response(message: str, context: dict = None) -> dict:
    """Get AI response using Gemini (lazy initialization)."""
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
    model = "gemini-3.5-flash-lite"
    system_prompt = SYSTEM_PROMPT

    kb_content = KNOWLEDGE_BASE
    if context and context.get("cart"):
        cart_info = "\n".join([
            f"  - {item['product']['name']} x{item['quantity']} ({item['size']}, {item['color']}) = PKR {item['product']['price'] * item['quantity']}"
            for item in context["cart"]
        ])
        kb_content += f"\n\nCurrent Cart:\n{cart_info}"

    user_message = f"Customer asked: {message}"

    try:
        response = client.models.generate_content(
            model=model,
            contents=[
                types.Part.from_text(text=system_prompt),
                types.Part.from_text(text=user_message),
            ],
        )
        response_text = response.text.strip()
        return {"response": response_text, "raw": response_text}
    except Exception as e:
        return {"response": "Sorry, I'm having trouble. Please message the owner at +923001234567.", "error": str(e)}


def parse_order_intent(message: str) -> dict:
    """
    Parse a customer message to detect order intent.
    Returns order info if detected, None otherwise.
    """
    order_keywords = ["order", "buy", "purchase", "want", "need", "book", "reserve", "i'd like", "i want"]
    has_order = any(kw in message.lower() for kw in order_keywords)

    if not has_order:
        return {"is_order": False}

    # Find product reference
    product = None
    for p in CATALOG["products"]:
        if p["id"] in message or p["name"].lower() in message.lower():
            product = p
            break

    # Find size
    size = None
    size_pattern = re.search(r'\b(S|M|L|XL|28|30|32|34|36)\b', message)
    if size_pattern:
        size = size_pattern.group(1)

    # Find color
    color = None
    for c in ["white", "blue", "pink", "green", "red", "maroon", "gold", "navy",
              "black", "brown", "cream", "peach", "mint", "lavender", "olive"]:
        if c.lower() in message.lower():
            color = c.title()
            break

    # Find customer info
    name = None
    phone = None
    address = None
    name_match = re.search(r'(?:my name is|I am|i am|i\'m)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', message)
    if name_match:
        name = name_match.group(1)
    phone_match = re.search(r'(?:phone|number|call)\s*[=:]*\s*(\+92\d{10})', message)
    if not phone_match:
        phone_match = re.search(r'(\+92\d{10})', message)
    if phone_match:
        phone = phone_match.group(1)

    return {
        "is_order": True,
        "product": product,
        "size": size,
        "color": color,
        "name": name,
        "phone": phone,
        "address": address,
        "raw_message": message
    }
