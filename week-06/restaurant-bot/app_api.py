"""
SpiceRoute Restaurant — WhatsApp AI Agent
Lahore, Pakistan — AI-powered restaurant ordering via WhatsApp.

FastAPI service that integrates:
- Google Gemini AI (RAG-powered menu knowledge)
- Meta WhatsApp Business Cloud API
- Order management system

Customers chat via WhatsApp → AI answers menu queries → takes orders →
notifies owner → n8n follow-up automation.

Run with:
    uvicorn app_api:app --reload --port 8001 --host 0.0.0.0
"""

import os
import json
import time
import logging
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

app = FastAPI(title="SpiceRoute Restaurant — WhatsApp AI Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client (exact week-05 pattern)
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.5-flash-lite"

# WhatsApp client
from scripts.whatsapp_client import WhatsAppClient
whatsapp = WhatsAppClient()

# Order manager
from scripts.order_manager import create_order, get_all_orders, get_pending_orders, get_sales_summary, init_data, get_order, update_order_status

# RAG agent
from scripts.rag_agent import search_menu, format_product_info, parse_order_intent, get_menu_summary, SYSTEM_PROMPT, CATALOG, KNOWLEDGE_BASE

# Logging (exact pattern from week-05)
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
    """Main chat endpoint — customers send WhatsApp messages here."""
    try:
        phone = request.phone
        message = request.message
        if not message:
            return {"action": "error", "error": "Empty message"}
        # Parse order intent
        intent = parse_order_intent(message)
        if intent is None:
            return {"action": "error", "error": "Could not parse message"}
        
        if intent["action"] == "order":
            # Handle order
            items_found = []
            for item_id in intent["items"]:
                for category_items in CATALOG["menu"].values():
                    for item in category_items:
                        if item["id"] == item_id:
                            items_found.append(item)
            
            if items_found:
                total = sum(item["price"] for item in items_found)
                # Create order
                customer_name = request.name if request.name else (intent.get("customer") or {}).get("name", "Customer")
                order = create_order(
                    customer_name=customer_name,
                    phone=phone,
                    items=[item["name"] for item in items_found],
                    total=total,
                    address=""
                )
                
                # Send confirmation to customer
                whatsapp.send_order_confirmation(
                    customer_name=order["customer_name"],
                    items=order["items"],
                    total=total,
                    phone=phone
                )
                
                # Notify owner
                whatsapp.send_to_owner(f"🔔 NEW ORDER #{order['order_id']}\nCustomer: {order['customer_name']}\nPhone: {phone}\nItems: {', '.join(order['items'])}\nTotal: PKR {total}")
                
                result = {"action": "order", "order_id": order["order_id"], "total": total}
            else:
                result = {"action": "order", "error": "No items found in order"}
        else:
            # Use Gemini AI for general queries
            prompt = f"{SYSTEM_PROMPT}\n\nCustomer message: {message}"
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )
            result = {"action": "chat", "response": response.text}
        
        log_request("chat", phone, message, result)
        return result
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"action": "error", "error": str(e)}


@app.post("/order")
async def create_order_endpoint(order: OrderCreate):
    """Create an order directly via API."""
    try:
        total = 0
        order_items = []
        for item_id in order.items:
            for category_items in CATALOG["menu"].values():
                for item in category_items:
                    if item["id"] == item_id:
                        order_items.append(item)
                        total += item["price"]
        
        order = create_order(
            customer_name=order.customer_name,
            phone=order.phone,
            items=[i["name"] for i in order_items],
            total=total,
            address=order.address
        )
        return {"order_id": order["order_id"], "total": total, "status": order["status"]}
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
    return {"error": "Order not found"}, 404


@app.get("/sales")
def sales_summary():
    """Get sales summary."""
    return get_sales_summary()


@app.post("/webhook")
async def webhook(request: WebhookRequest):
    """WhatsApp webhook endpoint for incoming messages."""
    return await chat(ChatRequest(phone=request.phone, message=request.message))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)