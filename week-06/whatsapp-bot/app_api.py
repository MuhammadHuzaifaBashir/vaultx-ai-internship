"""
VaultX AI Internship — Week 06: WhatsApp AI Agent
Loom & Thread Boutique — Product Chat & Order Assistant.

FastAPI service that integrates:
- Google Gemini AI (RAG-powered product knowledge)
- Meta WhatsApp Business Cloud API
- Order management system

Customers chat via WhatsApp → AI answers product queries
→ captures orders → notifies owner → n8n follow-up automation.

Run with:
    uvicorn app_api:app --reload --port 8001 --host 0.0.0.0
"""

import os
import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

app = FastAPI(title="Loom & Thread Boutique — WhatsApp AI Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client (exact pattern from week-05)
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.5-flash-lite"

# WhatsApp client
from scripts.whatsapp_client import WhatsAppClient
whatsapp = WhatsAppClient()

# Order manager
from scripts.order_manager import create_order, get_all_orders, get_pending_orders, get_sales_summary

# Logging (exact pattern from week-05: logs/requests.jsonl)
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "requests.jsonl"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "boutique.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def log_request(msg_type: str, phone: str, content: str, result: dict):
    """Log each request to logs/requests.jsonl (pattern from week-05)."""
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


# Retry with exponential backoff (exact pattern from week-05)
def retry_with_backoff(fn, max_attempts=3, base_delay=1):
    """Retry a function with exponential backoff."""
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as e:
            last_error = e
            if attempt < max_attempts:
                wait = base_delay * (2 ** (attempt - 1))
                time.sleep(wait)
    raise RuntimeError(f"Failed after {max_attempts} attempts: {last_error}")


@app.on_event("startup")
async def startup():
    """Verify credentials on startup."""
    status = whatsapp.verify_credentials()
    logger.info(f"WhatsApp credentials: {status}")
    logger.info("Loom & Thread Boutique AI Agent is running!")


@app.get("/health")
async def health():
    """Health check with credential verification."""
    try:
        wa_status = whatsapp.verify_credentials()
    except Exception as e:
        wa_status = {"valid": False, "error": str(e)}
    return {
        "status": "ok",
        "boutique": "Loom & Thread Boutique",
        "whatsapp": wa_status,
        "ai_engine": "Gemini-3.5-flash-lite",
    }


@app.get("/profile")
async def profile():
    """Get WhatsApp Business profile."""
    try:
        return whatsapp.get_profile()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/products")
async def list_products(category: str = None):
    """List all products or filter by category."""
    catalog_path = Path(__file__).parent / "catalog" / "products.json"
    with open(catalog_path) as f:
        catalog = json.load(f)
    all_products = catalog["products"]
    if category:
        all_products = [p for p in all_products if p["category"] == category]
    return {"products": all_products, "total": len(all_products)}


@app.get("/products/{product_id}")
async def get_product(product_id: str):
    """Get a specific product by ID."""
    catalog_path = Path(__file__).parent / "catalog" / "products.json"
    with open(catalog_path) as f:
        catalog = json.load(f)
    for product in catalog["products"]:
        if product["id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")


@app.post("/chat")
async def chat(phone: str, message: str):
    """
    AI-powered product chat.
    Uses Gemini RAG to answer product queries and capture orders.
    """
    try:
        # Load catalog
        catalog_path = Path(__file__).parent / "catalog" / "products.json"
        kb_path = Path(__file__).parent / "catalog" / "knowledge_base.txt"
        with open(catalog_path) as f:
            catalog = json.load(f)
        with open(kb_path) as f:
            knowledge = f.read()

        system_prompt = (
            f"You are the AI assistant for Loom & Thread Boutique, a premium clothing "
            f"boutique in Lahore, Pakistan. Answer customer questions about products, "
            f"prices, sizes, colors, and help them place orders.\n\n"
            f"Product Catalog:\n{knowledge}\n\n"
            f"Rules:\n"
            f"- If a product is out of stock, say so clearly.\n"
            f"- When helping with an order, collect: name, phone, product, size, color, address.\n"
            f"- Confirm the total price before finalizing.\n"
            f"- Keep responses concise and warm. Maximum 3-4 sentences unless details requested."
        )

        # Build the message for Gemini
        user_message = f"Customer asked: {message}"

        # Call Gemini with retry
        def call_gemini():
            response = client.models.generate_content(
                model=MODEL,
                contents=[
                    types.Part.from_text(text=system_prompt),
                    types.Part.from_text(text=user_message),
                ],
            )
            return response.text.strip()

        ai_response = retry_with_backoff(call_gemini)

        # Log the request
        log_request("chat", phone, message, {"response": ai_response, "success": True})

        return {"response": ai_response, "type": "ai_response"}

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/order")
async def place_order(product_id: str, size: str, color: str, name: str, phone: str, address: str):
    """Place an order directly."""
    try:
        catalog_path = Path(__file__).parent / "catalog" / "products.json"
        with open(catalog_path) as f:
            catalog = json.load(f)
        for product in catalog["products"]:
            if product["id"] == product_id:
                if product["stock"] <= 0:
                    raise HTTPException(status_code=400, detail="Product out of stock")
                customer = {"name": name, "phone": phone, "address": address}
                order = create_order(product, size, color, customer)
                try:
                    whatsapp.send_order_notification(order)
                except Exception as e:
                    logger.error(f"Notification failed: {e}")
                return {"order_id": order["order_id"], "total": order["total"], "status": "pending"}
        raise HTTPException(status_code=404, detail="Product not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders")
async def list_orders():
    """Get all orders."""
    return {"orders": get_all_orders(), "total": len(get_all_orders())}


@app.get("/orders/pending")
async def pending():
    """Get pending orders."""
    p = get_pending_orders()
    return {"pending": p, "count": len(p)}


@app.get("/sales")
async def sales():
    """Get sales summary."""
    return get_sales_summary()


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(entry: dict):
    """Incoming WhatsApp webhook handler."""
    try:
        messages = entry.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [])
        if not messages:
            return {"status": "ok", "handled": False}
        msg = messages[0]
        sender = msg.get("from", "")
        if msg.get("type") == "text":
            text = msg["text"]["body"]
            # Process through chat
            result = await chat(phone=sender, message=text)
            ai_response = result.dict()["response"]
            whatsapp.send_text(sender, ai_response)
            return {"status": "ok", "sent": True}
        return {"status": "ok", "handled": False}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
