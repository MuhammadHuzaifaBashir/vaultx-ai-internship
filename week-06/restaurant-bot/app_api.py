"""
SpiceRoute Restaurant — WhatsApp AI Agent
Lahore, Pakistan — AI-powered restaurant ordering via WhatsApp.

FastAPI service that integrates:
- Google Gemini AI (RAG-powered menu knowledge)
- Meta WhatsApp Business Cloud API
- Order management system
- n8n automation for follow-ups

Customers chat via WhatsApp → AI answers menu queries → takes orders →
notifies owner → n8n follow-up automation.

Run with:
    uvicorn app_api:app --reload --port 8001 --host 0.0.0.0
"""

import os
import json
import time
import logging
import requests
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

app = FastAPI(title="SpiceRoute Restaurant — WhatsApp AI Agent", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.5-flash-lite"

# Order manager
from scripts.order_manager import create_order, get_all_orders, get_pending_orders, get_sales_summary, init_data, get_order, update_order_status

# RAG agent
from scripts.rag_agent import search_menu, format_product_info, parse_order_intent, get_menu_summary, SYSTEM_PROMPT, CATALOG, KNOWLEDGE_BASE, format_order_confirmation, ID_TO_ITEM, NAME_TO_ITEM

# Logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "requests.jsonl"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "restaurant.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def log_request(msg_type: str, phone: str, content: str, result: dict):
    """Log each request to logs/requests.jsonl."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": msg_type,
        "phone": phone,
        "content": content,
        "result": result,
        "success": "error" not in result,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


# Lazy-load WhatsApp client
_whatsapp_instance = None

def get_whatsapp():
    """Lazy-load WhatsApp client to avoid import-time failures."""
    global _whatsapp_instance
    if _whatsapp_instance is None:
        from scripts.whatsapp_client import WhatsAppClient
        _whatsapp_instance = WhatsAppClient()
    return _whatsapp_instance


# ==================== Pydantic Models ====================

class OrderCreate(BaseModel):
    customer_name: str
    phone: str
    items: list
    address: str = ""

class ChatRequest(BaseModel):
    phone: str = ""
    message: str = ""
    name: str = ""

class WebhookRequest(BaseModel):
    phone: str = ""
    message: str = ""
    name: str = ""

class OrderStatusRequest(BaseModel):
    order_id: str
    status: str


# ==================== Helper Functions ====================

def _get_items_from_intent(intent: dict) -> list:
    """Convert intent items to full item data with prices."""
    items_found = []
    for item_data in intent["items"]:
        item_id = item_data["id"]
        item = ID_TO_ITEM.get(item_id)
        if item:
            item_copy = item.copy()
            item_copy["quantity"] = item_data["quantity"]
            items_found.append(item_copy)
    return items_found


def _calculate_total(items: list) -> float:
    """Calculate total from list of items."""
    return sum(item["price"] * item.get("quantity", 1) for item in items)


def _handle_order(intent: dict, phone: str, name: str = "") -> dict:
    """Handle order action."""
    items = _get_items_from_intent(intent)
    if not items:
        return {"action": "order", "error": "No items found. Please specify items from the menu."}

    total = _calculate_total(items)
    customer_name = name if name else (intent.get("customer", {}).get("name", "Customer"))
    address = intent.get("address", "")

    # Create order
    order_items = [item["name"] for item in items]
    order = create_order(
        customer_name=customer_name,
        phone=phone,
        items=order_items,
        total=total,
        address=address,
    )

    # Send confirmation via WhatsApp
    whatsapp = get_whatsapp()
    try:
        # Format order items for WhatsApp
        order_details = format_order_confirmation(items)
        whatsapp.send_order_confirmation(
            customer_name=customer_name,
            items=order_items,
            total=total,
            phone=phone,
        )
        # Notify owner
        whatsapp.send_to_owner(
            f"🔔 NEW ORDER #{order['order_id']}\n"
            f"Customer: {customer_name}\n"
            f"Phone: {phone}\n"
            f"Items: {', '.join(order_items)}\n"
            f"Total: PKR {total}\n"
            f"Address: {address or 'N/A'}\n"
            f"Status: {order['status']}"
        )
        # Trigger n8n follow-up automation
        _trigger_n8n(order, customer_name, phone, items, total, address)
    except Exception as e:
        logger.warning(f"WhatsApp send failed (will retry): {e}")
        # Still return order success even if WhatsApp fails

    return {
        "action": "order",
        "order_id": order["order_id"],
        "total": total,
        "status": order["status"],
        "items": items,
        "customer_name": customer_name,
    }


def _handle_chat(message: str, phone: str) -> dict:
    """Handle general chat queries using Gemini AI."""
    try:
        prompt = f"{SYSTEM_PROMPT}\n\nCustomer message: {message}"
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        return {"action": "chat", "response": response.text}
    except Exception as e:
        logger.error(f"Gemini chat error: {e}")
        return {"action": "chat", "error": "Sorry, I'm having trouble processing that. Please try again."}


def _handle_status(intent: dict, phone: str) -> dict:
    """Handle order status tracking."""
    order_id = intent.get("status_action")
    if not order_id:
        return {"action": "status", "error": "Please provide an order ID. Example: 'status ORD-12345678901234'"}

    order = get_order(order_id)
    if order:
        return {
            "action": "status",
            "order_id": order["order_id"],
            "status": order["status"],
            "customer_name": order["customer_name"],
            "items": order["items"],
            "total": order["total"],
            "created_at": order["created_at"],
        }
    return {"action": "status", "error": f"Order {order_id} not found."}


def _handle_cancel(intent: dict, phone: str) -> dict:
    """Handle order cancellation."""
    order_id = intent.get("status_action")
    if not order_id:
        return {"action": "cancel", "error": "Please provide an order ID to cancel."}

    order = get_order(order_id)
    if order:
        if order["status"] in ["pending", "confirmed"]:
            updated = update_order_status(order_id, "cancelled")
            return {"action": "cancel", "order_id": order_id, "status": "cancelled", "message": "Order cancelled successfully."}
        return {"action": "cancel", "order_id": order_id, "status": order["status"], "error": "Only pending or confirmed orders can be cancelled."}
    return {"action": "cancel", "error": f"Order {order_id} not found."}


def _handle_menu() -> dict:
    """Handle menu browse."""
    return {"action": "menu", "menu": CATALOG["menu"], "summary": get_menu_summary()}


def _trigger_n8n(order: dict, customer_name: str, phone: str, items: list, total: float, address: str):
    """Trigger n8n automation via webhook."""
    try:
        n8n_url = os.environ.get("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/restaurant-webhook")
        payload = {
            "phone": phone,
            "name": customer_name or "Customer",
            "items": [i["name"] for i in items],
            "total": total,
            "address": address,
            "order_id": order["order_id"],
            "status": order["status"],
        }
        # Fire-and-forget — don't block the response
        import threading
        def send_n8n():
            try:
                requests.post(n8n_url, json=payload, timeout=5)
            except Exception as e:
                logger.warning(f"n8n trigger failed: {e}")
        thread = threading.Thread(target=send_n8n, daemon=True)
        thread.start()
    except Exception as e:
        logger.warning(f"n8n trigger error: {e}")


# ==================== API Endpoints ====================

@app.get("/health")
def health():
    return {"status": "ok", "restaurant": "SpiceRoute", "ai_engine": MODEL}


@app.get("/menu")
def get_menu():
    """Return the full menu."""
    summary = get_menu_summary()
    return {"menu": CATALOG["menu"], "summary": summary}


@app.get("/menu/{category}")
def get_category(category: str):
    """Get menu items by category."""
    if category in CATALOG["menu"]:
        return {"category": category, "items": CATALOG["menu"][category]}
    return JSONResponse(status_code=404, content={"error": f"Category '{category}' not found"})


@app.post("/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint — handles all WhatsApp messages."""
    try:
        phone = request.phone or "+923****0000"
        message = request.message
        name = request.name

        if not message:
            return {"action": "error", "error": "Empty message"}

        # Parse intent
        intent = parse_order_intent(message)
        action = intent["action"]

        if action == "order":
            return _handle_order(intent, phone, name)
        elif action == "status":
            return _handle_status(intent, phone)
        elif action == "cancel":
            return _handle_cancel(intent, phone)
        elif action == "menu":
            return _handle_menu()
        else:
            # Default: chat with Gemini AI
            return _handle_chat(message, phone)

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"action": "error", "error": str(e)}


@app.post("/order")
async def create_order_endpoint(order: OrderCreate):
    """Create an order directly via API."""
    try:
        items = []
        total = 0
        for item_id in order.items:
            item = ID_TO_ITEM.get(item_id)
            if item:
                qty = 1
                # Check if item is a dict with quantity
                if isinstance(item_id, dict):
                    item = item_id
                    qty = item.get("quantity", 1)
                items.append({**item, "quantity": qty})
                total += item["price"] * qty
            else:
                # Try string match
                item_name = item_id if isinstance(item_id, str) else str(item_id)
                matched = NAME_TO_ITEM.get(item_name.lower())
                if matched:
                    qty = 1
                    items.append({**matched, "quantity": qty})
                    total += matched["price"] * qty

        if not items:
            raise HTTPException(status_code=400, detail="No valid items found")

        order_obj = create_order(
            customer_name=order.customer_name,
            phone=order.phone,
            items=[i["name"] for i in items],
            total=total,
            address=order.address,
        )
        return {"order_id": order_obj["order_id"], "total": total, "status": order_obj["status"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders")
def get_orders():
    """Get all orders."""
    return {"orders": get_all_orders()}


@app.get("/orders/pending")
def pending_orders():
    """Get pending orders."""
    return {"pending": get_pending_orders()}


@app.get("/orders/{order_id}")
def get_single_order(order_id: str):
    """Get a specific order."""
    order = get_order(order_id)
    if order:
        return order
    return JSONResponse(status_code=404, content={"error": "Order not found"})


@app.put("/orders/{order_id}/status")
def update_order_status_endpoint(order_id: str, status: str):
    """Update order status."""
    order = update_order_status(order_id, status)
    if order:
        return order
    return JSONResponse(status_code=404, content={"error": "Order not found"}), 404


@app.get("/sales")
def sales_summary():
    """Get sales summary."""
    return get_sales_summary()


@app.post("/webhook")
async def webhook(request: WebhookRequest):
    """WhatsApp webhook endpoint — responds immediately, triggers async processing."""
    try:
        phone = request.phone or "+923****0000"
        message = request.message
        name = request.name or ""
        if not message:
            return JSONResponse(status_code=400, content={"error": "Empty message"})

        # Parse intent first for immediate response type
        intent = parse_order_intent(message)
        action = intent["action"]

        # Respond immediately based on action type
        if action == "order":
            # Process order in background, return immediate acknowledgment
            import threading
            def process_order():
                try:
                    _handle_order(intent, phone, request.name)
                except Exception as e:
                    logger.error(f"Background order error: {e}")
            thread = threading.Thread(target=process_order, daemon=True)
            thread.start()
            return {"action": "order_received", "status": "processing", "message": "Your order is being processed!"}

        elif action == "status":
            result = _handle_status(intent, phone)
            return result

        elif action == "cancel":
            result = _handle_cancel(intent, phone)
            return result

        elif action == "menu":
            result = _handle_menu()
            return result

        else:
            # Chat query — respond immediately from Gemini
            result = _handle_chat(message, phone)
            return result

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"action": "error", "error": str(e)}


@app.post("/n8n/trigger")
async def n8n_trigger(request: dict):
    """Endpoint for n8n to trigger follow-up automation."""
    try:
        order_id = request.get("order_id")
        customer_name = request.get("name")
        phone = request.get("phone")
        items = request.get("items", [])
        total = request.get("total", 0)

        # Trigger n8n follow-up workflow
        _trigger_n8n(
            {"order_id": order_id},
            customer_name, phone, items, total, ""
        )
        return {"status": "triggered", "order_id": order_id}
    except Exception as e:
        logger.error(f"n8n trigger error: {e}")
        return {"status": "error", "error": str(e)}


@app.get("/welcome/{phone}")
def welcome(phone: str):
    """Send welcome message to new customer."""
    try:
        name = "Customer"
        whatsapp = get_whatsapp()
        whatsapp.send_welcome_message(name, phone)
        return {"status": "welcome sent"}
    except Exception as e:
        logger.error(f"Welcome error: {e}")
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)