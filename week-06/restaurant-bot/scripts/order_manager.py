"""
Order Manager — Handles order lifecycle for SpiceRoute Restaurant.
Stores orders, manages status, and prepares notifications.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone

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
        json.dump(data, f, indent=2)


def create_order(customer_name: str, phone: str, items: list, total: float, address: str = "") -> dict:
    """Create a new order."""
    init_data()
    orders_data = load_orders()
    
    order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    order = {
        "order_id": order_id,
        "customer_name": customer_name,
        "phone": phone,
        "items": items,
        "total": total,
        "address": address,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    orders_data["orders"].append(order)
    
    # Track customer
    customer_exists = any(c["phone"] == phone for c in orders_data["customers"])
    if not customer_exists:
        orders_data["customers"].append({
            "name": customer_name,
            "phone": phone,
            "first_order": order["created_at"],
            "total_orders": 1
        })
    else:
        for c in orders_data["customers"]:
            if c["phone"] == phone:
                c["total_orders"] += 1
    
    save_orders(orders_data)
    return order


def get_all_orders() -> list:
    """Get all orders."""
    return load_orders()["orders"]


def get_pending_orders() -> list:
    """Get all pending orders."""
    return [o for o in get_all_orders() if o["status"] == "pending"]


def get_order(order_id: str) -> dict:
    """Get a specific order by ID."""
    for order in get_all_orders():
        if order["order_id"] == order_id:
            return order
    return None


def update_order_status(order_id: str, status: str) -> dict:
    """Update an order's status."""
    orders_data = load_orders()
    for order in orders_data["orders"]:
        if order["order_id"] == order_id:
            order["status"] = status
            order["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_orders(orders_data)
            return order
    return None


def get_sales_summary() -> dict:
    """Get sales summary."""
    orders = load_orders()["orders"]
    total_revenue = sum(o["total"] for o in orders)
    total_orders = len(orders)
    pending = len([o for o in orders if o["status"] == "pending"])
    return {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "pending_orders": pending,
        "completed_orders": total_orders - pending
    }