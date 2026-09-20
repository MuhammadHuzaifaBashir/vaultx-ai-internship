#!/bin/bash
echo "🚀 Setting up VaultX WhatsApp Bot..."

# Create venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

echo "✅ Setup complete!"
echo "Run: uvicorn app:app --reload --port 8001 --host 0.0.0.0"
