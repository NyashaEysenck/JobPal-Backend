# routes/interview_routes.py
from flask import Blueprint, request, jsonify
import re
from services.gemini_service import get_gemini_response

# Create a Blueprint for interview-related routes.
interview_bp = Blueprint('interview', __name__)

@interview_bp.route('/interview-questions', methods=['POST', 'OPTIONS'])
def get_interview_questions():
    """
    Endpoint to generate interview questions and answer tips for a given role.

    Handles CORS preflight requests for POST methods.
    Interacts with the Gemini API to get intelligent questions and tips.
    Includes robust parsing logic to extract structured data from Gemini's text response.
    """
    # Handle CORS preflight requests.
    # This is necessary for complex (non-simple) HTTP requests, like POST with JSON payload.
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'preflight accepted'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response, 200

    data = request.json
    role = data.get('role', '').strip()

    # Validate input: role must be provided.
    if not role:
        return jsonify({"error": "Role is required to generate interview questions."}), 400

    try:
        # Construct a precise prompt for Gemini to guide its response format.
        prompt = f"""
        Generate a list of 10 common interview questions for the role of {role}.
        For each question, provide 3-5 tips on how to answer it effectively.
        Format the response as follows:

        1. [Question text]
           - Tips: [Tip 1], [Tip 2], [Tip 3], etc.

        2. [Question text]
           - Tips: [Tip 1], [Tip 2], [Tip 3], etc.

        ...and so on.

        Make sure each question is clearly numbered and each set of tips is on a separate line starting with "- Tips:".
        """

        gemini_response = get_gemini_response(prompt)

        # Robust parsing logic to extract questions and tips from Gemini's free-form text.
        questions_with_tips = []
        lines = gemini_response.strip().split("\n")
        current_question = None
        question_pattern = re.compile(r"^\s*(\d+)[\.\)]?\s*(.+)") # Matches numbered questions
        tips_pattern = re.compile(r"^\s*[-•*]?\s*(?:Tips|tips|TIPS)?:?\s*(.+)") # Matches tip lines

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            question_match = question_pattern.match(line)
            if question_match:
                # If a new question is found, store the previous one if it's complete.
                if current_question and current_question.get("question") and current_question.get("tips") is not None:
                    questions_with_tips.append(current_question)

                question_text = question_match.group(2).strip()
                current_question = {"question": question_text, "tips": []}
                i += 1
                continue

            tips_match = tips_pattern.match(line)
            if tips_match and current_question:
                tips_text = tips_match.group(1).strip()
                # Try splitting tips by common delimiters.
                parsed_tips = []
                for delimiter in [", ", "; ", "\n- ", " • "]:
                    if delimiter in tips_text:
                        parsed_tips = [tip.strip() for tip in tips_text.split(delimiter) if tip.strip()]
                        if parsed_tips:
                            break
                if not parsed_tips and tips_text:
                    parsed_tips = [tips_text] # Fallback to single tip if no delimiter found

                current_question["tips"].extend(parsed_tips)

                # Continue consuming lines that look like additional tips for the current question.
                j = i + 1
                while j < len(lines) and not question_pattern.match(lines[j].strip()):
                    next_line = lines[j].strip()
                    if next_line and (next_line.startswith("-") or next_line.startswith("•")):
                        tip = next_line.lstrip("-•").strip()
                        if tip:
                            current_question["tips"].append(tip)
                    j += 1
                i = j
                continue

            # Handle cases where tips might be on new lines without a "Tips:" prefix but start with a bullet.
            if current_question and (line.startswith("-") or line.startswith("•")):
                tip = line.lstrip("-•").strip()
                if tip:
                    current_question["tips"].append(tip)
            i += 1

        # Append the last processed question if it exists and is valid.
        if current_question and current_question.get("question") and current_question.get("tips") is not None:
            questions_with_tips.append(current_question)

        # Fallback parsing if initial structured parsing fails (e.g., Gemini returns less structured text).
        if not questions_with_tips:
            print("Warning: Initial parsing failed. Attempting fallback parsing for interview questions.")
            paragraphs = gemini_response.split("\n\n")
            for paragraph in paragraphs:
                lines = paragraph.strip().split("\n")
                if not lines:
                    continue
                potential_question = lines[0].strip()
                if re.search(r"^\d+[\.\)]|question|interview", potential_question.lower()):
                    question_text = re.sub(r"^\d+[\.\)]?\s*", "", potential_question).strip()
                    tips = []
                    for line in lines[1:]:
                        line = line.strip()
                        if line and not line.lower().startswith(("question", "interview")):
                            tip = re.sub(r"^[-•*]?\s*", "", line).strip()
                            if tip:
                                tips.append(tip)
                    if question_text and tips:
                        questions_with_tips.append({"question": question_text, "tips": tips})

        # Ensure a maximum of 10 questions and 5 tips per question for consistency.
        questions_with_tips = questions_with_tips[:10]
        for q in questions_with_tips:
            if not q["tips"]:
                q["tips"] = [
                    "Prepare specific examples from your experience.",
                    "Be concise and clear in your response.",
                    "Highlight relevant skills and accomplishments."
                ]
            q["tips"] = q["tips"][:5] # Limit tips to 5

        print(f"Successfully parsed {len(questions_with_tips)} interview questions.")
        return jsonify({"questions": questions_with_tips})
    except Exception as e:
        # Log and return a user-friendly error message in case of an exception.
        print(f"Error in /interview-questions: {str(e)}")
        return jsonify({
            "error": "Failed to generate interview questions at this time. Please try again later.",
            "questions": [] # Ensure an empty list is returned for frontend safety
        }), 500

