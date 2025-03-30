# ---- File: agents/market_research_agent.py ----

import json
import logging
from typing import Dict, Any, Optional

from pydantic import ValidationError, BaseModel

# Import the generic LLM client and helper functions
from llm_client import AIClient, clean_json_response, create_error_json

# Import the specific schemas needed for this agent
from schemas.market_research import CompetitiveAnalysis

logger = logging.getLogger(__name__)

# --- Prompt Components ---
# Ensure schema generation handles potential errors
try:
    # Generate schema as Dict, not just string for potential use later
    competitive_analysis_schema: Dict[str, Any] = CompetitiveAnalysis.model_json_schema()
    schema_json_str: str = json.dumps(competitive_analysis_schema, indent=2)
    # Access examples safely with get() method
    model_config = getattr(CompetitiveAnalysis, 'model_config', {})
    json_schema_extra = model_config.get('json_schema_extra', {})
    examples = json_schema_extra.get('examples', [{}])
    example_json_str: str = json.dumps(examples[0] if examples else {}, indent=2)
except Exception as e:
    logger.exception("Failed to generate schema/example JSON for Market Research Agent prompt.")
    schema_json_str = '{ "error": "schema generation failed" }'
    example_json_str = '{ "error": "example generation failed" }'
    competitive_analysis_schema = {} # Default empty schema


CORE_SYSTEM_INSTRUCTION = """You are a Competitive Analysis Agent specialized in market research and competitor analysis. Your task is to analyze the user's query and provide structured insights about competitors and market trends. Provide factual information and strategic recommendations. CRITICAL INSTRUCTION: You MUST respond ONLY with a valid JSON object that strictly adheres to the provided Pydantic schema. Do NOT include any introductory text, explanations, apologies, or markdown formatting (like ``` ... ```) around the JSON object. Your entire response must be the JSON object itself."""

SCHEMA_GUIDANCE = f"""The user requires the response formatted according to this Pydantic Schema:
{schema_json_str}

Here is an example of the exact JSON format required:
{example_json_str}

Analyze the user query below and return ONLY the valid JSON object matching the schema.
User Query: {{user_query}}"""
FULL_USER_PROMPT_TEMPLATE = SCHEMA_GUIDANCE


# Add specific return type hint: Dict[str, Any]
async def analyze_competition(query: str, model: str) -> Dict[str, Any]:
    """
    Performs competitive analysis using the selected LLM.
    Returns a dictionary containing results or error information.
    """
    # ... implementation ...
    logger.info(f"Market Research Agent: Starting analysis with model: {model}, query: {query[:50]}...")
    ai_client = AIClient()
    system_instruction = CORE_SYSTEM_INSTRUCTION
    user_prompt_content = FULL_USER_PROMPT_TEMPLATE.replace("{{user_query}}", query)

    raw_response: str = ""
    structured_result: Optional[Dict[str, Any]] = None
    error_result: Optional[Dict[str, Any]] = None

    try:
        # Determine schema usage based on model type (Example for LMStudio)
        schema_to_pass: Optional[Dict[str, Any]] = None
        if model == "lmstudio":
            # Pass the schema dict if using LMStudio and it supports it
            # schema_to_pass = competitive_analysis_schema # Disabled for now, using standard json_object mode
            pass # Keep using standard json_object mode for broader compatibility


        # Call the appropriate LLM provider via the client
        if model == "gemini":
            raw_response = await ai_client.call_gemini(system_instruction, user_prompt_content)
        elif model == "lmstudio":
             # Pass schema if needed, otherwise None
             raw_response = await ai_client.call_lmstudio(system_instruction, user_prompt_content, json_schema=schema_to_pass)
        elif model == "ollama":
            raw_response = await ai_client.call_ollama(system_instruction, user_prompt_content)
        else:
            logger.error(f"Market Research Agent: Invalid model requested: {model}")
            error_result = {"error": f"Invalid model selected for agent: {model}"}

        # Process the response if no error during model selection/call initiation
        if error_result is None:
            logger.info(f"Market Research Agent: Raw response received from {model} (length: {len(raw_response)})")
            cleaned_response = clean_json_response(raw_response)

            if not cleaned_response: # Handle empty cleaned response
                 logger.error(f"Market Research Agent: Received empty response from {model} after cleaning.")
                 error_result = {"error": f"LLM {model} returned an empty response.", "raw": raw_response}
            else:
                try:
                    # Check if it's an error object returned by the client
                    potential_error = json.loads(cleaned_response)
                    if isinstance(potential_error, dict) and "error" in potential_error:
                        logger.error(f"Market Research Agent: LLM client returned an error for {model}: {potential_error}")
                        error_result = {"error": f"LLM call failed: {potential_error.get('error', 'Unknown error')}", "details": potential_error.get('details'), "raw": raw_response}
                except json.JSONDecodeError:
                     # Expected path if the response IS the valid JSON data
                     pass # Proceed to Pydantic validation
                except Exception as e:
                     logger.warning(f"Market Research Agent: Could not peek into raw response from {model}: {e}")
                     pass # Proceed anyway

                # --- If not an error object, validate with Pydantic ---
                if error_result is None:
                    try:
                        # Use the imported CompetitiveAnalysis model for validation
                        analysis: CompetitiveAnalysis = CompetitiveAnalysis.model_validate_json(cleaned_response)
                        logger.info(f"Market Research Agent: Successfully validated response from {model}.")
                        structured_result = {
                            "structured": analysis.model_dump(mode='json'),
                            "raw": raw_response
                        }
                    except ValidationError as e:
                        logger.error(f"Market Research Agent: Pydantic validation failed for {model}: {e}", exc_info=False)
                        logger.error(f"Cleaned response snippet: {cleaned_response[:1000]}...")
                        error_result = {
                            "error": f"Response from {model} did not match expected structure.",
                            "raw": raw_response,
                            "validation_errors": e.errors()
                        }
                    except json.JSONDecodeError as e:
                        logger.error(f"Market Research Agent: Failed to decode cleaned JSON from {model}: {e}", exc_info=False)
                        logger.error(f"Cleaned response snippet: {cleaned_response[:1000]}...")
                        error_result = {"error": f"LLM {model} returned invalid JSON.", "raw": raw_response}

    except Exception as e:
        logger.exception(f"Market Research Agent: Unexpected error during analysis for model {model}: {e}")
        # Ensure raw_response is included if available
        error_result = {
            "error": f"An unexpected application error occurred in the agent: {str(e)}",
            "raw": raw_response if raw_response else "Raw response not available"
        }

    # Return final result, ensure a dict is always returned
    final_result = structured_result if structured_result is not None else (error_result if error_result is not None else {"error": "Unknown state in Market Research Agent", "raw": raw_response if raw_response else "N/A"})
    return final_result