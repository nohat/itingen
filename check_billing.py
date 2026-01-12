#!/usr/bin/env python3
"""Simple test to check if billing is enabled by trying a paid model."""

import os
from itingen.integrations.ai.gemini import GeminiClient

def test_billing_status():
    """Test if billing is enabled by trying models that require it."""
    try:
        client = GeminiClient()
        print(f"🔑 API Key loaded: {client.api_key[:10]}...{client.client.api_key}")
        
        # Test with a model that typically requires billing
        print("\n🧪 Testing billing status with gemini-1.5-pro...")
        try:
            response = client.generate_text("Test", model="gemini-1.5-pro")
            print("✅ Paid model accessible - billing is enabled")
            return True
        except Exception as e:
            error_msg = str(e)
            if "RESOURCE_EXHAUSTED" in error_msg and "free_tier" in error_msg:
                print("❌ Still hitting free tier limits - billing may not be enabled")
            elif "RESOURCE_EXHAUSTED" in error_msg:
                print("✅ Billing enabled but quota exhausted")
                return True
            else:
                print(f"❌ Other error: {error_msg}")
            return False
            
    except Exception as e:
        print(f"❌ API initialization failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking Google Cloud billing status...")
    billing_enabled = test_billing_status()
    
    if not billing_enabled:
        print("\n📋 To enable billing:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Select the project for your API key")
        print("3. Go to 'Billing' and enable billing")
        print("4. Go to 'APIs & Services' → 'Library'")
        print("5. Enable 'Generative AI API'")
        print("6. Try again in a few minutes")
