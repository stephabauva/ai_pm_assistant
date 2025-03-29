# ---- File: ai_agent.py ----

import os
import httpx
import json
import re
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field, ValidationError, SecretStr
import logging

# Import the global settings instance
from config import settings

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s')
logger = logging.getLogger(__name__)

# --- Pydantic Models --- (No changes needed)
class CompetitorInfo(BaseModel):
    name: str = Field(..., description="Name of the competitor")
    strengths: List[str] = Field(..., description="Key strengths of the competitor")
    weaknesses: List[str] = Field(..., description="Key weaknesses of the competitor")
    market_share: Optional[str] = Field(None, description="Estimated market share if known")
    key_features: List[str] = Field(..., description="Notable features or capabilities")
    pricing: Optional[str] = Field(None, description="Pricing information if available")

class MarketTrend(BaseModel):
    trend: str = Field(..., description="Description of the market trend")
    impact: str = Field(..., description="Potential impact on the product")
    opportunity: Optional[str] = Field(None, description="Potential opportunity this presents")
    threat: Optional[str] = Field(None, description="Potential threat this presents")

class CompetitiveAnalysis(BaseModel):
    competitors: List[CompetitorInfo] = Field(..., description="List of key competitors and their analysis")
    market_trends: List[MarketTrend] = Field(..., description="Key market trends relevant to the product")
    recommendations: List[str] = Field(..., description="Strategic recommendations based on the analysis")
    summary: str = Field(..., description="Executive summary of the competitive landscape")
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "competitors": [{"name": "ExampleCorp","strengths": ["Large user base"],"weaknesses": ["Slow innovation"],"market_share": "Approx. 30%","key_features": ["Core Platform"],"pricing": "$100/user/month"}],
                    "market_trends": [{"trend": "AI Integration","impact": "Increased demand","opportunity": "Develop AI features.","threat": "Competitors move faster."}],
                    "recommendations": ["Invest R&D in AI.","Simplify pricing."],
                    "summary": "Market shifting towards AI."
                }
            ] # Simplified example for brevity in logs if needed
        }
    }

# --- Centralized Prompt Components ---
# Using simplified example for schema guidance construction
schema_json = json.dumps(CompetitiveAnalysis.model_json_schema(), indent=2)
example_json = json.dumps(CompetitiveAnalysis.model_config['json_schema_extra']['examples'][0], indent=2)

CORE_SYSTEM_INSTRUCTION = """You are a Competitive Analysis Agent specialized in market research and competitor analysis. Your task is to analyze the user's query and provide structured insights about competitors and market trends. Provide factual information and strategic recommendations. CRITICAL INSTRUCTION: You MUST respond ONLY with a valid JSON object that strictly adheres to the provided Pydantic schema. Do NOT include any introductory text, explanations, apologies, or markdown formatting (like ``` ... ```) around the JSON object. Your entire response must be the JSON object itself."""

SCHEMA_GUIDANCE = f"""The user requires the response formatted according to this Pydantic Schema:
{schema_json}

Here is an example of the exact JSON format required:
{example_json}

Analyze the user query below and return ONLY the valid JSON object matching the schema.
User Query: {{user_query}}"""
FULL_USER_PROMPT_TEMPLATE = SCHEMA_GUIDANCE

def clean_json_response(text: str) -> str:
    """Removes optional markdown fences and strips whitespace."""
    if not isinstance(text, str): # Handle potential non-string inputs gracefully
        return ""
    # Remove leading/trailing fences and whitespace
    # Handles ```json, ```, and optional leading/trailing spaces/newlines
    cleaned = re.sub(r'^\s*```(?:json)?\s*', '', text.strip(), flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r'\s*```\s*$', '', cleaned, flags=re.MULTILINE)
    return cleaned.strip()

# --- Standard Error Response Format ---
def create_error_json(message: str, details: Any = None) -> str:
    """Creates a standardized JSON string for error responses."""
    error_obj = {"error": message}
    if details:
        # Ensure details are serializable (convert complex objects to string)
        if not isinstance(details, (str, int, float, bool, list, dict, type(None))):
             details = str(details)
        error_obj["details"] = details
    return json.dumps(error_obj)

class AIClient:
    """Client for making AI API calls using chat-oriented endpoints."""
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
        """Call Gemini API using system instructions and user content."""
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
                            return clean_json_response(raw_text)
                        else:
                            error_detail = result.get("promptFeedback", result) # Use full result if no feedback
                            logger.error(f"{provider}: Unexpected API response structure or blocked content: {error_detail}")
                            return create_error_json(f"{provider}: Unexpected API response or blocked content", error_detail)
                    except json.JSONDecodeError:
                        logger.error(f"{provider}: Response body was not valid JSON. Status: {response.status_code}, Response: {response.text[:200]}...")
                        return create_error_json(f"{provider}: Response body was not valid JSON", response.text[:500])
                    except Exception as e:
                        logger.exception(f"{provider}: Error processing response JSON: {e}")
                        return create_error_json(f"{provider}: Error processing response", str(e))
                else:
                    error_text = response.text[:500] # Limit error text length
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
        """Call Ollama API using the /api/chat endpoint."""
        provider = "Ollama"
        url = f"{self.ollama_url}/api/chat"
        messages = [{"role": "system", "content": system_instruction}, {"role": "user", "content": user_prompt}]
        data = {"model": self.ollama_model, "messages": messages, "stream": False, "format": "json", "options": {"temperature": 0.4, "top_k": 40, "top_p": 0.95}}

        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Sending request to {provider} Chat API ({self.ollama_model})")
                response = await client.post(url, json=data, timeout=180.0)
                logger.info(f"{provider} API response status: {response.status_code}")

                if response.status_code == 200:
                    try:
                        result = response.json()
                        if "message" in result and "content" in result["message"]:
                             raw_response = result["message"]["content"]
                             logger.info(f"{provider} raw response received (first 100 chars): {raw_response[:100]}...")
                             return clean_json_response(raw_response)
                        else:
                             logger.error(f"{provider}: Unexpected chat response structure: {result}")
                             return create_error_json(f"{provider}: Unexpected chat response structure", result)
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

    async def call_lmstudio(self, system_instruction: str, user_prompt: str) -> str:
        """Call LMStudio (OpenAI compatible) API using chat completions."""
        provider = "LMStudio"
        if not self.lmstudio_model:
             logger.error(f"{provider}: Model name not configured.")
             return create_error_json(f"{provider} model not configured")

        url = f"{self.lmstudio_url}/chat/completions"
        messages = [{"role": "system", "content": system_instruction}, {"role": "user", "content": user_prompt}]
        data = {"model": self.lmstudio_model, "messages": messages, "temperature": 0.4, "max_tokens": 3500, "response_format": {"type": "json_object"}, "stream": False}

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
                            return clean_json_response(raw_response)
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

    async def analyze_competition(self, query: str, model: str = "ollama") -> Dict[str, Any]:
        """Analyze competition by structuring messages for chat APIs and parsing JSON output."""
        logger.info(f"Starting analysis with model: {model}, query: {query[:50]}...")
        user_prompt_content = FULL_USER_PROMPT_TEMPLATE.replace("{{user_query}}", query)
        raw_response = ""
        structured_result: Optional[Dict[str, Any]] = None
        error_result: Optional[Dict[str, Any]] = None

        try:
            # --- Call the selected LLM provider ---
            if model == "gemini":
                raw_response = await self.call_gemini(CORE_SYSTEM_INSTRUCTION, user_prompt_content)
            elif model == "lmstudio":
                 raw_response = await self.call_lmstudio(CORE_SYSTEM_INSTRUCTION, user_prompt_content)
            elif model == "ollama":
                raw_response = await self.call_ollama(CORE_SYSTEM_INSTRUCTION, user_prompt_content)
            else:
                logger.error(f"Invalid model requested for analysis: {model}")
                error_result = {"error": f"Invalid model selected: {model}"}
                # No raw response to add in this specific case

            # --- Process the response (if no error during model selection) ---
            if error_result is None:
                logger.info(f"Raw response received from {model} (length: {len(raw_response)})")

                # Attempt to parse the raw response as JSON directly
                try:
                    # First, try parsing as JSON to check if it's an error object we generated
                    potential_error = json.loads(raw_response)
                    if isinstance(potential_error, dict) and "error" in potential_error:
                        logger.error(f"LLM call for {model} returned an error object: {potential_error}")
                        # Propagate the error, keeping the raw response
                        error_result = {"error": f"LLM call failed: {potential_error.get('error', 'Unknown error')}", "details": potential_error.get('details'), "raw": raw_response}
                    else:
                         # If it's not our error object, assume it *should* be the competitive analysis JSON
                         # Re-raise JSONDecodeError if it wasn't a dict or didn't have 'error' key? No, proceed to validation.
                         pass # Proceed to Pydantic validation

                except json.JSONDecodeError:
                     # This is the expected path if the response IS the valid JSON data (not an error obj)
                     # So, we proceed to Pydantic validation below.
                     pass
                except Exception as e:
                     # Unexpected error just trying to peek at the response
                     logger.warning(f"Could not peek into raw response from {model} for error checking: {e}")
                     # Proceed to Pydantic validation anyway, it might still be valid

                # --- If it wasn't identified as an internal error object, validate with Pydantic ---
                if error_result is None:
                    try:
                        analysis = CompetitiveAnalysis.model_validate_json(raw_response)
                        logger.info(f"Successfully parsed and validated response from {model}.")
                        structured_result = {
                            "structured": analysis.model_dump(mode='json'),
                            "raw": raw_response # Include raw for debugging/transparency
                        }
                    except ValidationError as e:
                        logger.error(f"Pydantic validation failed for {model} response: {e}", exc_info=False)
                        logger.error(f"Raw response snippet: {raw_response[:1000]}...")
                        error_result = {
                            "error": f"Response from {model} did not match the expected structure.",
                            "raw": raw_response,
                            "validation_errors": e.errors()
                        }
                    except json.JSONDecodeError as e:
                        # This might happen if clean_json_response failed or LLM gave truly malformed JSON
                        logger.error(f"Failed to decode JSON response from {model} even after checks: {e}", exc_info=False)
                        logger.error(f"Raw response snippet: {raw_response[:1000]}...")
                        error_result = {"error": f"Failed to decode JSON response from {model}. LLM likely returned invalid JSON.", "raw": raw_response}

        except Exception as e:
            # Catch-all for unexpected errors during the analysis process itself
            logger.exception(f"Unexpected error during analyze_competition for model {model}: {e}")
            error_result = {
                "error": f"An unexpected application error occurred: {str(e)}",
                "raw": raw_response # Include raw if available
            }

        # Return either the structured result or the error result
        return structured_result if structured_result is not None else (error_result if error_result is not None else {"error": "Unknown state in analyze_competition", "raw": raw_response})