# SpiceRoute Restaurant — Week 06: AI & Business Automation

## Overview
AI-powered restaurant ordering system for **SpiceRoute Restaurant**, a Pakistani restaurant in Lahore.

**Problem**: Customers call to order but have to wait on hold, menu questions go unanswered, orders get lost, no follow-up.

**Solution**: WhatsApp AI Agent — customers text their order, AI takes it, notifies kitchen, confirms order, follows up 2 days later.

## Tech Stack
- **FastAPI** — Backend server (uvicorn, port 8001)
- **Google Gemini** (`gemini-3.5-flash-lite`) — AI chat & order processing
- **Meta WhatsApp Business Cloud API** — Customer communication
- **n8n** (Podman, port 5678) — Automation workflow
- **Python-dotenv** — Environment configuration

## Project Structure
```
restaurant-bot/
├── app_api.py              # FastAPI server (9 endpoints)
├── scripts/
│   ├── rag_agent.py        # Gemini RAG menu knowledge
│   ├── whatsapp_client.py  # WhatsApp Business API client
│   └── order_manager.py    # Order lifecycle & sales tracking
├── catalog/
│   ├── products.json       # Full menu (5 categories, 17 items)
│   └── knowledge_base.txt  # AI knowledge base
├── tests/
│   ├── test_restaurant.py  # 10 unit tests
│   └── test_playwright_e2e.py  # 10 E2E tests
├── n8n/
│   ├── workflow.json       # 6-node automation
│   ├── .env
│   └── start_n8n.sh        # Podman startup script
├── data/                   # Orders database
├── logs/                   # Request logs
├── requirements.txt
├── .env
└── README.md
```

## Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/menu` | GET | Full menu |
| `/menu/{category}` | GET | Menu by category |
| `/chat` | POST | AI chat & order |
| `/order` | POST | Create order |
| `/orders` | GET | All orders |
| `/orders/pending` | GET | Pending orders |
| `/orders/{id}` | GET | Specific order |
| `/orders/{id}/status` | PUT | Update status |
| `/sales` | GET | Sales summary |
| `/webhook` | POST | WhatsApp webhook |

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Start server: `uvicorn app_api:app --reload --port 8001`
3. Start n8n: `bash n8n/start_n8n.sh`
4. Import n8n workflow: `podman exec n8n-boutique npx n8n import:workflow --input=n8n/workflow.json`
5. Run tests: `python tests/test_restaurant.py`

## Menu Categories
- Appetizers (Momos, Tikki, Spring Rolls)
- Main Course (Biryani, Karahi, Palak Paneer)
- Biryani (Veg, Chicken, Mutton)
- Desserts (Gulab Jamun, Kheer, Rabri)
- Drinks (Lassi, Nimbu Pani, Chai)

## n8n Automation
WhatsApp Webhook → AI Agent → Notify Owner + Customer Confirmed → Wait 2 Days → Follow-up

## Credentials
- Gemini API Key: in `.env`
- WhatsApp Phone ID: `1268258293044883`
- WhatsApp Token: in `.env`
- Admin Phone: `+923****4567`

## Status
- Server: Running on `:8001`
- n8n: Running on `:5678`
- Tests: 10 unit + 10 E2E = 20/20
- Model: `gemini-3.5-flash-lite`