"""
Order Manager — Handles order lifecycle for Loom & Thread Boutique.
Stores orders, manages status, calculates totals, and prepares notifications.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

DATA_DIR = Path(__file__).parent.parent / "data"
ORDERS_FILE = DATA_DIR / "orders.json"


def init_data():
    """Initialize data directories and files."""
    DATA_DIR.mkdir(exist_ok=True)
    if not ORDERS_FILE.exists():
        ORDERS_FILE.write_text(json.dumps({"orders": [], "customers": []}, indent=2))


def load_orders() -> dict:
    """Load all orders from storage."""
    init_data()
    with open(ORDERS_FILE) as f:
        return json.load(f)


def save_orders(data: dict):
    """Save orders to storage."""
    DATA_DIR.mkdir(exist_ok=True)
    with open(ORDERS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def create_order(product: dict, size: str, color: str, customer: dict) -> dict:
    """Create a new order."""
    orders_data = load_orders()

    total = product["price"]
    order = {
        "order_id": f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "product": {
            "id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "material": product["material"],
        },
        "size": size,
        "color": color,
        "quantity": 1,
        "total": total,
        "customer": {
            "name": customer.get("name", ""),
            "phone": customer.get("phone", ""),
            "address": customer.get("address", ""),
        },
        "status": "pending",
        "payment_method": "cash_on_delivery",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "notes": "",
    }

    orders_data["orders"].append(order)
    save_orders(orders_data)
    return order


def get_order(order_id: str) -> Optional[dict]:
    """Get a specific order by ID."""
    orders_data = load_orders()
    for order in orders_data["orders"]:
        if order["order_id"] == order_id:
            return order
    return None


def update_order_status(order_id: str, status: str) -> dict:
    """Update order status."""
    orders_data = load_orders()
    for order in orders_data["orders"]:
        if order["order_id"] == order_id:
            order["status"] = status
            order["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_orders(orders_data)
            return order
    return None


def get_all_orders() -> list:
    """Get all orders sorted by date."""
    orders_data = load_orders()
    return sorted(orders_data["orders"], key=lambda x: x["created_at"], reverse=True)


def get_pending_orders() -> list:
    """Get all pending orders."""
    return [o for o in get_all_orders() if o["status"] == "pending"]


def calculate_total(items: list) -> float:
    """Calculate order total from items list."""
    return sum(item["product"]["price"] * item.get("quantity", 1) for item in items)


def get_sales_summary() -> dict:
    """Get sales summary statistics."""
    orders_data = load_orders()
    orders = orders_data["orders"]
    total_orders = len(orders)
    total_revenue = sum(o["total"] for o in orders if o["status"] in ["confirmed", "delivered"])
    pending = len([o for o in orders if o["status"] == "pending"])
    confirmed = len([o for o in orders if o["status"] == "confirmed"])
    delivered = len([o for o in orders if o["status"] == "delivered"])

    return {
        "total_orders": total_orders,
        "total_revenue_pkrs": total_revenue,
        "pending": pending,
        "confirmed": confirmed,
        "delivered": delivered,
        "average_order_value": round(total_revenue / max(confirmed + delivered, 1), 2),
    }
