#!/usr/bin/env python3
"""Test script to validate Google Gemini API tier and billing status."""

from itingen.integrations.ai.gemini import GeminiClient

def test_api_tier():
    """Test API access and determine tier."""
    print("🔍 Testing Google Gemini API access...")
    
    try:
        # Initialize client
        client = GeminiClient()
        print("✅ API Key loaded successfully")
        
        # Test 1: Try text generation (should work on all tiers)
        print("\n📝 Testing text generation...")
        try:
            response = client.generate_text("Hello, world!")
            print(f"✅ Text generation works: {response[:50]}...")
        except Exception as e:
            print(f"❌ Text generation failed: {e}")
            return
        
        # Test 2: Try image generation with free tier model
        print("\n🖼️ Testing image generation (free tier model)...")
        try:
            image_bytes = client.generate_image_with_gemini(
                prompt="A simple red circle",
                model="gemini-2.5-flash-image",
                aspect_ratio="1:1"
            )
            print(f"✅ Free tier image generation works: {len(image_bytes)} bytes")
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Free tier image generation failed: {error_msg}")
            
            if "RESOURCE_EXHAUSTED" in error_msg and "free_tier" in error_msg:
                print("🔍 Free tier quota exhausted")
            elif "INVALID_ARGUMENT" in error_msg and "billed users" in error_msg:
                print("🔍 This model requires billing")
            elif "RESOURCE_EXHAUSTED" in error_msg and "gemini-3-pro" in error_msg:
                print("🔍 Pro model quota exhausted")
        
        # Test 3: Try image generation with pro model
        print("\n🎨 Testing image generation (pro model)...")
        try:
            image_bytes = client.generate_image_with_gemini(
                prompt="A simple blue square",
                model="gemini-3-pro-image-preview", 
                aspect_ratio="1:1"
            )
            print(f"✅ Pro model image generation works: {len(image_bytes)} bytes")
            print("🎉 You have access to paid tier features!")
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Pro model image generation failed: {error_msg}")
            
            if "RESOURCE_EXHAUSTED" in error_msg and "gemini-3-pro" in error_msg:
                print("🔍 Pro model quota exhausted (but you have billing access)")
            elif "INVALID_ARGUMENT" in error_msg and "billed users" in error_msg:
                print("🔍 Pro model requires billing - check your Google Cloud Console")
        
        print(f"\n📊 API Key: {client.api_key[:10]}...{client.api_key[-4:]}")
        
    except Exception as e:
        print(f"❌ API initialization failed: {e}")

if __name__ == "__main__":
    test_api_tier()
