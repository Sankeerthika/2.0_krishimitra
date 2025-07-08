#!/usr/bin/env python3
"""
WhatsApp API Troubleshooting Script
"""

import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

def test_whatsapp_api():
    """Test WhatsApp API connection and permissions"""
    
    print("🔍 WhatsApp API Troubleshooting")
    print("=" * 50)
    
    # Get environment variables
    access_token = os.getenv("ACCESS_TOKEN")
    phone_number_id = os.getenv("PHONE_NUMBER_ID")
    version = os.getenv("VERSION", "v18.0")
    
    if not access_token:
        print("❌ ACCESS_TOKEN not found in environment")
        return False
    
    if not phone_number_id:
        print("❌ PHONE_NUMBER_ID not found in environment")
        return False
    
    print(f"📱 Phone Number ID: {phone_number_id}")
    print(f"🔗 API Version: {version}")
    print(f"🔑 Access Token: {access_token[:20]}...{access_token[-10:]}")
    
    # Test 1: Check if we can access the phone number
    print("\n📋 Test 1: Phone Number Access")
    print("-" * 30)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    
    phone_url = f"https://graph.facebook.com/{version}/{phone_number_id}"
    
    try:
        response = requests.get(phone_url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Phone number accessible")
            print(f"   Display Name: {data.get('display_phone_number', 'N/A')}")
            print(f"   Verified Name: {data.get('verified_name', 'N/A')}")
        elif response.status_code == 401:
            print("❌ 401 Unauthorized - Token expired or invalid")
            print("   🔄 Need to generate a new access token")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
    
    # Test 2: Check token permissions
    print("\n🔐 Test 2: Token Permissions")
    print("-" * 30)
    
    debug_url = f"https://graph.facebook.com/{version}/debug_token"
    params = {
        "input_token": access_token,
        "access_token": access_token
    }
    
    try:
        response = requests.get(debug_url, params=params)
        if response.status_code == 200:
            data = response.json()
            token_data = data.get('data', {})
            
            print(f"✅ Token is valid: {token_data.get('is_valid', False)}")
            print(f"   App ID: {token_data.get('app_id', 'N/A')}")
            print(f"   Expires: {token_data.get('expires_at', 'Never')}")
            print(f"   Scopes: {', '.join(token_data.get('scopes', []))}")
            
            # Check for required scopes
            required_scopes = ['whatsapp_business_messaging', 'whatsapp_business_management']
            current_scopes = token_data.get('scopes', [])
            
            for scope in required_scopes:
                if scope in current_scopes:
                    print(f"   ✅ {scope}")
                else:
                    print(f"   ❌ Missing: {scope}")
                    
        else:
            print(f"❌ Cannot validate token: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Token validation error: {str(e)}")
    
    # Test 3: Try sending a test message to yourself
    print("\n📤 Test 3: Send Test Message")
    print("-" * 30)
    print("⚠️  This will attempt to send a test message")
    
    # Get recipient from environment or prompt
    recipient = os.getenv("RECIPIENT_WAID")
    if not recipient:
        print("📱 RECIPIENT_WAID not set in .env file")
        print("   You can add your WhatsApp number (with country code) to test")
        return False
    
    test_message_data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual", 
        "to": recipient,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": "🤖 Test message from your bot! If you receive this, your bot is working correctly."
        }
    }
    
    send_url = f"https://graph.facebook.com/{version}/{phone_number_id}/messages"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    
    try:
        response = requests.post(send_url, data=json.dumps(test_message_data), headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Test message sent successfully!")
            data = response.json()
            print(f"   Message ID: {data.get('messages', [{}])[0].get('id', 'N/A')}")
        else:
            print(f"❌ Failed to send message: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Send message error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🔧 TROUBLESHOOTING GUIDE:")
    print("-" * 30)
    print("If you see 401 Unauthorized errors:")
    print("1. 🔄 Generate a new access token from Meta for Developers")
    print("2. 📝 Update ACCESS_TOKEN in your .env file")
    print("3. 🔑 Ensure token has whatsapp_business_messaging scope")
    print("4. ⏰ Remember: Temporary tokens expire after 24 hours")
    print("\nFor permanent tokens:")
    print("1. 🏢 Create a System User in Meta Business Settings")
    print("2. 🎯 Assign WhatsApp permissions to the System User")
    print("3. 🔑 Generate a permanent access token")
    
    return True

if __name__ == "__main__":
    test_whatsapp_api()
