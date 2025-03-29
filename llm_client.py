# ---- File: llm_client.py ----

import httpx
import json
import re
import logging
import aiohttp
from typing import Optional, Any
from pydantic import SecretStr

# Import the global settings instance
from config import settings

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s')
logger = logging.getLogger(__name__)


def clean_json_response(text: str) -> str:
    """Removes optional markdown fences and strips whitespace."""
    if not isinstance(text, str):
        return ""
    cleaned = re.sub(r'^\s*```(?:json)?\s*', '', text.strip(), flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r'\s*```\s*$', '', cleaned, flags=re.MULTILINE)
    return cleaned.strip()

def create_error_json(message: str, details: Any = None) -> str:
    """Creates a standardized JSON string for error responses."""
    error_obj = {"error": message}
    if details:
        if not isinstance(details, (str, int, float, bool, list, dict, type(None))):
             details = str(details)
        error_obj["details"] = details
    return json.dumps(error_obj)


class AIClient:
    """Client for making generic AI API calls using chat-oriented endpoints."""

    def __init__(self):
        self.gemini_api_key: Optional[SecretStr] = settings.gemini_api_key
        self.ollama_url: str = str(settings.ollama_url)
        self.lmstudio_url: str = str(settings.lmstudio_url)
        self.ollama_model: str = settings.ollama_model
        self.lmstudio_model: Optional[str] = settings.lmstudio_model
        self.gemini_model: str = settings.gemini_model

        if not self.gemini_api_key:
            logger.warning("AIClient initialized: Gemini API key not found. Gemini calls will fail.")
        if not self.lmstudio_model:
            logger.warning("AIClient initialized: LMSTUDIO_MODEL not set. LMStudio calls will fail.")

    async def call_gemini(self, system_instruction: str, user_prompt: str) -> str:
        """Calls Gemini API. Returns raw response string or error JSON string."""
        provider = "Gemini"
        if not self.gemini_api_key:
            logger.error(f"{provider}: API key not configured.")
            return create_error_json(f"{provider} API key not configured")

        model_name = self.gemini_model
        if not model_name.startswith("models/"): model_name = f"models/{model_name}"
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent"

        headers = {"Content-Type": "application/json", "x-goog-api-key": self.gemini_api_key.get_secret_value()}
        data = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": 0.4, "topK": 40, "topP": 0.95, "maxOutputTokens": 3500, "response_mime_type": "application/json"}
        }

        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Sending request to {provider} API ({model_name})")
                response = await client.post(url, headers=headers, json=data, timeout=120.0)
                logger.info(f"{provider} API response status: {response.status_code}")

                if response.status_code == 200:
                    try:
                        result = response.json()
                        if "candidates" in result and result["candidates"] and "content" in result["candidates"][0] and "parts" in result["candidates"][0]["content"]:
                            raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
                            logger.info(f"{provider} raw response received (first 100 chars): {raw_text[:100]}...")
                            # Return the raw text, cleaning is caller's responsibility if needed after error check
                            return raw_text
                        else:
                            error_detail = result.get("promptFeedback", result)
                            logger.error(f"{provider}: Unexpected API response structure or blocked content: {error_detail}")
                            return create_error_json(f"{provider}: Unexpected API response or blocked content", error_detail)
                    except json.JSONDecodeError:
                        logger.error(f"{provider}: Response body was not valid JSON. Status: {response.status_code}, Response: {response.text[:200]}...")
                        return create_error_json(f"{provider}: Response body was not valid JSON", response.text[:500])
                    except Exception as e:
                        logger.exception(f"{provider}: Error processing response JSON: {e}")
                        return create_error_json(f"{provider}: Error processing response", str(e))
                else:
                    error_text = response.text[:500]
                    logger.error(f"{provider} API Error: {response.status_code} - {error_text}")
                    return create_error_json(f"{provider} API Error: {response.status_code}", error_text)
        except httpx.ReadTimeout:
            logger.error(f"{provider} API request timed out.")
            return create_error_json(f"{provider} API request timed out")
        except httpx.RequestError as e:
            logger.error(f"{provider}: Network error calling API: {e}")
            return create_error_json(f"{provider}: Network error", str(e))
        except Exception as e:
            logger.exception(f"{provider}: Unexpected error during API call: {e}")
            return create_error_json(f"{provider}: Unexpected error", str(e))

    async def call_ollama(self, system_instruction: str, user_prompt: str) -> str:
        """Calls Ollama Chat API. Returns raw response string or error JSON string."""
        provider = "Ollama"
        # Use a hardcoded URL to avoid any URL parsing issues
        url = "http://127.0.0.1:11434/api/chat"
        messages = [{"role": "system", "content": system_instruction}, {"role": "user", "content": user_prompt}]
        data = {"model": self.ollama_model, "messages": messages, "stream": False, "options": {"temperature": 0.4, "top_k": 40, "top_p": 0.95}}

        try:
            # Use aiohttp instead of httpx
            async with aiohttp.ClientSession() as session:
                logger.info(f"Sending request to {provider} Chat API ({self.ollama_model}) at URL: {url}")
                async with session.post(url, json=data, timeout=180) as response:
                    logger.info(f"{provider} API response status: {response.status}")
                    
                    if response.status == 200:
                        try:
                            result = await response.json()
                            if "message" in result and "content" in result["message"]:
                                raw_response = result["message"]["content"]
                                logger.info(f"{provider} raw response received (first 100 chars): {raw_response[:100]}...")
                                return raw_response
                            else:
                                logger.error(f"{provider}: Unexpected chat response structure: {result}")
                                return create_error_json(f"{provider}: Unexpected chat response structure", result)
                        except json.JSONDecodeError:
                            response_text = await response.text()
                            logger.error(f"{provider}: Response body was not valid JSON. Status: {response.status}, Response: {response_text[:200]}...")
                            return create_error_json(f"{provider}: Response body was not valid JSON", response_text[:500])
                        except Exception as e:
                            logger.exception(f"{provider}: Error processing response JSON: {e}")
                            return create_error_json(f"{provider}: Error processing response", str(e))
                    else:
                        error_text = await response.text()
                        logger.error(f"{provider} API Error: {response.status} - {error_text[:500]}")
                        return create_error_json(f"{provider} API Error: {response.status}", error_text[:500])
        except aiohttp.ClientTimeout:
            logger.error(f"{provider} API request timed out.")
            return create_error_json(f"{provider} API request timed out")
        except aiohttp.ClientError as e:
            logger.error(f"{provider}: Network error calling API: {e}, URL: {url}")
            return create_error_json(f"{provider}: Network error", str(e))
        except Exception as e:
            logger.exception(f"{provider}: Unexpected error during API call: {e}")
            return create_error_json(f"{provider}: Unexpected error", str(e))

    async def call_lmstudio(self, system_instruction: str, user_prompt: str, json_schema: Optional[dict] = None) -> str:
        """Calls LMStudio API. Returns raw response string or error JSON string."""
        provider = "LMStudio"
        if not self.lmstudio_model:
            logger.error(f"{provider}: Model name not configured.")
            return create_error_json(f"{provider} model not configured")

        url = f"{self.lmstudio_url}/chat/completions"
        messages = [{"role": "system", "content": system_instruction}, {"role": "user", "content": user_prompt}]
        data = {"model": self.lmstudio_model, "messages": messages, "temperature": 0.4, "max_tokens": 3500, "stream": False}
        if json_schema:
            data["response_format"] = {"type": "json_schema", "json_schema": {"schema": json_schema}}

        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Sending request to {provider} API ({self.lmstudio_model})")
                response = await client.post(url, json=data, timeout=180.0)
                logger.info(f"{provider} API response status: {response.status_code}")

                if response.status_code == 200:
                    try:
                        result = response.json()
                        if "choices" in result and result["choices"] and "message" in result["choices"][0] and "content" in result["choices"][0]["message"]:
                            raw_response = result["choices"][0]["message"]["content"]
                            logger.info(f"{provider} raw response received (first 100 chars): {raw_response[:100]}...")
                            return raw_response
                        else:
                            logger.error(f"{provider}: Unexpected response structure: {result}")
                            return create_error_json(f"{provider}: Unexpected response structure", result)
                    except json.JSONDecodeError:
                        logger.error(f"{provider}: Response body was not valid JSON. Status: {response.status_code}, Response: {response.text[:200]}...")
                        return create_error_json(f"{provider}: Response body was not valid JSON", response.text[:500])
                    except Exception as e:
                         logger.exception(f"{provider}: Error processing response JSON: {e}")
                         return create_error_json(f"{provider}: Error processing response", str(e))
                else:
                    error_text = response.text[:500]
                    logger.error(f"{provider} API Error: {response.status_code} - {error_text}")
                    return create_error_json(f"{provider} API Error: {response.status_code}", error_text)
        except httpx.ReadTimeout:
            logger.error(f"{provider} API request timed out.")
            return create_error_json(f"{provider} API request timed out")
        except httpx.RequestError as e:
            logger.error(f"{provider}: Network error calling API: {e}")
            return create_error_json(f"{provider}: Network error", str(e))
        except Exception as e:
            logger.exception(f"{provider}: Unexpected error during API call: {e}")
            return create_error_json(f"{provider}: Unexpected error", str(e))