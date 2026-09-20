"""
Playwright E2E tests — Loom & Thread Boutique.
Tests all API endpoints through Playwright's request context.
"""
import sys
sys.path.insert(0, '/home/huzaifa/dataa/huzaifabackup/vaultx-ai-internship/week-06/whatsapp-bot')

from playwright.sync_api import sync_playwright
import json

BASE_URL = "http://localhost:8001"

def main():
    print("=" * 60)
    print("Playwright E2E Tests — Loom & Thread Boutique")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # 1. Health
            r = page.request.get(f"{BASE_URL}/health")
            assert r.status == 200
            print("✅ Health: 200 OK")

            # 2. Products
            r = page.request.get(f"{BASE_URL}/products")
            assert r.status == 200
            data = r.json()
            assert data["total"] == 10
            print(f"✅ Products: {data['total']} products")

            # 3. Category filter
            r = page.request.get(f"{BASE_URL}/products?category=kurtis")
            assert r.status == 200
            data = r.json()
            assert data["total"] == 3
            print(f"✅ Category filter: {data['total']} kurtis")

            # 4. Product detail
            r = page.request.get(f"{BASE_URL}/products/KT-001")
            assert r.status == 200
            data = r.json()
            assert data["id"] == "KT-001"
            print(f"✅ Product detail: {data['name']}")

            # 5. Sales
            r = page.request.get(f"{BASE_URL}/sales")
            assert r.status == 200
            print("✅ Sales: working")

            # 6. OpenAPI docs
            r = page.request.get(f"{BASE_URL}/docs")
            assert r.status == 200
            print("✅ OpenAPI docs: accessible")

            # 7. Orders list
            r = page.request.get(f"{BASE_URL}/orders")
            assert r.status == 200
            print("✅ Orders list: working")

            # 8. Pending orders
            r = page.request.get(f"{BASE_URL}/orders/pending")
            assert r.status == 200
            print("✅ Pending orders: working")

            # 9. WhatsApp Webhook
            r = page.request.get(f"{BASE_URL}/webhook/whatsapp")
            assert r.status == 405  # Method not allowed for GET (exists)
            print("✅ WhatsApp webhook endpoint: exists")

            # 9. Order creation (query params)
            import urllib.parse
            order_url = f"{BASE_URL}/order?" + urllib.parse.urlencode({
                "product_id": "KT-001", "size": "M", "color": "blue",
                "name": "E2E Test Customer", "phone": "+923000000001",
                "address": "Test Address, Lahore"
            })
            r = page.request.post(order_url)
            assert r.status == 200
            print("✅ Order creation: working")

            print()
            print("=" * 60)
            print("✅ All Playwright E2E tests passed!")
            print("=" * 60)
        finally:
            browser.close()

if __name__ == "__main__":
    main()
