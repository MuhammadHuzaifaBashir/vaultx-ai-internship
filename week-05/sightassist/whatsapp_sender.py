"""
WhatsApp Business API message sender for VaultX AI Internship.
Uses Meta's WhatsApp Business API to send messages programmatically.

Usage:
    python whatsapp_sender.py --message "Hello from VaultX"
    python whatsapp_sender.py --test        # Send a test message to self
"""

import os
import json
import sys
import argparse
import requests
from dotenv import load_dotenv

load_dotenv("/home/huzaifa/dataa/huzaifabackup/vaultx-ai-internship/.env")

# Credentials loaded from .env
PHONE_NUMBER_ID = os.environ["WHATSAPP_PHONE_NUMBER_ID"]
ACCESS_TOKEN = os.environ["WHATSAPP_ACCESS_TOKEN"]
PHONE_NUMBER = os.environ["WHATSAPP_PHONE_NUMBER"]

API_BASE = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}"

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
}


def send_message(to: str, text: str, messaging_product: str = "whatsapp") -> dict:
    """Send a WhatsApp message to a recipient."""
    payload = {
        "messaging_product": messaging_product,
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    response = requests.post(f"{API_BASE}/messages", headers=HEADERS, json=payload)
    result = response.json()
    if response.status_code != 200:
        print(f"❌ Error: {json.dumps(result, indent=2)}")
    return result


def send_media(to: str, media_url: str, caption: str = None) -> dict:
    """Send a media (image/video/document) message."""
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {"link": media_url},
    }
    if caption:
        payload["image"]["caption"] = caption
    response = requests.post(f"{API_BASE}/messages", headers=HEADERS, json=payload)
    return response.json()


def check_recipient_status(phone: str) -> dict:
    """Check if a phone number is an allowed recipient."""
    response = requests.get(
        f"{API_BASE}/test_recipients",
        headers=HEADERS,
        params={"phone_number": phone},
    )
    return response.json()


def get_profile() -> dict:
    """Get the WhatsApp Business profile info."""
    response = requests.get(
        f"https://graph.facebook.com/v18.0/me",
        headers=HEADERS,
        params={"fields": "name,profile_picture_url,verified"},
    )
    return response.json()


def main():
    parser = argparse.ArgumentParser(description="VaultX WhatsApp Message Sender")
    parser.add_argument("--message", "-m", type=str, help="Message text to send")
    parser.add_argument("--to", type=str, default=PHONE_NUMBER, help="Recipient number")
    parser.add_argument("--test", action="store_true", help="Send test message to self")
    parser.add_argument("--check", action="store_true", help="Check if your number is an allowed recipient")
    parser.add_argument("--profile", action="store_true", help="Get WhatsApp Business profile")

    args = parser.parse_args()

    if args.check:
        print(f"Checking recipient status for {PHONE_NUMBER}...")
        result = check_recipient_status(PHONE_NUMBER)
        print(json.dumps(result, indent=2))
        return

    if args.profile:
        print("Getting profile...")
        result = get_profile()
        print(json.dumps(result, indent=2))
        return

    if args.test:
        message = args.message or "✅ VaultX AI Internship — WhatsApp API working! 🚀\n\nMessage sent via Meta WhatsApp Business API."
        print(f"📤 Sending test message to {PHONE_NUMBER}...")
        result = send_message(PHONE_NUMBER, message)
        print(json.dumps(result, indent=2))
        if "error" not in result:
            print("✅ Message sent successfully!")
        return

    if args.message:
        print(f"📤 Sending message to {args.to}...")
        result = send_message(args.to, args.message)
        print(json.dumps(result, indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
