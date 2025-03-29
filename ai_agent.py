# ---- File: ai_agent.py ----

import os
import httpx
import json
import re  # Keep re for potential minor cleanup if needed, but not for core parsing
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv
import logging

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# --- Pydantic Models for Structured Output ---

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

    # Add an example for the LLM prompt
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


# --- Centralized System Prompt ---

# Note: We ask for JSON output directly matching the Pydantic schema.
# Create the system prompt with proper escaping for JSON schema
schema_json = json.dumps(CompetitiveAnalysis.model_json_schema(), indent=2)
example_json = json.dumps(CompetitiveAnalysis.model_config['json_schema_extra']['examples'][0], indent=2)

SYSTEM_PROMPT = """You are a Competitive Analysis Agent specialized in market research and competitor analysis.
Your task is to analyze the user's query and provide structured insights about competitors and market trends.
Provide factual information and strategic recommendations.

CRITICAL INSTRUCTION: You MUST respond ONLY with a valid JSON object that strictly adheres to the following Pydantic schema. Do NOT include any introductory text, explanations, apologies, or markdown formatting (like ```json ... ```) around the JSON object. Your entire response must be the JSON object itself.

Pydantic Schema:
```json
{0}
```

Example of the expected JSON format (use this structure):
```json
{1}
```

Analyze the user query below and return the JSON object.

User Query: {{user_query}}
"""

# Format the prompt template with the JSON schema and example
SYSTEM_PROMPT = SYSTEM_PROMPT.format(schema_json, example_json)


class AIClient:
    """Client for making AI API calls, expecting structured JSON output."""

    def __init__(self):
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.lmstudio_url = os.getenv("LMSTUDIO_URL", "http://localhost:1234/v1") # Ensure /v1
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3") # Default model
        self.lmstudio_model = os.getenv("LMSTUDIO_MODEL") # No default, needs to be set in .env
        self.gemini_model = os.getenv("GEMINI_MODEL", "models/gemini-1.5-flash-latest") # Use latest flash

        if not self.gemini_api_key:
            logger.warning("Gemini API key not found in environment variables. Gemini functionality will be disabled.")
        if not self.lmstudio_model:
             logger.warning("LMSTUDIO_MODEL not set in environment variables. LMStudio functionality may be limited.")

    def _prepare_prompt(self, query: str) -> str:
        """Formats the prompt with the user query."""
        # The SYSTEM_PROMPT is already pre-formatted with schema and example
        # Just need to replace the user_query placeholder
        return SYSTEM_PROMPT.replace("{{user_query}}", query)

    async def call_gemini(self, prompt: str) -> str:
        """Call Gemini API, requesting JSON output."""
        if not self.gemini_api_key:
            logger.error("Gemini API key is not configured.")
            return json.dumps({"error": "Gemini API key not configured"}) # Return JSON error

        # Ensure the model name starts with "models/" if it doesn't already
        model_name = self.gemini_model
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"

        url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.gemini_api_key
        }
        # Request JSON output explicitly
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.5, # Slightly lower temp might help with structured output
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 3072, # Increased max tokens for potentially larger JSON
                "response_mime_type": "application/json", # CRITICAL: Ask Gemini for JSON
            }
        }

        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Sending request to Gemini API ({self.gemini_model}) Prompt length: {len(prompt)}")
                response = await client.post(url, headers=headers, json=data, timeout=120.0) # Increased timeout
                logger.info(f"Gemini API response status: {response.status_code}")

                if response.status_code == 200:
                    # Gemini should return JSON directly because of response_mime_type
                    # Sometimes it might still wrap it, attempt to extract if necessary
                    try:
                        result = response.json()
                        # Standard Gemini structure check
                        if "candidates" in result and result["candidates"] and "content" in result["candidates"][0] and "parts" in result["candidates"][0]["content"]:
                            raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
                            # The raw_text *should* be the JSON string
                            logger.info(f"Gemini raw response text received (first 200 chars): {raw_text[:200]}...")
                            # Basic cleanup: remove potential markdown fences
                            cleaned_text = re.sub(r'^```json\s*|\s*```$', '', raw_text.strip(), flags=re.MULTILINE)
                            return cleaned_text
                        else:
                            logger.error(f"Unexpected Gemini API response structure: {result}")
                            return json.dumps({"error": "Unexpected Gemini API response structure", "details": result})
                    except json.JSONDecodeError:
                         # If the outer response isn't JSON (unexpected)
                         logger.error(f"Gemini response was not valid JSON. Status: {response.status_code}, Response: {response.text[:500]}")
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

    async def call_ollama(self, prompt: str) -> str:
        """Call Ollama API, expecting JSON output based on prompt."""
        url = f"{self.ollama_url}/api/generate"
        data = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "format": "json", # Explicitly ask Ollama for JSON format
            "options": { # Ollama specific generation parameters if needed
                 "temperature": 0.5,
                 "top_k": 40,
                 "top_p": 0.95,
                 # Ollama doesn't have maxOutputTokens here, depends on model limits/context size
            }
        }

        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Sending request to Ollama API ({self.ollama_model}). Prompt length: {len(prompt)}")
                response = await client.post(url, json=data, timeout=180.0) # Longer timeout for local models
                logger.info(f"Ollama API response status: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    raw_response = result.get("response", "")
                    logger.info(f"Ollama raw response received (first 200 chars): {raw_response[:200]}...")
                    # Ollama with format=json should return just the JSON string
                    # Basic cleanup: remove potential markdown fences just in case
                    cleaned_text = re.sub(r'^```json\s*|\s*```$', '', raw_response.strip(), flags=re.MULTILINE)
                    return cleaned_text
                else:
                    logger.error(f"Ollama API Error: {response.status_code} - {response.text}")
                    return json.dumps({"error": f"Ollama API Error: {response.status_code}", "details": response.text})
            except httpx.ReadTimeout:
                 logger.error("Ollama API request timed out.")
                 return json.dumps({"error": "Ollama API request timed out"})
            except Exception as e:
                logger.error(f"Error calling Ollama API: {e}", exc_info=True)
                return json.dumps({"error": f"Exception calling Ollama API: {str(e)}"})

    async def call_lmstudio(self, prompt: str) -> str:
        """Call LMStudio (OpenAI compatible) API, expecting JSON output based on prompt."""
        if not self.lmstudio_model:
             return json.dumps({"error": "LMStudio model not configured in .env (LMSTUDIO_MODEL)"})

        url = f"{self.lmstudio_url}/chat/completions" # Use chat completions endpoint
        data = {
            "model": self.lmstudio_model, # Model name might be required depending on LMStudio setup
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT.split("User Query:")[0].strip()}, # Extract system part
                {"role": "user", "content": prompt.split("User Query:")[-1].strip()} # Extract user query part
            ],
            "temperature": 0.5,
            "max_tokens": 3072, # Adjust as needed
             "response_format": {"type": "json_object"}, # Request JSON mode (OpenAI standard)
            "stream": False
        }

        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Sending request to LMStudio API ({self.lmstudio_model}). Prompt length: {len(prompt)}")
                response = await client.post(url, json=data, timeout=180.0) # Longer timeout
                logger.info(f"LMStudio API response status: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and result["choices"]:
                        message = result["choices"][0].get("message", {})
                        raw_response = message.get("content", "")
                        logger.info(f"LMStudio raw response received (first 200 chars): {raw_response[:200]}...")
                        # Basic cleanup: remove potential markdown fences
                        cleaned_text = re.sub(r'^```json\s*|\s*```$', '', raw_response.strip(), flags=re.MULTILINE)
                        return cleaned_text
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
        """Analyze competition by calling the selected LLM and parsing the expected JSON output."""
        logger.info(f"Starting analysis with model: {model}, query: {query[:50]}...")
        full_prompt = self._prepare_prompt(query)

        raw_response = ""
        try:
            if model == "gemini":
                if not self.gemini_api_key: return {"error": "Gemini API key not configured"}
                raw_response = await self.call_gemini(full_prompt)
            elif model == "lmstudio":
                 if not self.lmstudio_model: return {"error": "LMStudio model not configured"}
                 raw_response = await self.call_lmstudio(full_prompt)
            elif model == "ollama":
                raw_response = await self.call_ollama(full_prompt)
            else:
                logger.error(f"Invalid model selected: {model}")
                return {"error": f"Invalid model selected: {model}"}

            logger.info(f"Raw response received from {model} (length: {len(raw_response)})")
            # Attempt to parse the raw response as JSON directly into the Pydantic model
            analysis = CompetitiveAnalysis.model_validate_json(raw_response)
            logger.info(f"Successfully parsed response from {model} into CompetitiveAnalysis model.")
            return {
                "structured": analysis.model_dump(mode='json'), # Return dict representation
                "raw": raw_response # Still useful for debugging
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response from {model}: {e}", exc_info=True)
            logger.error(f"Raw response was: {raw_response[:1000]}...") # Log more of the failing response
            # Try to extract potential error message if the response itself was a JSON error object
            try:
                error_json = json.loads(raw_response)
                if "error" in error_json:
                     return {"error": f"LLM returned an error: {error_json.get('error')} - {error_json.get('details', '')}", "raw": raw_response}
            except Exception:
                 pass # Ignore if it wasn't a JSON error object
            return {"error": f"Failed to decode JSON response from {model}. Response was not valid JSON.", "raw": raw_response}

        except ValidationError as e:
            logger.error(f"Failed to validate JSON response from {model} against Pydantic schema: {e}", exc_info=True)
            logger.error(f"Raw response was: {raw_response[:1000]}...")
            return {
                "error": f"Response from {model} did not match the expected structure (Pydantic Validation Error).",
                "raw": raw_response,
                "validation_errors": e.errors() # Include Pydantic validation errors
            }
        except Exception as e:
            # Catch any other unexpected errors during processing
            logger.error(f"An unexpected error occurred during analysis with {model}: {e}", exc_info=True)
            return {
                "error": f"An unexpected error occurred: {str(e)}",
                "raw": raw_response # Include raw response if available
            }