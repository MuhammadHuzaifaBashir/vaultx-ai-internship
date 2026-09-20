# VaultX AI Internship — Week 06: WhatsApp AI Agent

A practical AI-powered WhatsApp automation project for a Pakistani SME
boutique (Loom & Thread Boutique, Lahore).

## Business Problem

Small clothing boutiques in Pakistan lose sales because customers
ask about products on WhatsApp and owners reply slowly or forget
to follow up. Every slow reply = a lost sale.

## Solution

WhatsApp → AI Agent (Gemini RAG) → Product queries answered instantly
→ Orders captured → Owner notified → n8n follow-up automation

## Tech Stack

- Python 3.14
- FastAPI + uvicorn
- Google GenAI (`google-genai` SDK) — Gemini-3.5-flash-lite
- Meta WhatsApp Business Cloud API
- n8n automation (follow-up workflow)
- `python-dotenv`, `requests`, `pydantic`

## Setup

```bash
# Create virtual environment
cd week-06/whatsapp-bot
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up .env (credentials are already in .env — don't share publicly)
# Contains: GEMINI_API_KEY, WHATSAPP_PHONE_NUMBER_ID,
#           WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER
```

## Run

```bash
# Start the FastAPI server
uvicorn app_api:app --reload --port 8001 --host 0.0.0.0
```

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check + credential verification |
| GET | `/profile` | WhatsApp Business profile |
| GET | `/products` | List all products (filter by `?category=`) |
| GET | `/products/{id}` | Product details |
| POST | `/chat` | AI-powered product chat |
| POST | `/order` | Place an order |
| GET | `/orders` | All orders |
| GET | `/orders/pending` | Pending orders |
| GET | `/sales` | Sales summary |
| POST | `/webhook/whatsapp` | Incoming WhatsApp webhook |

## Project Structure

```
week-06/whatsapp-bot/
├── app_api.py                  # FastAPI server (main entry point)
├── scripts/
│   ├── rag_agent.py            # Gemini RAG product knowledge
│   ├── whatsapp_client.py      # Meta WhatsApp Business API client
│   └── order_manager.py        # Order lifecycle + sales tracking
├── catalog/
│   ├── products.json           # 10 products, 5 categories
│   └── knowledge_base.txt      # RAG knowledge base for Gemini
├── n8n/
│   └── workflow.json           # 9-node follow-up automation
├── logs/
│   └── requests.jsonl          # Request/response log
├── data/
│   └── orders.json             # Stored orders
├── tests/
│   ├── test_boutique.py        # Unit tests (9 tests)
│   └── test_playwright_e2e.py  # Playwright E2E tests (9 tests)
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## Testing

```bash
# Unit tests
python tests/test_boutique.py

# Playwright E2E tests
python tests/test_playwright_e2e.py
```

## n8n Integration

n8n runs on port 5678 (Podman container). The 9-node workflow:
1. **WhatsApp Webhook** — Receives incoming messages
2. **AI Classifier** — Classifies message type using OpenAI
3. **Order Capture** — Captures order details
4. **Notify Owner** — Sends notification to owner via WhatsApp
5. **Customer Confirmation** — Sends confirmation to customer
6. **Save to Sheet** — Stores order in Google Sheets
7. **Wait 2 Days** — Delay before follow-up
8. **Check Order** — Checks order status via Boutique API
9. **Send Follow-Up** — Sends follow-up message to customer

## Credentials (from Meta WhatsApp Business setup)

- App: **Internship** (ID: `1958847838835342`)
- Phone Number ID: `1268258293044883`
- Access Token: 60-day token from Meta embedded sign-up
- Profile: **Huzaifa Bashir**

## Secrets Policy

`.env` is git-ignored. No credentials are committed to this repository.

## Deliverables

| # | Deliverable | File |
|---|-------------|------|
| 1 | FastAPI server with AI chat | `app_api.py` |
| 2 | WhatsApp Business API client | `scripts/whatsapp_client.py` |
| 3 | RAG product knowledge | `scripts/rag_agent.py` |
| 4 | Order management system | `scripts/order_manager.py` |
| 5 | Product catalog (10 items) | `catalog/products.json` |
| 6 | n8n automation workflow | `n8n/workflow.json` |
| 7 | Unit tests (9 passing) | `tests/test_boutique.py` |
| 8 | Playwright E2E tests (9 passing) | `tests/test_playwright_e2e.py` |
| 9 | Live server running on port 8001 | `uvicorn app_api:app --port 8001` |
