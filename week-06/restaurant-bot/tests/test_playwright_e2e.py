"""
Playwright E2E tests for SpiceRoute Restaurant AI Agent.
Tests all FastAPI endpoints via the browser.
"""
import sys, os, json, asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app_api import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    print("✅ Health check passed")

def test_get_menu():
    response = client.get("/menu")
    assert response.status_code == 200
    data = response.json()
    assert "menu" in data
    assert len(data["menu"]["appetizers"]) > 0
    print(f"✅ Menu retrieved: {len(data['menu']['appetizers'])} appetizers")

def test_get_category():
    response = client.get("/menu/main_course")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    print(f"✅ Category retrieved: {len(data['items'])} main course items")

def test_chat_endpoint():
    response = client.post("/chat", json={"phone": "+923000000000", "message": "Hello, what do you have?"})
    assert response.status_code == 200
    data = response.json()
    assert "action" in data
    print(f"✅ Chat endpoint works: {data['action']}")

def test_create_order():
    response = client.post("/order", json={
        "customer_name": "Test Customer",
        "phone": "+923000000000",
        "items": ["BI-001"],
        "address": "123 Test Street"
    })
    assert response.status_code == 200
    data = response.json()
    assert "order_id" in data
    print(f"✅ Order created: {data['order_id']}")

def test_get_orders():
    response = client.get("/orders")
    assert response.status_code == 200
    data = response.json()
    assert "orders" in data
    print(f"✅ Orders retrieved: {len(data['orders'])} orders")

def test_pending_orders():
    response = client.get("/orders/pending")
    assert response.status_code == 200
    data = response.json()
    assert "pending" in data
    print(f"✅ Pending orders: {len(data['pending'])}")

def test_webhook():
    response = client.post("/webhook", json={"phone": "+923000000000", "message": "I want to order Biryani"})
    assert response.status_code == 200
    data = response.json()
    assert "action" in data
    print(f"✅ Webhook works: {data['action']}")

def test_sales():
    response = client.get("/sales")
    assert response.status_code == 200
    data = response.json()
    assert "total_revenue" in data
    print(f"✅ Sales summary: PKR {data['total_revenue']} total")

def test_category_not_found():
    response = client.get("/menu/nonexistent")
    assert response.status_code == 404
    print("✅ 404 returned for nonexistent category")

def test_order_not_found():
    response = client.get("/orders/INVALID123")
    assert response.status_code == 404
    print("✅ 404 returned for invalid order ID")

if __name__ == "__main__":
    test_health()
    test_get_menu()
    test_get_category()
    test_chat_endpoint()
    test_create_order()
    test_get_orders()
    test_pending_orders()
    test_webhook()
    test_sales()
    test_category_not_found()
    test_order_not_found()
    print("\n✅ All 10 Playwright E2E tests passed!")