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

# Initialize Gemini client
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

# Build reverse lookup: item name -> item dict, item id -> item dict
NAME_TO_ITEM = {}
ID_TO_ITEM = {}
for category_items in CATALOG["menu"].values():
    for item in category_items:
        NAME_TO_ITEM[item["name"].lower()] = item
        ID_TO_ITEM[item["id"]] = item
        # Also add common aliases
        aliases = {
            "biryani": ["chicken biryani", "mutton biryani", "veg biryani", "vegetable biryani"],
            "karahi": ["chicken karahi", "chicken karahi"],
            "momos": ["chicken momos"],
            "lassi": [],
            "chai": ["masala chai"],
            "gulab jamun": [],
            "kheer": [],
            "rabri": [],
        }
        base_name = item["name"].lower()
        if base_name in aliases:
            for alias in aliases[base_name]:
                NAME_TO_ITEM[alias] = item


def search_menu(query: str) -> list:
    """Search the menu for items matching the query."""
    results = []
    q = query.lower().strip()
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
    stock_status = f"Stock: {item['stock']}" if item['stock'] > 0 else "❌ OUT OF STOCK"
    return (f"**{item['name']}**{spicy}\n"
            f"Price: PKR {item['price']}\n"
            f"Description: {item['description']}\n"
            f"{stock_status}")


def parse_quantity(message: str, item_name: str) -> int:
    """Extract quantity from message for a given item. Defaults to 1."""
    # Patterns: "2 biryani", "biryani x2", "biryani 2", "2x biryani"
    patterns = [
        rf'(\d+)\s*{re.escape(item_name)}',
        rf'{re.escape(item_name)}\s*x?\s*(\d+)',
        rf'(\d+)\s*x',
    ]
    for pattern in patterns:
        match = re.search(pattern, message.lower())
        if match:
            return int(match.group(1))
    return 1


def parse_order_intent(message: str) -> dict:
    """Parse customer message to extract order intent, items, quantities, customer info.
    
    Returns:
        dict with keys: action ('order'|'chat'|'status'|'cancel'|'menu'),
                        items (list of {id, name, quantity}),
                        customer (dict), address, status_action
    """
    msg_lower = message.lower().strip()
    intent = {
        "action": "chat",
        "items": [],
        "customer": None,
        "address": "",
        "status_action": None,
    }

    # --- Check for order status commands ---
    status_patterns = [
        r'(?:check|track|status|where).*?(order|my order|ord[-]?\w+)',
        r'(?:order|ord[-]?\w+).*?(status|track|where)',
        r'status\s+(ord[-]?\w+)',
    ]
    for pattern in status_patterns:
        if re.search(pattern, msg_lower):
            intent["action"] = "status"
            order_match = re.search(r'(ord[-]\d{14})', msg_lower)
            if order_match:
                intent["status_action"] = order_match.group(1)
            break

    # --- Check for cancel commands ---
    if re.search(r'(?:cancel|remove).*?(order|my order)', msg_lower):
        intent["action"] = "cancel"
        order_match = re.search(r'(ord[-]?\d{14})', msg_lower)
        if order_match:
            intent["status_action"] = order_match.group(1)
        return intent

    # --- Check for menu browse commands ---
    if re.search(r'(?:menu|show menu|what.*?(on|available)|list|browse)', msg_lower):
        intent["action"] = "menu"
        return intent

    # --- Check for order keywords ---
    order_keywords = ["order", "book", "reserve", "deliver", "want", "need", 
                      "get", "i'd like", "i want", "can i have", "please",
                      "i'll have", "gimme", "let me have", "give me"]
    is_order = any(kw in msg_lower for kw in order_keywords)

    if is_order:
        intent["action"] = "order"

    # --- Extract customer name ---
    name_patterns = [
        (r'my name is\s+(\w+)', 1),
        (r"(?:i'm|i am)\s+(\w+)", 1),
        (r'call me\s+(\w+)', 1),
        (r'(?:my|the customer is)\s+(\w+)', 1),
    ]
    for pattern, group_idx in name_patterns:
        match = re.search(pattern, msg_lower)
        if match:
            name = match.group(group_idx).capitalize()
            intent["customer"] = {"name": name}
            break

    # --- Extract phone number ---
    phone_match = re.search(r'\+92\d{10}', msg_lower)
    if not phone_match:
        phone_match = re.search(r'03\d{9}', msg_lower)
    if phone_match:
        phone = phone_match.group()
        if not phone.startswith('+92'):
            phone = '+92' + phone[1:]
        if intent["customer"]:
            intent["customer"]["phone"] = phone
        else:
            intent["customer"] = {"phone": phone}

    # --- Extract address ---
    addr_patterns = [
        r'(?:address|deliver to|at)\s+([^.]+?)(?:\.|$)',
        r'(?:send to|ship to)\s+([^,\.]+)',
    ]
    for pattern in addr_patterns:
        match = re.search(pattern, msg_lower)
        if match:
            addr = match.group(1).strip().rstrip('.').strip()
            # Filter out common false positives
            if addr.lower() not in ['order', 'food', 'phone', 'yes', 'no']:
                intent["address"] = addr
            break

    # --- Extract items (by ID or name) with quantities ---
    # First try matching by item ID (e.g., "BI-001", "MC-002")
    id_matches = re.findall(r'\b(MC-\d{3}|BI-\d{3}|APP-\d{3}|DS-\d{3}|DR-\d{3})\b', msg_lower)
    if id_matches:
        for item_id in id_matches:
            if item_id in ID_TO_ITEM:
                qty = parse_quantity(msg_lower, ID_TO_ITEM[item_id]["name"])
                intent["items"].append({
                    "id": item_id,
                    "name": ID_TO_ITEM[item_id]["name"],
                    "quantity": qty,
                })

    # Then try matching by item name
    if not intent["items"]:
        for name_lower, item in NAME_TO_ITEM.items():
            # Match full item name
            if re.search(r'\b' + re.escape(name_lower) + r'\b', msg_lower):
                if not any(i["id"] == item["id"] for i in intent["items"]):
                    qty = parse_quantity(msg_lower, item["name"])
                    intent["items"].append({
                        "id": item["id"],
                        "name": item["name"],
                        "quantity": qty,
                    })

    # If no items found by name but the message implies ordering, try a generic search
    if not intent["items"] and is_order:
        # Try to find any item names mentioned in the message
        for name_lower, item in NAME_TO_ITEM.items():
            if name_lower[:4] in msg_lower and len(name_lower) >= 4:
                if not any(i["id"] == item["id"] for i in intent["items"]):
                    qty = parse_quantity(msg_lower, item["name"])
                    intent["items"].append({
                        "id": item["id"],
                        "name": item["name"],
                        "quantity": qty,
                    })

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


def format_order_confirmation(items: list) -> str:
    """Format order items for confirmation message."""
    lines = []
    total = 0
    for item_data in items:
        item = ID_TO_ITEM.get(item_data["id"])
        if item:
            line_total = item["price"] * item_data["quantity"]
            total += line_total
            qty_text = f" x{item_data['quantity']}" if item_data["quantity"] > 1 else ""
            lines.append(f"  {item['name']}{qty_text} — PKR {line_total}")
    lines.append(f"\n**Total: PKR {total}**")
    return "\n".join(lines)