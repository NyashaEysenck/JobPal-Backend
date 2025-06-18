# routes/career_routes.py
from flask import Blueprint, request, jsonify
import json
from services.gemini_service import get_gemini_response

# Create a Blueprint for career-related routes.
# This helps in organizing routes and applying specific prefixes or middleware.
career_bp = Blueprint('career', __name__)

@career_bp.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    """
    Endpoint to retrieve career opportunities based on a specified program.

    Expects a JSON payload with a 'program' field.
    Leverages the Gemini API to fetch structured job recommendations.
    """
    data = request.json
    program = data.get("program", "Unknown Program")

    # Construct a detailed prompt for the Gemini API to ensure structured JSON output.
    prompt = f"""
        Provide a structured JSON response with career opportunities for a degree in {program}.
        The JSON must have this format:
        {{
        "jobs": [
            {{
            "title": "Job Title",
            "description": "Brief job description.",
            "skills": ["Skill1", "Skill2"],
            "education": "Required education level",
            "outlook": "Job market outlook",
            "salary": "Average salary range"
            }}
        ]
        }}
        """
    gemini_response = get_gemini_response(prompt)

    # Clean the Gemini response by removing markdown code block delimiters.
    cleaned_response = gemini_response.strip('```json \n').strip('```')

    try:
        # Attempt to parse the cleaned response as JSON.
        structured_output = json.loads(cleaned_response)
        recommendations = structured_output.get("jobs", [])

        # Ensure that the 'jobs' field is indeed a list.
        if not isinstance(recommendations, list):
            print(f"Warning: 'jobs' field in Gemini response was not a list: {type(recommendations)}")
            recommendations = [] # Default to an empty list to prevent errors

        return jsonify(recommendations)
    except json.JSONDecodeError as e:
        # Log parsing errors for debugging purposes.
        print(f"JSON parsing error in /get_recommendations: {e}. Raw response: {cleaned_response}")
        return jsonify({"error": "Failed to parse recommendations from AI.", "details": str(e)}), 500
    except Exception as e:
        # Catch any other unexpected errors during processing.
        print(f"An unexpected error occurred in /get_recommendations: {e}")
        return jsonify({"error": "An unexpected error occurred.", "details": str(e)}), 500

@career_bp.route('/career_guidance', methods=['POST'])
def career_guidance():
    """
    Endpoint to provide general career guidance based on a specified program.

    Expects a JSON payload with a 'program' field.
    The response is formatted as structured JSON containing guidance sections.
    """
    data = request.json
    program = data.get("program", "Unknown Program")

    # Craft a prompt for Gemini to generate career guidance.
    # Emphasize the JSON structure for consistent parsing.
    prompt = f"""
    You are a career advisor. Provide career guidance for someone with a degree in {program}.
    Return the response in valid JSON format with the following structure:
    {{
        "guidance": [
            {{
                "section_title": "Section Title (e.g., 'Key Skills to Develop')",
                "content": "Detailed advice for this section."
            }},
            {{
                "section_title": "Networking Strategies",
                "content": "Advice on how to network effectively."
            }}
            // ... more sections as appropriate
        ]
    }}
    Ensure all content is within the 'content' field for each section.
    """
    gemini_response = get_gemini_response(prompt)

    # Clean the response to remove any extraneous markdown.
    cleaned_response = gemini_response.strip('```json \n').strip('```')

    try:
        # Attempt to load the cleaned response as JSON.
        structured_output = json.loads(cleaned_response)

        # Validate that the 'guidance' key exists and is a list.
        guidance_data = structured_output.get("guidance", [])
        if not isinstance(guidance_data, list):
            print(f"Warning: 'guidance' field was not a list: {type(guidance_data)}")
            guidance_data = []

        return jsonify(guidance_data)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error in /career_guidance: {e}. Raw response: {cleaned_response}")
        return jsonify({"error": "Failed to parse career guidance from AI.", "details": str(e)}), 500
    except Exception as e:
        print(f"An unexpected error occurred in /career_guidance: {e}")
        return jsonify({"error": "An unexpected error occurred.", "details": str(e)}), 500

