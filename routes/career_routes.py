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
    Endpoint to provide career guidance based on a specified program.
    
    Expects a JSON payload with a 'program' field.
    Returns structured career guidance with key skills, career paths, certifications, and industry trends.
    """
    try:
        # Validate request data
        if not request.json:
            return jsonify({"error": "Request must contain JSON data"}), 400
        
        data = request.json
        program = data.get("program", "").strip()
        
        if not program:
            return jsonify({"error": "Program field is required and cannot be empty"}), 400
        
        if len(program) < 2:
            return jsonify({"error": "Program field must be at least 2 characters long"}), 400
        
        if len(program) > 100:
            return jsonify({"error": "Program field must be less than 100 characters"}), 400

        # Craft a detailed prompt for Gemini to generate career guidance in the expected format
        prompt = f"""
        You are a professional career advisor. Provide comprehensive career guidance for someone studying {program}.
        
        Return the response as valid JSON with this EXACT structure:
        {{
            "keySkills": [
                "Skill 1",
                "Skill 2",
                "Skill 3",
                "Skill 4",
                "Skill 5"
            ],
            "careerPaths": [
                "Career Path 1",
                "Career Path 2", 
                "Career Path 3",
                "Career Path 4",
                "Career Path 5"
            ],
            "certifications": [
                "Certification 1",
                "Certification 2",
                "Certification 3",
                "Certification 4"
            ],
            "industryTrends": [
                "Industry Trend 1",
                "Industry Trend 2",
                "Industry Trend 3",
                "Industry Trend 4"
            ]
        }}
        
        Requirements:
        - Provide 5-8 key skills that are essential for this field
        - List 5-7 realistic career paths/job titles
        - Include 4-6 relevant certifications or qualifications
        - Describe 4-5 current industry trends affecting this field
        - All entries should be concise but informative (1-2 sentences max)
        - Return ONLY valid JSON, no additional text or markdown
        """
        
        gemini_response = get_gemini_response(prompt)

        # Clean the response more thoroughly
        cleaned_response = gemini_response.strip()
        
        # Remove common markdown formatting
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        elif cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]
            
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
            
        cleaned_response = cleaned_response.strip()

        # Parse the JSON response
        try:
            structured_output = json.loads(cleaned_response)
        except json.JSONDecodeError as parse_error:
            print(f"JSON parsing error in /career_guidance: {parse_error}")
            print(f"Raw Gemini response: {gemini_response}")
            print(f"Cleaned response: {cleaned_response}")
            return jsonify({
                "error": "Failed to parse career guidance from AI service",
                "message": "The AI service returned an invalid response format"
            }), 500

        # Validate the response structure
        required_fields = ['keySkills', 'careerPaths', 'certifications', 'industryTrends']
        response_data = {}
        
        for field in required_fields:
            field_data = structured_output.get(field, [])
            
            # Ensure it's a list
            if not isinstance(field_data, list):
                print(f"Warning: '{field}' field was not a list: {type(field_data)}")
                field_data = []
            
            # Ensure it's not empty
            if len(field_data) == 0:
                print(f"Warning: '{field}' field was empty")
                # Provide fallback data based on field type
                if field == 'keySkills':
                    field_data = [f"Core skills relevant to {program}"]
                elif field == 'careerPaths':
                    field_data = [f"Entry-level positions in {program}"]
                elif field == 'certifications':
                    field_data = [f"Industry certifications for {program}"]
                elif field == 'industryTrends':
                    field_data = [f"Current trends in {program} industry"]
            
            response_data[field] = field_data

        # Validate that we have some meaningful data
        total_items = sum(len(response_data[field]) for field in required_fields)
        if total_items < 4:  # At least one item per category
            return jsonify({
                "error": "Insufficient career guidance data generated",
                "message": "Please try again or contact support if the issue persists"
            }), 500

        return jsonify(response_data)

    except Exception as e:
        print(f"Unexpected error in /career_guidance: {e}")
        return jsonify({
            "error": "An unexpected error occurred while processing your request",
            "message": "Please try again later or contact support if the issue persists"
        }), 500