# services/gemini_service.py
import google.generativeai as genai
import os

# Module-level variable to store the Gemini model instance.
_gemini_model = None

def configure_gemini(api_key):
    """
    Configures the Google Gemini API with the provided API key.

    This should be called once during application startup.
    Raises ValueError if the API key is missing.
    """
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
    # Initialize the model once to reuse it across requests.
    global _gemini_model
    _gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    print("Gemini API successfully configured and model initialized.")

def get_gemini_response(prompt):
    """
    Interacts with the configured Gemini model to get a text response.

    Args:
        prompt (str): The text prompt to send to the Gemini model.

    Returns:
        str: The text content of the Gemini model's response.

    Raises:
        RuntimeError: If the Gemini model has not been configured.
        Exception: For any other errors during API interaction.
    """
    if _gemini_model is None:
        raise RuntimeError("Gemini model not configured. Call configure_gemini() first.")
    try:
        response = _gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        # Log the specific error for debugging.
        print(f"Error calling Gemini API with prompt: '{prompt[:100]}...'. Error: {e}")
        # Re-raise or return a specific error indication as per error handling strategy.
        raise Exception(f"Failed to get response from Gemini API: {e}")

