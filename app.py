"""
Loom & Thread Boutique — WhatsApp AI Agent FastAPI Application.

Main application that integrates:
- Google Gemini AI (RAG-powered product knowledge)
- Meta WhatsApp Business Cloud API
- Order management system
- n8n automation workflows

Endpoints handle incoming WhatsApp messages, AI-powered product queries,
order capture, and automated owner notifications.

Run:
    uvicorn app:app --reload --port 8001 --host 0.0.0.0
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv("/home/huzaifa/dataa/huzaifabackup/vaultx-ai-internship/week-06/boutique-assistant/.env")

# Import services
from services.rag_agent import get_ai_response, search_products, format_product_info, parse_order_intent
from services.whatsapp_client import WhatsAppClient, WhatsAppAPIError
from services.order_manager import create_order, get_all_orders, get_pending_orders, get_sales_summary

# Load catalog for product lookups
CATALOG_PATH = Path(__file__).parent / "catalog" / "products.json"
with open(CATALOG_PATH) as _f:
    _CATALOG = json.load(_f)

app = FastAPI(title="Loom & Thread Boutique — WhatsApp AI Agent", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
whatsapp = WhatsAppClient()
ai_agent = None  # Initialized lazily

# Logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "boutique.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# Pydantic models
class ChatRequest(BaseModel):
    message: str
    sender: str
    context: dict = {}

class OrderRequest(BaseModel):
    product_id: str
    size: str
    color: str
    name: str
    phone: str
    address: str

class WebhookPayload(BaseModel):
    entry: list


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
    except Exception:
        wa_status = {"valid": False, "error": "Connection failed"}
    return {
        "status": "ok",
        "boutique": "Loom & Thread Boutique",
        "whatsapp": wa_status,
        "ai_engine": "Gemini-3.5-flash-lite",
    }


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Main chat endpoint — receives a customer message and returns an AI response.
    This is the core of the WhatsApp AI Agent.
    """
    try:
        message = request.message
        sender = request.sender

        # Check if this is an order intent
        order_data = parse_order_intent(message)

        if order_data["is_order"] and order_data["product"]:
            # Handle order
            product = order_data["product"]

            if product["stock"] <= 0:
                return ChatResponse(
                    response=f"Sorry, {product['name']} is currently out of stock. Would you like to know about similar products?",
                    type="out_of_stock",
                    product=None
                )

            # If size/color provided, create order
            if order_data["size"] and order_data["color"]:
                if order_data["size"] not in product["sizes"]:
                    return ChatResponse(
                        response=f"Sorry, {product['name']} is not available in size {order_data['size']}. Available sizes: {', '.join(product['sizes'])}.",
                        type="wrong_size",
                        product=product
                    )

                if order_data["color"] not in product["colors"]:
                    return ChatResponse(
                        response=f"Sorry, {product['name']} is not available in {order_data['color']}. Available colors: {', '.join(product['colors'])}.",
                        type="wrong_color",
                        product=product
                    )

                # Create order
                customer = {"name": order_data["name"], "phone": order_data["phone"], "address": ""}
                order = create_order(product, order_data["size"], order_data["color"], customer)

                # Notify owner
                try:
                    whatsapp.send_order_notification(order)
                except WhatsAppAPIError as e:
                    logger.error(f"Notification failed: {e}")

                return ChatResponse(
                    response=f"✅ Order placed! {product['name']} ({order_data['size']}, {order_data['color']}) — PKR {product['price']:,}. Cash on delivery. We'll confirm shortly.",
                    type="order_confirmed",
                    product=product,
                    order_id=order["order_id"],
                    total=order["total"]
                )

            # Need more info for order
            return ChatResponse(
                response=f"Great choice! {product['name']} — PKR {product['price']:,}. To complete the order, tell me your full name, phone number, size ({', '.join(product['sizes'])}), color ({', '.join(product['colors'])}), and delivery address.",
                type="order_in_progress",
                product=product
            )

        # Search products
        results = search_products(message)
        if results:
            top = results[0]
            info = format_product_info(top)
            return ChatResponse(
                response=f"Here's what I found:\n\n{info}\n\nWant to order this? Just say your name, phone, size, color, and delivery address!",
                type="product_found",
                product=top,
                results=len(results)
            )

        # Use AI for general questions
        ai_result = get_ai_response(message)
        return ChatResponse(
            response=ai_result["response"],
            type="ai_response"
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(payload: WebhookPayload):
    """
    Webhook endpoint for incoming WhatsApp messages.
    Processes the message and returns a response.
    """
    try:
        data = payload.entry[0]["changes"][0]["value"]
        messages = data.get("messages", [])

        if not messages:
            return {"status": "ok", "handled": False}

        msg = messages[0]
        sender = msg.get("from", "")

        if msg.get("type") == "text":
            text = msg["text"]["body"]
            # Process through chat endpoint
            request = ChatRequest(message=text, sender=sender)
            response = await chat(request)
            # Send response back via WhatsApp
            ai_response = response.dict()["response"]
            whatsapp.send_text(sender, ai_response)
            return {"status": "ok", "sent": True}

        return {"status": "ok", "handled": False}

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products")
async def list_products(category: str = None):
    all_products = _CATALOG["products"]
    if category:
        all_products = [p for p in all_products if p["category"] == category]
    return {"products": all_products, "total": len(all_products)}


@app.get("/products/{product_id}")
async def get_product(product_id: str):
    """Get a specific product by ID."""
    with open(Path(__file__).parent / "catalog" / "products.json") as f:
        catalog = json.load(f)
    for product in catalog["products"]:
        if product["id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")


@app.post("/order")
async def place_order(order: OrderRequest):
    """Place an order directly."""
    with open(Path(__file__).parent / "catalog" / "products.json") as f:
        catalog = json.load(f)
    for product in catalog["products"]:
        if product["id"] == order.product_id:
            if product["stock"] <= 0:
                raise HTTPException(status_code=400, detail="Product out of stock")

            customer = {"name": order.name, "phone": order.phone, "address": order.address}
            order_data = create_order(product, order.size, order.color, customer)

            try:
                whatsapp.send_order_notification(order_data)
            except WhatsAppAPIError as e:
                logger.error(f"Notification failed: {e}")

            return {"order_id": order_data["order_id"], "total": order_data["total"], "status": "pending"}

    raise HTTPException(status_code=404, detail="Product not found")


@app.get("/orders")
async def list_orders():
    """Get all orders."""
    return {"orders": get_all_orders(), "total": len(get_all_orders())}


@app.get("/orders/pending")
async def pending_orders():
    """Get pending orders."""
    return {"pending": get_pending_orders(), "count": len(get_pending_orders())}


@app.get("/sales")
async def sales_summary():
    """Get sales summary."""
    return get_sales_summary()


@app.get("/profile")
async def profile():
    """Get WhatsApp Business profile."""
    try:
        return whatsapp.get_profile()
    except WhatsAppAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Pydantic response model
from pydantic import BaseModel as _BaseModel

class ChatResponse(_BaseModel):
    response: str
    type: str
    product: dict = None
    order_id: str = None
    total: float = None
    results: int = None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
