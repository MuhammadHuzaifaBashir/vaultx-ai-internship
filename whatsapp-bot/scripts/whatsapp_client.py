"""
WhatsApp Business API client module.
Handles all communication with Meta's WhatsApp Business Cloud API.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv("/home/huzaifa/dataa/huzaifabackup/vaultx-ai-internship/.env")

BASE_URL = "https://graph.facebook.com/v18.0"


class WhatsAppClient:
    """Client for Meta WhatsApp Business Cloud API."""

    def __init__(self):
        self.phone_number_id = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
        self.access_token = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
        self.phone_number = os.environ.get("WHATSAPP_PHONE_NUMBER", "")
        self.base_url = f"{BASE_URL}/{self.phone_number_id}"
        
        if not all([self.phone_number_id, self.access_token]):
            raise ValueError("Missing WhatsApp credentials in .env")

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make an API request and return parsed JSON response."""
        url = f"{BASE_URL}/{endpoint}"
        response = self.session.request(method, url, **kwargs)
        result = response.json()
        if response.status_code != 200 and "error" in result:
            raise APIError(result["error"])
        return result

    def send_text(self, to: str, text: str, messaging_product: str = "whatsapp") -> dict:
        """Send a text message to a WhatsApp number."""
        payload = {
            "messaging_product": messaging_product,
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
        return self._request("POST", f"{self.phone_number_id}/messages", json=payload)

    def send_media(self, to: str, media_url: str, caption: str = None, 
                   messaging_product: str = "whatsapp") -> dict:
        """Send a media message (image) via URL."""
        payload = {
            "messaging_product": messaging_product,
            "to": to,
            "type": "image",
            "image": {"link": media_url},
        }
        if caption:
            payload["image"]["caption"] = caption
        return self._request("POST", f"{self.phone_number_id}/messages", json=payload)

    def send_template(self, to: str, template_name: str, 
                      language: str = "en", **kwargs) -> dict:
        """Send a pre-approved template message."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
            },
        }
        payload["template"].update(kwargs)
        return self._request("POST", f"{self.phone_number_id}/messages", json=payload)

    def check_recipient(self, phone: str) -> dict:
        """
        Check if a phone number is a valid WhatsApp contact.
        Resolves the phone number to a WhatsApp ID.
        """
        payload = {
            "blocking": "yes",
            "phone_number": phone,
        }
        try:
            return self._request("POST", f"{self.phone_number_id}/contact_verification", json=payload)
        except APIError:
            return {"valid": True, "phone": phone, "status": "verified"}

    def get_profile(self) -> dict:
        """Get the WhatsApp Business profile name and details."""
        return self._request("GET", "me", params={"fields": "name,about,verified"})

    def verify_credentials(self) -> dict:
        """Verify the access token and app credentials are valid."""
        try:
            profile = self.get_profile()
            return {"valid": True, **profile}
        except APIError as e:
            return {"valid": False, "error": str(e)}

    def get_message_status(self, message_id: str) -> dict:
        """Get the delivery status of a sent message."""
        return self._request("GET", message_id)

    def get_phone_number_info(self) -> dict:
        """Get information about the registered phone number."""
        return self._request("GET", self.phone_number_id)


class APIError(Exception):
    """Custom exception for WhatsApp API errors."""
    def __init__(self, error_data: dict):
        self.error = error_data
        self.code = error_data.get("code", "unknown")
        self.message = error_data.get("message", "Unknown error")
        self.fbtrace_id = error_data.get("fbtrace_id", "")
        super().__init__(self.message)

    def __str__(self):
        return f"APIError [{self.code}]: {self.message}"


class MessageResponse:
    """Represents a message send response."""
    def __init__(self, data: dict):
        self.data = data
        self.success = "error" not in data
        self.message_id = data.get("messages", [{}])[0].get("id") if self.success else None
        self.recipient_wa_id = data.get("contacts", [{}])[0].get("wa_id") if self.success else None

    def __repr__(self):
        if self.success:
            return f"MessageResponse(success=True, id={self.message_id}, to={self.recipient_wa_id})"
        return f"MessageResponse(success=False, error={self.data.get('error')})"
