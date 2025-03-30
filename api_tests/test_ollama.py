import asyncio
import aiohttp
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

async def test_ollama_api():
    """Test the Ollama API directly using the same code as in llm_client.py"""
    provider = "Ollama"
    ollama_url = "http://127.0.0.1:11434"  # Using the exact URL from .env
    model = "phi4"
    
    # Test 1: Direct curl-like request
    logger.info(f"Test 1: Direct API call to {ollama_url}/api/chat")
    url = f"{ollama_url}/api/chat"
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"}
    ]
    data = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.4}
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            logger.info(f"Sending request to {url}")
            timeout = aiohttp.ClientTimeout(total=30)
            async with session.post(url, json=data, timeout=timeout) as response:
                logger.info(f"Response status: {response.status}")
                
                if response.status == 200:
                    result = await response.json(content_type=None)
                    logger.info(f"Success! Response: {json.dumps(result, indent=2)[:200]}...")
                else:
                    error_text = await response.text()
                    logger.error(f"API Error: {response.status} - {error_text[:500]}")
    except Exception as e:
        logger.exception(f"Error during API call: {e}")
    
    # Test 2: Try with different URL structure
    logger.info(f"\nTest 2: Alternative URL structure {ollama_url}/v1/chat/completions")
    url2 = f"{ollama_url}/v1/chat/completions"
    
    try:
        async with aiohttp.ClientSession() as session:
            logger.info(f"Sending request to {url2}")
            timeout = aiohttp.ClientTimeout(total=30)
            async with session.post(url2, json=data, timeout=timeout) as response:
                logger.info(f"Response status: {response.status}")
                
                if response.status == 200:
                    result = await response.json(content_type=None)
                    logger.info(f"Success! Response: {json.dumps(result, indent=2)[:200]}...")
                else:
                    error_text = await response.text()
                    logger.error(f"API Error: {response.status} - {error_text[:500]}")
    except Exception as e:
        logger.exception(f"Error during API call: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama_api())