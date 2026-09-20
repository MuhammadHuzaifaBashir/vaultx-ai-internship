"""Tests for WhatsApp bot."""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.whatsapp_client import WhatsAppClient, APIError, MessageResponse

def test_client_init():
    """Test that the client initializes with valid credentials."""
    client = WhatsAppClient()
    assert client.phone_number_id == "1268258293044883"
    assert client.phone_number == "+923259633411"
    assert len(client.access_token) > 10
    print("✅ Client initialization test passed")

def test_verify_credentials():
    """Test credential verification."""
    client = WhatsAppClient()
    result = client.verify_credentials()
    assert result["valid"] == True, f"Credentials invalid: {result}"
    print(f"✅ Credentials verified — Profile: {result.get('name', 'N/A')}")

def test_get_profile():
    """Test getting profile."""
    client = WhatsAppClient()
    result = client.get_profile()
    assert "name" in result
    print(f"✅ Profile check passed — {result['name']}")

def test_get_phone_info():
    """Test getting phone number info."""
    client = WhatsAppClient()
    result = client.get_phone_number_info()
    assert "id" in result
    print(f"✅ Phone info: ID={result['id']}, Platform={result.get('platform_type', 'N/A')}")

def test_send_text():
    """Test sending a text message."""
    client = WhatsAppClient()
    result = client.send_text("+923259633411", "Test from VaultX Week 06 🚀")
    assert "error" not in result
    assert "messages" in result
    assert result["messages"][0]["id"].startswith("wamid.")
    print(f"✅ Send text test passed — Message ID: {result['messages'][0]['id']}")

if __name__ == "__main__":
    print("Running WhatsApp Bot tests...\n")
    test_client_init()
    test_verify_credentials()
    test_get_profile()
    test_get_phone_info()
    # test_send_text()  # Uncomment to send another test message
    print("\n✅ All tests passed!")
