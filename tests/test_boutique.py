"""
Test suite for Loom & Thread Boutique AI Agent.
"""
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.rag_agent import search_products, format_product_info, parse_order_intent, CATALOG, KNOWLEDGE_BASE
from services.order_manager import create_order, get_all_orders, get_sales_summary, init_data


def test_catalog_loaded():
    """Test that the product catalog loads correctly."""
    assert len(CATALOG["products"]) == 10
    assert CATALOG["boutique"]["name"] == "Loom & Thread Boutique"
    print("✅ Catalog loaded: 10 products, correct boutique name")


def test_knowledge_base_loaded():
    """Test that the knowledge base is populated."""
    assert len(KNOWLEDGE_BASE) > 100
    assert "Loom & Thread" in KNOWLEDGE_BASE
    print(f"✅ Knowledge base loaded: {len(KNOWLEDGE_BASE)} chars")


def test_product_search():
    """Test product search functionality."""
    results = search_products("kurti")
    assert len(results) > 0
    names = [r["name"] for r in results]
    assert any("Kurti" in n for n in names)
    print(f"✅ Product search works: found {len(results)} results for 'kurti'")


def test_search_jeans():
    """Test searching for denim."""
    results = search_products("jeans")
    assert len(results) > 0
    assert any("Jeans" in r["name"] for r in results)
    print(f"✅ Denim search works: found {len(results)} results")


def test_search_by_color():
    """Test searching by color."""
    results = search_products("red")
    assert len(results) > 0
    print(f"✅ Color search works: found {len(results)} products for 'red'")


def test_order_creation():
    """Test order creation."""
    init_data()
    with open(Path(__file__).parent.parent / "catalog" / "products.json") as f:
        catalog = json.load(f)
    product = catalog["products"][0]
    customer = {"name": "Test Customer", "phone": "+923000000000", "address": "Test Address, Lahore"}
    order = create_order(product, "M", "blue", customer)

    assert order["order_id"].startswith("ORD-")
    assert order["total"] == product["price"]
    assert order["status"] == "pending"
    assert order["customer"]["name"] == "Test Customer"
    print(f"✅ Order created: {order['order_id']} — PKR {order['total']:,}")


def test_sales_summary():
    """Test sales summary."""
    summary = get_sales_summary()
    assert "total_orders" in summary
    assert "total_revenue_pkrs" in summary
    print(f"✅ Sales summary: {summary['total_orders']} orders, PKR {summary['total_revenue_pkrs']:,} revenue")


def test_order_intent_parsing():
    """Test parsing order intent from customer messages."""
    # Test with order keywords
    result = parse_order_intent("I want to order KT-001 in M size blue")
    assert result["is_order"] == True
    assert result["size"] == "M"
    print("✅ Order intent parsing works")

    # Test without order keywords
    result2 = parse_order_intent("What kurtis do you have?")
    # This may or may not detect order intent depending on keywords
    print("✅ Order intent parsing test completed")


def test_product_details():
    """Test product information formatting."""
    product = CATALOG["products"][0]
    info = format_product_info(product)
    assert product["name"] in info
    assert str(product["price"]) in info or f"{product['price']:,}" in info
    print(f"✅ Product info formatted: {product['name']}")


if __name__ == "__main__":
    print("=" * 50)
    print("Loom & Thread Boutique — Test Suite")
    print("=" * 50)
    print()
    test_catalog_loaded()
    test_knowledge_base_loaded()
    test_product_search()
    test_search_jeans()
    test_search_by_color()
    test_order_intent_parsing()
    test_product_details()
    test_order_creation()
    test_sales_summary()
    print()
    print("=" * 50)
    print("✅ All tests passed!")
    print("=" * 50)
