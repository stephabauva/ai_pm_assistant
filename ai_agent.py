import os
import httpx
import json
import re
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field, ValidationError, SecretStr
# Removed dotenv import here, handled in config.py
import logging
# Import the global settings instance
from config import settings

# Setup logging (remains the same)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# --- Pydantic Models --- (Keep these as they are)
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
    """Structured analysis of competitors and market trends for a product."""
    competitors: List[CompetitorInfo] = Field(..., description="List of key competitors and their analysis")
    market_trends: List[MarketTrend] = Field(..., description="Key market trends relevant to the product")
    recommendations: List[str] = Field(..., description="Strategic recommendations based on the analysis")
    summary: str = Field(..., description="Executive summary of the competitive landscape")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "competitors": [
                        {
                            "name": "ExampleCorp",
                            "strengths": ["Large user base", "Strong brand recognition"],
                            "weaknesses": ["Slow innovation cycle", "Complex pricing"],
                            "market_share": "Approx. 30%",
                            "key_features": ["Core Platform", "Advanced Analytics Module"],
                            "pricing": "Starts at $100/user/month"
                        }
                    ],
                    "market_trends": [
                        {
                            "trend": "AI Integration in Business Tools",
                            "impact": "Increased demand for automated insights and efficiency.",
                            "opportunity": "Develop AI-powered features.",
                            "threat": "Competitors launching AI features faster."
                        }
                    ],
                    "recommendations": [
                        "Invest R&D in AI capabilities.",
                        "Simplify the pricing structure.",
                        "Target niche markets with specialized features."
                    ],
                    "summary": "The market is shifting towards AI integration, where ExampleCorp faces challenges in innovation speed despite its strong market presence."
                }
            ]
        }
    }

# --- Centralized Prompt Components --- (Keep these as they are)
schema_json = json.dumps(CompetitiveAnalysis.model_json_schema(), indent=2)
example_json = json.dumps(CompetitiveAnalysis.model_config['json_schema_extra']['examples'][0], indent=2)

CORE_SYSTEM_INSTRUCTION = """You are a Competitive Analysis Agent specialized in market research and competitor analysis.
Your task is to analyze the user's query and provide structured insights about competitors and market trends.
Provide factual information and strategic recommendations.

CRITICAL INSTRUCTION: You MUST respond ONLY with a valid JSON object that strictly adheres to the provided Pydantic schema. Do NOT include any introductory text, explanations, apologies, or markdown formatting (like ```json ... ```) around the JSON object. Your entire response must be the JSON object itself."""

SCHEMA_GUIDANCE = f"""The user requires the response formatted according to this Pydantic Schema:
{schema_json}

Here is an example of the exact JSON format required:
{example_json}

Analyze the user query below and return ONLY the valid JSON object matching the schema.
User Query: {{user_query}}"""
FULL_USER_PROMPT_TEMPLATE = SCHEMA_GUIDANCE

def clean_json_response(text: str) -> str:
    """Removes optional json markdown fences and strips whitespace.""" # Updated regex to handle optional 'json' label after fences more reliably
    cleaned = re.sub(r'^(?:json)?\s*```', '', text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r'```$', '', cleaned)
    return cleaned.strip()

class AIClient:
    """Client for making AI API calls using chat-oriented endpoints for better token efficiency."""
    def __init__(self):
        # Load configuration directly from the imported settings object
        self.gemini_api_key: Optional[SecretStr] = settings.gemini_api_key
        self.ollama_url: str = str(settings.ollama_url) # Convert HttpUrl to string
        self.lmstudio_url: str = str(settings.lmstudio_url) # Convert HttpUrl to string
        self.ollama_model: str = settings.ollama_model
        self.lmstudio_model: Optional[str] = settings.lmstudio_model
        self.gemini_model: str = settings.gemini_model

        # Log warnings based on loaded settings
        if not self.gemini_api_key:
            logger.warning("AIClient initialized: Gemini API key not found. Gemini calls will fail.")
        if not self.lmstudio_model:
            logger.warning("AIClient initialized: LMSTUDIO_MODEL not set. LMStudio calls will fail.")

    async def call_gemini(self, system_instruction: str, user_prompt: str) -> str:
        """Call Gemini API using system instructions and user content."""
        if not self.gemini_api_key:
            return json.dumps({"error": "Gemini API key not configured"})

        # Use model name from settings
        model_name = self.gemini_model
        # Ensure model name format (Gemini specific)
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent"

        headers = {
            "Content-Type": "application/json",
            # Use .get_secret_value() for SecretStr types
            "x-goog-api-key": self.gemini_api_key.get_secret_value()
        }
        data = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "temperature": 0.4,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 3500,
                "response_mime_type": "application/json",
            }
        }

        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Sending request to Gemini API ({model_name})")
                response = await client.post(url, headers=headers, json=data, timeout=120.0)
                logger.info(f"Gemini API response status: {response.status_code}")

                if response.status_code == 200:
                    try:
                        result = response.json()
                        if "candidates" in result and result["candidates"] and "content" in result["candidates"][0] and "parts" in result["candidates"][0]["content"]:
                            raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
                            logger.info(f"Gemini raw response text received (first 200 chars): {raw_text[:200]}...")
                            return clean_json_response(raw_text)
                        else:
                            error_detail = result.get("promptFeedback", "No candidates found in response.")
                            logger.error(f"Unexpected Gemini API response structure or blocked content: {error_detail}")
                            return json.dumps({"error": "Unexpected Gemini API response structure or blocked content", "details": error_detail})
                    except json.JSONDecodeError:
                        logger.error(f"Gemini response body was not valid JSON. Status: {response.status_code}, Response: {response.text[:500]}")
                        return json.dumps({"error": "Gemini response body was not valid JSON", "details": response.text[:500]})
                    except Exception as e:
                        logger.error(f"Error processing Gemini response JSON: {e}", exc_info=True)
                        return json.dumps({"error": f"Error processing Gemini response: {str(e)}", "details": response.text[:500]})
                else:
                    logger.error(f"Gemini API Error: {response.status_code} - {response.text}")
                    return json.dumps({"error": f"Gemini API Error: {response.status_code}", "details": response.text})
            except httpx.ReadTimeout:
                logger.error("Gemini API request timed out.")
                return json.dumps({"error": "Gemini API request timed out"})
            except Exception as e:
                logger.error(f"Error calling Gemini API: {e}", exc_info=True)
                return json.dumps({"error": f"Exception calling Gemini API: {str(e)}"})

    async def call_ollama(self, system_instruction: str, user_prompt: str) -> str:
        """Call Ollama API using the /api/chat endpoint."""
        # Use URL and model from settings
        url = f"{self.ollama_url}/api/chat"
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ]
        data = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {
                 "temperature": 0.4,
                 "top_k": 40,
                 "top_p": 0.95,
            }
        }

        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Sending request to Ollama Chat API ({self.ollama_model})")
                response = await client.post(url, json=data, timeout=180.0)
                logger.info(f"Ollama API response status: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    if "message" in result and "content" in result["message"]:
                         raw_response = result["message"]["content"]
                         logger.info(f"Ollama raw response received (first 200 chars): {raw_response[:200]}...")
                         return clean_json_response(raw_response)
                    else:
                         logger.error(f"Unexpected Ollama chat response structure: {result}")
                         return json.dumps({"error": "Unexpected Ollama chat response structure", "details": result})
                else:
                    logger.error(f"Ollama API Error: {response.status_code} - {response.text}")
                    return json.dumps({"error": f"Ollama API Error: {response.status_code}", "details": response.text})
            except httpx.ReadTimeout:
                logger.error("Ollama API request timed out.")
                return json.dumps({"error": "Ollama API request timed out"})
            except Exception as e:
                logger.error(f"Error calling Ollama API: {e}", exc_info=True)
                return json.dumps({"error": f"Exception calling Ollama API: {str(e)}"})

    async def call_lmstudio(self, system_instruction: str, user_prompt: str) -> str:
        """Call LMStudio (OpenAI compatible) API using chat completions."""
        if not self.lmstudio_model:
             return json.dumps({"error": "LMStudio model not configured"})

        # Use URL and model from settings
        url = f"{self.lmstudio_url}/chat/completions"
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ]
        data = {
            "model": self.lmstudio_model,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 3500,
            "response_format": {"type": "json_object"},
            "stream": False
        }

        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Sending request to LMStudio API ({self.lmstudio_model})")
                response = await client.post(url, json=data, timeout=180.0)
                logger.info(f"LMStudio API response status: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and result["choices"]:
                        message = result["choices"][0].get("message", {})
                        raw_response = message.get("content", "")
                        logger.info(f"LMStudio raw response received (first 200 chars): {raw_response[:200]}...")
                        return clean_json_response(raw_response)
                    else:
                        logger.error(f"Unexpected LMStudio response structure: {result}")
                        return json.dumps({"error": "Unexpected LMStudio response structure", "details": result})
                else:
                    logger.error(f"LMStudio API Error: {response.status_code} - {response.text}")
                    return json.dumps({"error": f"LMStudio API Error: {response.status_code}", "details": response.text})
            except httpx.ReadTimeout:
                logger.error("LMStudio API request timed out.")
                return json.dumps({"error": "LMStudio API request timed out"})
            except Exception as e:
                logger.error(f"Error calling LMStudio API: {e}", exc_info=True)
                return json.dumps({"error": f"Exception calling LMStudio API: {str(e)}"})

    async def analyze_competition(self, query: str, model: str = "ollama") -> Dict[str, Any]:
        """Analyze competition by structuring messages for chat APIs and parsing JSON output."""
        logger.info(f"Starting analysis with model: {model}, query: {query[:50]}...")

        user_prompt_content = FULL_USER_PROMPT_TEMPLATE.replace("{{user_query}}", query)
        raw_response = ""

        try:
            if model == "gemini":
                raw_response = await self.call_gemini(CORE_SYSTEM_INSTRUCTION, user_prompt_content)
            elif model == "lmstudio":
                 raw_response = await self.call_lmstudio(CORE_SYSTEM_INSTRUCTION, user_prompt_content)
            elif model == "ollama":
                raw_response = await self.call_ollama(CORE_SYSTEM_INSTRUCTION, user_prompt_content)
            else:
                logger.error(f"Invalid model selected: {model}")
                return {"error": f"Invalid model selected: {model}"}

            logger.info(f"Raw response received from {model} (length: {len(raw_response)})")

            # Check if the response indicates an error before attempting to parse
            try:
                # Peek into the response to see if it's a JSON error object we generated
                potential_error = json.loads(raw_response)
                if isinstance(potential_error, dict) and "error" in potential_error:
                     logger.error(f"LLM call returned an error object: {potential_error}")
                     return {"error": f"LLM call failed: {potential_error.get('error', 'Unknown error')} {potential_error.get('details', '')}", "raw": raw_response}
            except json.JSONDecodeError:
                 # This is expected if the response is the actual valid JSON data
                 pass
            except Exception as e:
                 # Unexpected error trying to peek
                 logger.warning(f"Could not peek into raw response for error checking: {e}")


            # --- Attempt to parse the (presumed valid) raw response as JSON ---
            analysis = CompetitiveAnalysis.model_validate_json(raw_response)
            logger.info(f"Successfully parsed response from {model} into CompetitiveAnalysis model.")
            return {
                "structured": analysis.model_dump(mode='json'),
                "raw": raw_response
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response from {model}: {e}", exc_info=False) # Less verbose log
            logger.error(f"Raw response snippet: {raw_response[:1000]}...")
            return {"error": f"Failed to decode JSON response from {model}. LLM likely returned invalid JSON.", "raw": raw_response}

        except ValidationError as e:
            logger.error(f"Failed to validate JSON response from {model} against Pydantic schema: {e}", exc_info=False) # Less verbose log
            logger.error(f"Raw response snippet: {raw_response[:1000]}...")
            # Simplify error message for UI
            return {
                "error": f"Response from {model} did not match the expected structure. Check logs for details.",
                "raw": raw_response,
                "validation_errors": e.errors() # Keep validation errors for debugging if needed
            }
        except Exception as e:
            logger.error(f"An unexpected error occurred during analysis processing with {model}: {e}", exc_info=True)
            return {
                "error": f"An unexpected processing error occurred: {str(e)}",
                "raw": raw_response
            }