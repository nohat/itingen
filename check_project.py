#!/usr/bin/env python3
"""Check which Google Cloud project your API key is associated with."""

from itingen.integrations.ai.gemini import GeminiClient

def check_project_info():
    """Get project information from API key."""
    try:
        client = GeminiClient()
        print(f"🔑 API Key: {client.api_key[:10]}...{client.api_key[-4:]}")
        
        # Try to get model info to see project context
        try:
            client.client.models.get_model("gemini-2.0-flash-exp")
            print("📊 Model info available - API key is working")
            print("🔍 Check your Google Cloud Console for the project linked to this API key")
        except Exception as e:
            print(f"❌ Error checking project: {e}")
            
    except Exception as e:
        print(f"❌ API key issue: {e}")

if __name__ == "__main__":
    check_project_info()
