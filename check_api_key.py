#!/usr/bin/env python3
"""Check API key and provide guidance for billing setup."""

import os
from dotenv import load_dotenv

load_dotenv()

def check_api_setup():
    """Check API key and provide guidance."""
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        print("📝 Make sure your .env file contains:")
        print("   GEMINI_API_KEY=your_api_key_here")
        return
    
    print(f"🔑 API Key found: {api_key[:10]}...{api_key[-4:]}")
    print(f"🔑 Key length: {len(api_key)} characters")
    
    # API keys should be 39 characters for Gemini
    if len(api_key) != 39:
        print("⚠️  Gemini API keys are typically 39 characters long")
        print("   Your key might be from a different service")
    
    print("\n📋 To verify billing status:")
    print("1. Go to https://aistudio.google.com/app/apikey")
    print("2. Find your API key in the list")
    print("3. Check the 'Project' column")
    print("4. Go to https://console.cloud.google.com/")
    print("5. Select that project")
    print("6. Check 'Billing' - should be enabled")
    print("7. Check 'APIs & Services' - 'Generative AI API' should be enabled")
    
    print(f"\n🔗 Your API key starts with: {api_key[:10]}")
    print("   Use this to identify the correct project in Google Cloud Console")

if __name__ == "__main__":
    check_api_setup()
