# ---- File: agents/market_research_agent.py ----

import json
import logging
from typing import Dict, Any

from pydantic import ValidationError

# Import the generic LLM client and helper functions
from llm_client import AIClient, clean_json_response

# Import the specific schemas needed for this agent
from schemas.market_research import CompetitiveAnalysis

logger = logging.getLogger(__name__)

# --- Prompt Components specific to Market Research Agent ---
# Prepare schema and example JSON strings once, using the imported schema
try:
    schema_json = json.dumps(CompetitiveAnalysis.model_json_schema(), indent=2)
    example_json = json.dumps(CompetitiveAnalysis.model_config['json_schema_extra']['examples'][0], indent=2)
except Exception as e:
    logger.exception("Failed to generate schema/example JSON for Market Research Agent prompt.")
    # Set defaults or raise error to prevent startup with bad prompts
    schema_json = "{ 'error': 'schema generation failed' }"
    example_json = "{ 'error': 'example generation failed' }"


CORE_SYSTEM_INSTRUCTION = """You are a Competitive Analysis Agent specialized in market research and competitor analysis. Your task is to analyze the user's query and provide structured insights about competitors and market trends. Provide factual information and strategic recommendations. CRITICAL INSTRUCTION: You MUST respond ONLY with a valid JSON object that strictly adheres to the provided Pydantic schema. Do NOT include any introductory text, explanations, apologies, or markdown formatting (like ``` ... ```) around the JSON object. Your entire response must be the JSON object itself."""

SCHEMA_GUIDANCE = f"""The user requires the response formatted according to this Pydantic Schema:
{schema_json}

Here is an example of the exact JSON format required:
{example_json}

Analyze the user query below and return ONLY the valid JSON object matching the schema.
User Query: {{user_query}}"""
FULL_USER_PROMPT_TEMPLATE = SCHEMA_GUIDANCE


async def analyze_competition(query: str, model: str) -> Dict[str, Any]:
    """
    Performs competitive analysis using the selected LLM.

    Args:
        query: The user's query for competitive analysis.
        model: The identifier of the LLM model to use ('gemini', 'ollama', 'lmstudio').

    Returns:
        A dictionary containing either:
        - {"structured": analysis_dict, "raw": raw_response_str} on success.
        - {"error": error_message, "details": ..., "raw": raw_response_str} on failure.
    """
    logger.info(f"Market Research Agent: Starting analysis with model: {model}, query: {query[:50]}...")

    # Instantiate the generic AI Client
    # Consider dependency injection later if agents become more complex
    ai_client = AIClient()

    # Prepare the prompts for the LLM call
    system_instruction = CORE_SYSTEM_INSTRUCTION
    user_prompt_content = FULL_USER_PROMPT_TEMPLATE.replace("{{user_query}}", query)

    raw_response = ""
    structured_result = None
    error_result = None

    try:
        # Call the appropriate LLM provider via the client
        if model == "gemini":
            raw_response = await ai_client.call_gemini(system_instruction, user_prompt_content)
        elif model == "lmstudio":
             raw_response = await ai_client.call_lmstudio(system_instruction, user_prompt_content, json_schema=CompetitiveAnalysis.model_json_schema())
        elif model == "ollama":
            raw_response = await ai_client.call_ollama(system_instruction, user_prompt_content)
        else:
            # This case should ideally be caught before calling the agent
            logger.error(f"Market Research Agent: Invalid model requested: {model}")
            error_result = {"error": f"Invalid model selected for agent: {model}"}

        # Process the response if no error during model selection/call initiation
        if error_result is None:
            logger.info(f"Market Research Agent: Raw response received from {model} (length: {len(raw_response)})")

            # Clean the response first (remove potential markdown fences)
            cleaned_response = clean_json_response(raw_response)

            # Attempt to parse the cleaned response as JSON
            try:
                # Check if it's an error object returned by the client
                potential_error = json.loads(cleaned_response)
                if isinstance(potential_error, dict) and "error" in potential_error:
                    logger.error(f"Market Research Agent: LLM client returned an error for {model}: {potential_error}")
                    error_result = {"error": f"LLM call failed: {potential_error.get('error', 'Unknown error')}", "details": potential_error.get('details'), "raw": raw_response}
                else:
                     # Assume it's the actual data, proceed to Pydantic validation
                     pass

            except json.JSONDecodeError:
                 # Expected path if the response IS the valid JSON data
                 pass # Proceed to Pydantic validation
            except Exception as e:
                 logger.warning(f"Market Research Agent: Could not peek into raw response from {model}: {e}")
                 pass # Proceed anyway

            # --- If not an error object, validate with Pydantic ---
            if error_result is None:
                try:
                    analysis = CompetitiveAnalysis.model_validate_json(cleaned_response)
                    logger.info(f"Market Research Agent: Successfully validated response from {model}.")
                    structured_result = {
                        "structured": analysis.model_dump(mode='json'),
                        "raw": raw_response # Keep original raw for transparency
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
                     # Should be less likely now with cleaning first, but handle anyway
                    logger.error(f"Market Research Agent: Failed to decode cleaned JSON from {model}: {e}", exc_info=False)
                    logger.error(f"Cleaned response snippet: {cleaned_response[:1000]}...")
                    error_result = {"error": f"LLM {model} returned invalid JSON.", "raw": raw_response}

    except Exception as e:
        # Catch-all for unexpected errors within this agent's logic
        logger.exception(f"Market Research Agent: Unexpected error during analysis for model {model}: {e}")
        error_result = {
            "error": f"An unexpected application error occurred in the agent: {str(e)}",
            "raw": raw_response
        }

    # Return final result
    return structured_result if structured_result is not None else (error_result if error_result is not None else {"error": "Unknown state in Market Research Agent", "raw": raw_response})