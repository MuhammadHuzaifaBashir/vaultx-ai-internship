"""
WhatsApp Business Cloud API client for SpiceRoute Restaurant.
Handles sending and receiving messages via Meta's WhatsApp Business API.
"""

import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone

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
    pass


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

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make an API request."""
        url = f"{BASE_URL}/{endpoint}"
        response = self.session.request(method, url, **kwargs)
        result = response.json()
        if response.status_code != 200 and "error" in result:
            raise WhatsAppAPIError(result["error"])
        return result

    def send_message(self, to: str, text: str, messaging_product: str = "whatsapp") -> dict:
        """Send a WhatsApp message to a recipient."""
        payload = {
            "messaging_product": messaging_product,
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        return self._request("POST", f"{PHONE_NUMBER_ID}/messages", json=payload)

    def send_order_confirmation(self, customer_name: str, items: list, total: float, phone: str) -> dict:
        """Send a formatted order confirmation."""
        items_text = "\n".join([f"  - {item}" for item in items])
        message = (f"🌟 *Order Confirmed!*\n\n"
                   f"Customer: {customer_name}\n"
                   f"*Items:*\n{items_text}\n"
                   f"*Total: PKR {total:.0f}*\n\n"
                   f"Thank you for ordering at SpiceRoute Restaurant! 🍽️\n"
                   f"Estimated delivery: 30-45 minutes.")
        return self.send_message(phone, message)

    def send_to_owner(self, message: str) -> dict:
        """Send a notification to the restaurant owner."""
        return self.send_message(ADMIN_PHONE, message)

    def validate_phone(self, phone: str) -> bool:
        """Validate if a phone number is in the allowed list."""
        # Accept any Pakistani number starting with +923
        return phone.startswith("+923") and len(phone) == 13