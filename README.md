{
  "name": "Loom & Thread Boutique",
  "version": "1.0.0",
  "description": "WhatsApp AI Agent for Pakistani boutique — Order & Inventory Assistant",
  "author": "Muhammad Huzaifa Bashir",
  "ai_provider": "Google Gemini (Gemini-3.5-flash-lite)",
  "whatsapp_api": "Meta WhatsApp Business Cloud API",
  "automation": "n8n",
  "features": [
    "Product search via natural language",
    "Stock availability checking",
    "Order capture and management",
    "Customer lead capture",
    "Automated owner notifications",
    "n8n follow-up workflow",
    "RAG-powered product knowledge"
  ],
  "endpoints": {
    "webhook": "/webhook/whatsapp",
    "chat": "/chat",
    "products": "/products",
    "order": "/order",
    "health": "/health"
  }
}
