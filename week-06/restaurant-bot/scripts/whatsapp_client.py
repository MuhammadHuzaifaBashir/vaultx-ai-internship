"""
WhatsApp Business Cloud API client for SpiceRoute Restaurant.
Handles sending and receiving messages via Meta's WhatsApp Business API.
With graceful token handling and retry on failures.
"""

import os
import json
import time
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

BASE_URL = "https://graph.facebook.com/v18.0"
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
BUSINESS_PHONE = os.environ.get("WHATSAPP_PHONE_NUMBER", "")
ADMIN_PHONE = os.environ.get("ADMIN_PHONE", "")

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
}


class WhatsAppAPIError(Exception):
    """Custom exception for WhatsApp API errors."""
    def __init__(self, message, code=None, error_type=None):
        self.message = message
        self.code = code
        self.error_type = error_type
        super().__init__(self.message)


class WhatsAppClient:
    """Client for Meta WhatsApp Business Cloud API."""

    def __init__(self):
        self.phone_number_id = PHONE_NUMBER_ID
        self.access_token = ACCESS_TOKEN
        self.phone_number = BUSINESS_PHONE
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        })
        self._token_valid = None

    def _check_token(self) -> bool:
        """Check if the access token is still valid."""
        try:
            url = f"{BASE_URL}/{self.phone_number_id}"
            resp = self.session.get(url)
            if resp.status_code == 200:
                self._token_valid = True
                return True
            elif resp.status_code == 401:
                self._token_valid = False
                return False
            else:
                return False
        except Exception:
            self._token_valid = False
            return False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make an API request with retry on transient failures."""
        url = f"{BASE_URL}/{endpoint}"
        response = self.session.request(method, url, **kwargs)
        result = response.json()
        if response.status_code != 200 and "error" in result:
            error = result["error"]
            raise WhatsAppAPIError(
                message=error.get("message", str(error)),
                code=error.get("code"),
                error_type=error.get("type"),
            )
        return result

    def send_message(self, to: str, text: str, messaging_product: str = "whatsapp") -> dict:
        """Send a WhatsApp message to a recipient."""
        if not self._check_token():
            raise WhatsAppAPIError(
                "WhatsApp token expired. Please regenerate at Meta Developer Dashboard.",
                code=401,
                error_type="OAuthException"
            )
        payload = {
            "messaging_product": messaging_product,
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        return self._request("POST", f"{self.phone_number_id}/messages", json=payload)

    def send_order_confirmation(self, customer_name: str, items: list, total: float, phone: str) -> dict:
        """Send a formatted order confirmation."""
        items_text = "\n".join([f"  - {item}" for item in items])
        message = (
            f"🌟 *Order Confirmed!*\n\n"
            f"Customer: {customer_name}\n"
            f"*Items:*\n{items_text}\n"
            f"*Total: PKR {total:.0f}*\n\n"
            f"Thank you for ordering at SpiceRoute Restaurant! 🍽️\n"
            f"Estimated delivery: 30-45 minutes.\n"
            f"Track your order: text 'status ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}'"
        )
        return self.send_message(phone, message)

    def send_to_owner(self, message: str) -> dict:
        """Send a notification to the restaurant owner."""
        return self.send_message(ADMIN_PHONE, message)

    def send_order_status(self, customer_name: str, order_id: str, status: str, phone: str) -> dict:
        """Send order status update to customer."""
        status_emoji = {"pending": "⏳", "confirmed": "✅", "preparing": "👨‍🍳", 
                        "ready": "🎉", "on_the_way": "🚗", "delivered": "📦",
                        "cancelled": "❌"}
        emoji = status_emoji.get(status, "📋")
        message = (
            f"{emoji} *Order Status Update*\n\n"
            f"Order ID: {order_id}\n"
            f"Status: {status.upper()}\n"
            f"Customer: {customer_name}\n\n"
            f"Thank you for choosing SpiceRoute! 🍽️"
        )
        return self.send_message(phone, message)

    def send_welcome_message(self, name: str, phone: str) -> dict:
        """Send welcome message when customer first chats."""
        message = (
            f"🍽️ *Welcome to SpiceRoute Restaurant!*\n\n"
            f"Hi {name}! 👋\n\n"
            f"I'm your AI assistant. How can I help you?\n\n"
            f"*Menu:* text 'menu'\n"
            f"*Order:* text 'I want to order Biryani'\n"
            f"*Track order:* text 'status ORD-XXXXXXXX'\n"
            f"*Hours:* 11:00 AM - 11:00 PM\n"
            f"*Delivery:* 5 km range\n\n"
            f"Let's get started! 🔥"
        )
        return self.send_message(phone, message)

    def send_followup_reminder(self, name: str, phone: str, order_id: str) -> dict:
        """Send follow-up reminder 2 days after order."""
        message = (
            f"Hi {name}! 😊\n\n"
            f"Hope you enjoyed your meal from SpiceRoute! 🍽️\n"
            f"Your order {order_id} is all taken care of.\n\n"
            f"Want to order again? Just text us your order! 🔥\n\n"
            f"Special today: Try our new Mutton Biryani! 🌶️"
        )
        return self.send_message(phone, message)

    def validate_phone(self, phone: str) -> bool:
        """Validate if a phone number is in the allowed list."""
        return phone.startswith("+923") and len(phone) == 13