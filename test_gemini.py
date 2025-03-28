import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

async def list_models():
    """List available Gemini models."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    
    if not api_key:
        print("ERROR: Gemini API key not found in environment variables")
        return
    
    print(f"Using Gemini API key: {api_key[:5]}...{api_key[-3:]}")
    
    url = "https://generativelanguage.googleapis.com/v1beta/models"
    headers = {
        "x-goog-api-key": api_key
    }
    
    try:
        async with httpx.AsyncClient() as client:
            print("Listing available models...")
            response = await client.get(url, headers=headers, timeout=30.0)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("Available models:")
                for model in result.get("models", []):
                    print(f"- {model.get('name')}: {model.get('displayName')}")
            else:
                print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")

async def test_gemini_api():
    """Test the Gemini API directly."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    
    if not api_key:
        print("ERROR: Gemini API key not found in environment variables")
        return
    
    print(f"Using Gemini API key: {api_key[:5]}...{api_key[-3:]}")
    
    # Try with current models based on the list
    urls = [
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.0-pro-vision-latest:generateContent"
    ]
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    data = {
        "contents": [{"parts": [{"text": "Hello, please respond with plain text only. What is 2+2?"}]}],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 100
        }
    }
    
    # Try each URL
    for url in urls:
        try:
            async with httpx.AsyncClient() as client:
                print(f"\nTrying endpoint: {url}")
                response = await client.post(url, headers=headers, json=data, timeout=30.0)
                print(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print("Response JSON keys:", result.keys())
                    
                    if "candidates" in result and result["candidates"]:
                        text = result["candidates"][0]["content"]["parts"][0]["text"]
                        print(f"Response text: {text}")
                        return  # Success, no need to try other URLs
                    else:
                        print("No candidates in response:", result)
                else:
                    print(f"Error response: {response.text}")
        except Exception as e:
            print(f"Exception with {url}: {str(e)}")

async def main():
    # First list available models
    await list_models()
    print("\n" + "-"*50 + "\n")
    # Then try to generate content
    await test_gemini_api()

if __name__ == "__main__":
    asyncio.run(main())