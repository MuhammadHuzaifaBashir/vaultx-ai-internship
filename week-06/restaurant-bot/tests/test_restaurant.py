"""
Unit tests for SpiceRoute Restaurant AI Agent.
"""
import sys, os, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.rag_agent import search_menu, format_product_info, parse_order_intent, CATALOG, KNOWLEDGE_BASE
from scripts.order_manager import create_order, get_all_orders, get_pending_orders, get_sales_summary, init_data, get_order, update_order_status

def test_catalog_loaded():
    assert len(CATALOG["menu"]["appetizers"]) > 0
    assert len(CATALOG["menu"]["main_course"]) > 0
    print("✅ Catalog loaded with multiple categories")

def test_knowledge_base_loaded():
    assert len(KNOWLEDGE_BASE) > 100
    print(f"✅ Knowledge base loaded ({len(KNOWLEDGE_BASE)} chars)")

def test_menu_search():
    results = search_menu("biryani")
    assert len(results) > 0
    print(f"✅ Menu search: found {len(results)} biryani items")

def test_search_chicken():
    results = search_menu("chicken")
    assert len(results) > 0
    print(f"✅ Chicken search: found {len(results)} items")

def test_order_creation():
    init_data()
    order = create_order("Test Customer", "+923000000000", ["Biryani"], 1299, "Test Address")
    assert order["order_id"].startswith("ORD-")
    assert order["total"] == 1299
    print(f"✅ Order created: {order['order_id']}")

def test_pending_orders():
    pending = get_pending_orders()
    assert isinstance(pending, list)
    print(f"✅ Pending orders retrieved: {len(pending)}")

def test_sales_summary():
    summary = get_sales_summary()
    assert "total_revenue" in summary
    assert "total_orders" in summary
    print(f"✅ Sales summary: {summary['total_orders']} orders")

def test_order_status_update():
    orders = get_all_orders()
    if orders:
        order = update_order_status(orders[0]["order_id"], "confirmed")
        assert order["status"] == "confirmed"
        print(f"✅ Order status updated to confirmed")
    else:
        print("✅ No orders to update (test passed)")

def test_phone_validation():
    from scripts.whatsapp_client import WhatsAppClient
    wc = WhatsAppClient()
    assert wc.validate_phone("+923000000000") == True
    assert wc.validate_phone("+923123456789") == True
    print("✅ Phone validation works")

def test_whatsapp_client_init():
    from scripts.whatsapp_client import WhatsAppClient
    wc = WhatsAppClient()
    assert wc.phone_number_id == "1268258293044883"
    print("✅ WhatsApp client initialized correctly")

if __name__ == "__main__":
    test_catalog_loaded()
    test_knowledge_base_loaded()
    test_menu_search()
    test_search_chicken()
    test_order_creation()
    test_pending_orders()
    test_sales_summary()
    test_order_status_update()
    test_phone_validation()
    test_whatsapp_client_init()
    print("\n✅ All 10 unit tests passed!")