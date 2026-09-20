# VaultX AI Internship — Week 06: WhatsApp Bot

FastAPI service integrating Meta's WhatsApp Business Cloud API.

## Quick Start

### Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run
```bash
# Start the server (port 8001)
uvicorn app:app --reload --port 8001 --host 0.0.0.0
```

### Test
```bash
# Health check
curl http://localhost:8001/health

# Send a text message
curl -X POST http://localhost:8001/send/text \
  -d "phone=+923259633411&message=Hello from VaultX!"

# Send a media message
curl -X POST http://localhost:8001/send/media \
  -d "phone=+923259633411&media_url=https://example.com/image.jpg&caption=Check this out"

# Check profile
curl http://localhost:8001/profile

# Check if a number is valid
curl http://localhost:8001/contacts/+923259633411
```

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check + credential verification |
| GET | `/profile` | WhatsApp Business profile info |
| POST | `/send/text` | Send a text message |
| POST | `/send/media` | Send an image via URL |
| POST | `/send/template` | Send a pre-approved template |
| GET | `/contacts/{phone}` | Verify a phone number is valid |

## Credentials

Credentials are in `.env` (root project level) and also referenced here:
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_ACCESS_TOKEN`  
- `WHATSAPP_PHONE_NUMBER`

## Meta Setup

1. App: **Internship** (ID: `1958847838835342`)
2. Phone Number ID: `1268258293044883`
3. Access Token: 60-day token (generated via Meta embedded sign-up)
4. Recipient: `+923259633411` ✅ Verified
