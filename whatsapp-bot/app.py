"""
VaultX AI Internship — Week 06: WhatsApp Bot

FastAPI service that integrates with Meta's WhatsApp Business API.
Provides endpoints to send text, media, and template messages
via the WhatsApp Business Cloud API.

Run:
    uvicorn app:app --reload --port 8001 --host 0.0.0.0
"""

import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load env from project root
load_dotenv("/home/huzaifa/dataa/huzaifabackup/vaultx-ai-internship/.env")

from scripts.whatsapp_client import WhatsAppClient, MessageResponse, APIError

app = FastAPI(title="VaultX WhatsApp Bot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize WhatsApp client
client = WhatsAppClient()

# Request logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "messages.jsonl"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup():
    """Verify credentials on startup."""
    status = client.verify_credentials()
    logger.info(f"WhatsApp client initialized: {status}")


@app.get("/health")
async def health():
    """Health check endpoint."""
    status = client.verify_credentials()
    return {"status": "ok", "whatsapp": status}


@app.post("/send/text")
async def send_text(phone: str, message: str):
    """Send a text message to a WhatsApp number."""
    try:
        result = client.send_text(phone, message)
        log_request("text", phone, message, result)
        return result
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send/media")
async def send_media(phone: str, media_url: str, caption: str = None):
    """Send a media message (image) via URL."""
    try:
        result = client.send_media(phone, media_url, caption)
        log_request("media", phone, caption or "", result)
        return result
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send/template")
async def send_template(phone: str, template_name: str, language: str = "en"):
    """Send a pre-approved template message."""
    try:
        result = client.send_template(phone, template_name, language)
        log_request("template", phone, template_name, result)
        return result
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/contacts/{phone}")
async def check_contact(phone: str):
    """Check if a phone number is a valid WhatsApp contact."""
    try:
        result = client.check_recipient(phone)
        return result
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/profile")
async def get_profile():
    """Get WhatsApp Business profile information."""
    try:
        result = client.get_profile()
        return result
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/phone-info")
async def get_phone_info():
    """Get information about the registered phone number."""
    try:
        result = client.get_phone_number_info()
        return result
    except APIError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def log_request(msg_type: str, phone: str, content: str, result: dict):
    """Log each request to JSONL file."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": msg_type,
        "phone": phone,
        "content": content,
        "result": result,
        "success": "error" not in result,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
