"""
Unit tests for Loom & Thread Boutique AI Agent.
"""
import sys, os, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.rag_agent import search_products, format_product_info, parse_order_intent, CATALOG, KNOWLEDGE_BASE
from scripts.order_manager import create_order, get_all_orders, get_pending_orders, get_sales_summary, init_data

def test_catalog_loaded():
    assert len(CATALOG["products"]) == 10
    print("✅ Catalog loaded: 10 products")

def test_knowledge_base_loaded():
    assert len(KNOWLEDGE_BASE) > 100
    print(f"✅ Knowledge base loaded")

def test_product_search():
    results = search_products("kurti")
    assert len(results) > 0
    print(f"✅ Product search: found {len(results)} results")

def test_search_jeans():
    results = search_products("jeans")
    assert len(results) > 0
    print(f"✅ Denim search: found {len(results)} results")

def test_order_creation():
    init_data()
    product = CATALOG["products"][0]
    customer = {"name": "Test Customer", "phone": "+923000000000"}
    order = create_order(product, "M", "blue", customer)
    assert order["order_id"].startswith("ORD-")
    print(f"✅ Order created: {order['order_id']}")

def test_sales_summary():
    summary = get_sales_summary()
    assert "total_orders" in summary
    print(f"✅ Sales summary: {summary['total_orders']} orders")

def test_order_intent_parsing():
    result = parse_order_intent("I want to order KT-001 in M size blue")
    assert result["is_order"] == True
    print("✅ Order intent parsing works")

def test_product_info():
    product = CATALOG["products"][0]
    info = format_product_info(product)
    assert product["name"] in info
    print(f"✅ Product info: {product['name']}")

def test_get_all_orders():
    orders = get_all_orders()
    assert isinstance(orders, list)
    print(f"✅ Orders list: {len(orders)} orders")

def test_pending_orders():
    pending = get_pending_orders()
    assert isinstance(pending, list)
    print(f"✅ Pending orders: {len(pending)} pending")

if __name__ == "__main__":
    print("=" * 50)
    print("Loom & Thread Boutique — Unit Tests")
    print("=" * 50)
    test_catalog_loaded()
    test_knowledge_base_loaded()
    test_product_search()
    test_search_jeans()
    test_order_intent_parsing()
    test_product_info()
    test_order_creation()
    test_sales_summary()
    test_get_all_orders()
    test_pending_orders()
    print("=" * 50)
    print("✅ All unit tests passed!")
    print("=" * 50)
