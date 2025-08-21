import logging
import json
import google.generativeai as genai

from src.core.config import config
from src.api.v1.schemas.analyzer_schemas import ModelChoice


def load_pre_prompt():
    """
    Loads the pre-defined prompt text from a file specified in the configuration.

    The prompt is used for initializing the language model with context or instructions
    before performing detailed analysis.

    Returns:
        str: The content of the pre-prompt file as a string.

    Raises:
        FileNotFoundError: If the pre-prompt file cannot be found at the specified path.
        IOError: If there is an error reading the pre-prompt file.
    """

    prompt_path = config.GBP_ANALYSIS_PROMPT_PATH

    try:
        with open(prompt_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        logging.error(
            f"CRITICAL: Prompt template file not found at path: '{prompt_path}'"
        )
        return "Please provide a professional analysis of the following business data: {business_data_json}"  # noqa
    except Exception as e:
        logging.error(f"Error loading prompt template from '{prompt_path}': {e}")
        return "Error loading prompt."


PROMPT_TEMPLATE = load_pre_prompt()

try:
    genai.configure(api_key=config.GEMINI_API_KEY)
except Exception as e:
    logging.error(f"Error configuring Generative AI: {e}")


def get_llm_analysis(
    business_data: dict, score: float, model_choice: ModelChoice
) -> str:
    """
    Takes structured data, sends it to the chosen Google Gemini model using a
    file-based prompt template, and returns a detailed analysis.
    """

    if model_choice == ModelChoice.PRO:
        selected_model_name = config.GEMINI_MODEL_PRO
    else:
        selected_model_name = config.GEMINI_MODEL_FLASH

    logging.info(f"Using Gemini model: {selected_model_name}")

    try:
        model = genai.GenerativeModel(selected_model_name)
    except Exception as e:
        logging.error(f"Could not initialize Gemini model '{selected_model_name}': {e}")
        return "LLM analysis is currently unavailable (could not initialize model)."

    business_data_as_json_string = json.dumps(business_data, indent=2)

    final_prompt = PROMPT_TEMPLATE.format(
        business_data_json=business_data_as_json_string, score=score
    )

    try:
        response = model.generate_content(final_prompt)
        return response.text.strip()
    except Exception as e:
        logging.error(
            f"Error calling Google Gemini API with model {selected_model_name}: {e}"
        )
        return "Failed to generate detailed analysis due to an API error."
