"""
WhatsApp Business Cloud API client for Loom & Thread Boutique.
Handles sending and receiving messages via Meta's WhatsApp Business API.
"""

import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv("/home/huzaifa/dataa/huzaifabackup/vaultx-ai-internship/week-06/boutique-assistant/.env")

BASE_URL = "https://graph.facebook.com/v18.0"
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
BUSINESS_PHONE = os.environ.get("WHATSAPP_PHONE_NUMBER", "")
ADMIN_PHONE = os.environ.get("ADMIN_PHONE", "")


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

    def send_text(self, to: str, text: str) -> dict:
        """Send a text message."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        return self._request("POST", f"{self.phone_number_id}/messages", json=payload)

    def send_media(self, to: str, media_url: str, caption: str = None) -> dict:
        """Send a media message."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "image",
            "image": {"link": media_url},
        }
        if caption:
            payload["image"]["caption"] = caption
        return self._request("POST", f"{self.phone_number_id}/messages", json=payload)

    def send_template(self, to: str, template_name: str, language: str = "en", **kwargs) -> dict:
        """Send a template message."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {"name": template_name, "language": {"code": language}},
        }
        payload["template"].update(kwargs)
        return self._request("POST", f"{self.phone_number_id}/messages", json=payload)

    def send_order_notification(self, order_data: dict) -> dict:
        """Send an order notification to the owner."""
        product = order_data["product"]
        text = (
            f"🛒 NEW ORDER from Loom & Thread Boutique\n"
            f"{'='*40}\n"
            f"👤 Customer: {order_data.get('name', 'Unknown')}\n"
            f"📱 Phone: {order_data.get('phone', 'N/A')}\n"
            f"📦 Product: {product['name']} (ID: {product['id']})\n"
            f"🎨 Color: {order_data.get('color', 'N/A')}\n"
            f"📏 Size: {order_data.get('size', 'N/A')}\n"
            f"💰 Price: PKR {product['price']:,}\n"
            f"📍 Address: {order_data.get('address', 'Not provided')}\n"
            f"📅 Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{'='*40}\n"
            f"Reply to confirm or call {self.phone_number}"
        )
        return self.send_text(ADMIN_PHONE, text)

    def send_lead_capture(self, customer_info: dict) -> dict:
        """Notify owner of a new lead."""
        text = (
            f"📋 NEW LEAD from Loom & Thread Boutique\n"
            f"{'='*40}\n"
            f"👤 Name: {customer_info.get('name', 'Unknown')}\n"
            f"📱 Phone: {customer_info.get('phone', 'N/A')}\n"
            f"📝 Query: {customer_info.get('query', 'N/A')}\n"
            f"📅 Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{'='*40}"
        )
        return self.send_text(ADMIN_PHONE, text)

    def get_profile(self) -> dict:
        """Get WhatsApp Business profile."""
        return self._request("GET", "me", params={"fields": "name,verified"})

    def verify_credentials(self) -> dict:
        """Verify credentials are valid."""
        try:
            profile = self.get_profile()
            return {"valid": True, **profile}
        except WhatsAppAPIError as e:
            return {"valid": False, "error": str(e)}

    def process_webhook(self, payload: dict) -> dict:
        """
        Process incoming WhatsApp webhook message.
        Returns the response message text and parsed data.
        """
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"type": "status", "message": "No messages"}

        msg = messages[0]
        sender = msg.get("from", "")
        msg_type = msg.get("type", "text")
        msg_id = msg.get("id", "")

        if msg_type == "text":
            text = msg.get("text", {}).get("body", "")
            return {
                "type": "message",
                "sender": sender,
                "message": text,
                "message_id": msg_id,
                "timestamp": msg.get("timestamp", ""),
            }

        return {"type": msg_type, "sender": sender, "message_id": msg_id}


class WhatsAppAPIError(Exception):
    """Exception for WhatsApp API errors."""
    def __init__(self, error_data: dict):
        self.error = error_data
        self.code = error_data.get("code", "unknown")
        self.message = error_data.get("message", "Unknown error")
        self.fbtrace_id = error_data.get("fbtrace_id", "")
        super().__init__(self.message)

    def __str__(self):
        return f"WhatsAppAPIError [{self.code}]: {self.message}"
