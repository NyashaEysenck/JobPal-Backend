from flask import Flask, render_template, request, send_file ,jsonify, send_from_directory
import google.generativeai as genai
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from dotenv import load_dotenv
import os, re
from io import StringIO
import uuid
from fpdf import FPDF
from datetime import datetime
import shutil
from threading import Timer


from flask_cors import CORS, cross_origin # Import CORS

# Load environment variables from the .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all domains (or specify the frontend URL)
# Alternatively, you can specify which origins are allowed:
CORS(app, resources={r"/*": {"origins": "*"}})


# Configure Gemini API
  # Replace with your actual API key
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Function to interact with Gemini API
def get_gemini_response(prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
   
    return response.text  # Gemini may return a plain text response


@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    data = request.json
    program = data.get("program", "Unknown Program")
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

    response = get_gemini_response(prompt)
    print(response)
    print("Type of response:", type(response))  # Debugging: Print response type

    # Clean the response to remove unwanted backticks and extra characters
    cleaned_response = response.strip('```json \n').strip('```')

    try:
        structured_output = json.loads(cleaned_response)  # Convert cleaned response to dictionary
        print("Parsed structured_output:", structured_output)  # Debugging: Check parsed JSON

        # Ensure "jobs" exists and is a list
        recommendations = structured_output.get("jobs", [])

        if not isinstance(recommendations, list):
            print("Unexpected format for jobs:", type(recommendations))  # Debugging: Check if "jobs" is a list
            recommendations = []

        print("Final recommendations:", recommendations)  # Debugging: Check final output

        return jsonify(recommendations)  # Ensure frontend gets an array

    except json.JSONDecodeError as e:
        print("JSON parsing error:", e)  # Debugging: Show decoding errors
        return jsonify([])  # Return empty list if parsing fails




# Configuration
app.config.update({
    'CV_FOLDER': 'temp_cvs',          # Folder to store generated CVs
    'MAX_CV_AGE_HOURS': 24,           # Maximum age of CV files in hours
    'CLEANUP_INTERVAL': 3600,         # Cleanup interval in seconds (1 hour)
    'MAX_CVS_STORED': 100,            # Maximum number of CVs to keep
})

# Ensure the temp directory exists
os.makedirs(app.config['CV_FOLDER'], exist_ok=True)

class ModernCV(FPDF):
    """Custom PDF class with modern styling"""
    
    def __init__(self):
        super().__init__()
        self.primary_color = (70, 130, 180)  # SteelBlue
        self.secondary_color = (100, 100, 100)  # DarkGray
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        # Skip header on first page
        if self.page_no() == 1:
            return
        
        self.set_font('Arial', 'B', 10)
        self.set_text_color(*self.secondary_color)
        self.cell(0, 10, f"{os.getenv('APP_NAME', 'Professional CV')} - Page {self.page_no()}", 0, 0, 'C')
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(*self.secondary_color)
        self.cell(0, 10, f"Generated on {datetime.now().strftime('%Y-%m-%d')}", 0, 0, 'C')

def generate_cv_pdf(data, filename):
    """Generate a modern styled CV PDF"""
    pdf = ModernCV()
    pdf.add_page()
    
    # Personal Information Section
    pdf.set_font("Arial", 'B', 24)
    pdf.set_text_color(*pdf.primary_color)
    pdf.cell(0, 15, txt=data['name'], ln=1, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.set_text_color(*pdf.secondary_color)
    contact_info = f"{data['email']} | {data['phone']}"
    pdf.cell(0, 10, txt=contact_info, ln=1, align='C')
    pdf.ln(15)
    
    # Professional Summary
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(*pdf.primary_color)
    pdf.cell(0, 10, txt="PROFESSIONAL SUMMARY", ln=1)
    pdf.set_line_width(0.5)
    pdf.set_draw_color(*pdf.primary_color)
    pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
    pdf.ln(8)
    
    pdf.set_font("Arial", size=11)
    pdf.set_text_color(0, 0, 0)  # Black
    pdf.multi_cell(0, 6, txt=data['summary'])
    pdf.ln(12)
    
    # Education Section
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(*pdf.primary_color)
    pdf.cell(0, 10, txt="EDUCATION", ln=1)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
    pdf.ln(8)
    
    for edu in data['education']:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 7, txt=edu['institution'], ln=1)
        
        pdf.set_font("Arial", size=11)
        pdf.set_text_color(*pdf.secondary_color)
        pdf.cell(0, 6, txt=f"{edu['degree']} | {edu['year']}", ln=1)
        
        if edu['description']:
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 5, txt=edu['description'])
            pdf.set_font("Arial", size=11)
        
        pdf.ln(5)
    
    # Work Experience Section
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(*pdf.primary_color)
    pdf.cell(0, 10, txt="WORK EXPERIENCE", ln=1)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
    pdf.ln(8)
    
    for exp in data['experience']:
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 7, txt=exp['company'], ln=1)
        
        pdf.set_font("Arial", size=11)
        pdf.set_text_color(*pdf.secondary_color)
        date_range = f"{exp['startDate']} - {exp['endDate'] or 'Present'}"
        pdf.cell(0, 6, txt=f"{exp['position']} | {date_range}", ln=1)
        
        if exp['description']:
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 5, txt=exp['description'])
            pdf.set_font("Arial", size=11)
        
        pdf.ln(5)
    
    # Skills Section
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(*pdf.primary_color)
    pdf.cell(0, 10, txt="SKILLS", ln=1)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
    pdf.ln(8)
    
    pdf.set_font("Arial", size=11)
    pdf.set_text_color(0, 0, 0)
    skills = " • ".join([skill.strip() for skill in data['skills'] if skill.strip()])
    pdf.multi_cell(0, 7, txt=skills)
    
    # Save the PDF
    pdf.output(os.path.join(app.config['CV_FOLDER'], filename))

def cleanup_cv_files():
    """Clean up old CV files"""
    try:
        now = datetime.now()
        cv_files = []
        
        # Get all CV files with their creation time
        for filename in os.listdir(app.config['CV_FOLDER']):
            if filename.endswith('.pdf'):
                filepath = os.path.join(app.config['CV_FOLDER'], filename)
                created_time = datetime.fromtimestamp(os.path.getctime(filepath))
                age_hours = (now - created_time).total_seconds() / 3600
                cv_files.append((filepath, created_time, age_hours))
        
        # Sort by oldest first
        cv_files.sort(key=lambda x: x[1])
        
        # Delete files that are too old or if we have too many
        deleted_count = 0
        for filepath, _, age_hours in cv_files:
            if (age_hours > app.config['MAX_CV_AGE_HOURS'] or 
                len(cv_files) - deleted_count > app.config['MAX_CVS_STORED']):
                try:
                    os.remove(filepath)
                    deleted_count += 1
                except Exception as e:
                    app.logger.error(f"Error deleting file {filepath}: {str(e)}")
        
        app.logger.info(f"Cleaned up {deleted_count} CV files")
        
    except Exception as e:
        app.logger.error(f"Error during CV cleanup: {str(e)}")
    
    # Schedule next cleanup
    Timer(app.config['CLEANUP_INTERVAL'], cleanup_cv_files).start()

@app.route('/generate-cv', methods=['POST'])
def generate_cv():
    """Endpoint to generate and store a CV"""
    try:
        data = request.get_json()
        
        # Validate required data
        if not data or 'name' not in data:
            return jsonify({"error": "Invalid data", "details": "Name is required"}), 400
        
        # Generate a unique filename
        filename = f"cv_{uuid.uuid4().hex}.pdf"
        
        # Generate and save the PDF
        generate_cv_pdf(data, filename)
        
        # Return the download information
        return jsonify({
            "success": True,
            "filename": filename,
            "downloadUrl": f"/download-cv/{filename}",
            "message": "CV generated successfully. Use the downloadUrl to retrieve it."
        })
    
    except Exception as e:
        app.logger.error(f"Error generating CV: {str(e)}")
        return jsonify({
            "error": "Failed to generate CV",
            "details": str(e)
        }), 500

@app.route('/download-cv/<filename>', methods=['GET'])
def download_cv(filename):
    """Endpoint to download a generated CV"""
    try:
        # Security check - simple validation
        if not filename.endswith('.pdf') or '..' in filename or '/' in filename:
            return jsonify({"error": "Invalid filename"}), 400
        
        return send_from_directory(
            directory=app.config['CV_FOLDER'],
            path=filename,
            as_attachment=True,
            download_name=f"cv_{datetime.now().strftime('%Y%m%d')}.pdf",
            mimetype='application/pdf'
        )
    
    except FileNotFoundError:
        return jsonify({"error": "CV not found"}), 404
    except Exception as e:
        app.logger.error(f"Error downloading CV {filename}: {str(e)}")
        return jsonify({"error": "Failed to download CV"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cv_files_count": len([f for f in os.listdir(app.config['CV_FOLDER']) if f.endswith('.pdf')])
    })

# Start the cleanup scheduler
cleanup_cv_files()


@app.route('/interview-questions', methods=['POST', 'OPTIONS'])
def get_interview_questions():
    print("Entered interview-questions endpoint")
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'status': 'preflight accepted'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response, 200  # Explicit HTTP 200 status

    
    data = request.json
    role = data.get('role', '').strip()

    if not role:
        return jsonify({"error": "Role is required."}), 400

    try:
        # Generate a prompt for Gemini that's clear but not overly restrictive
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
        
        # Get the response from Gemini
        gemini_response = get_gemini_response(prompt)
        print(f"Raw Gemini response received: {gemini_response[:100]}...")  # Log first 100 chars
        
        # More robust parsing logic
        questions_with_tips = []
        lines = gemini_response.strip().split("\n")
        current_question = None
        question_pattern = re.compile(r"^\s*(\d+)[\.\)]?\s+(.+)")
        tips_pattern = re.compile(r"^\s*[-•*]?\s*(?:Tips|tips|TIPS)?:?\s*(.+)")

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:  # Skip empty lines
                i += 1
                continue
                
            # Check for question pattern (number followed by text)
            question_match = question_pattern.match(line)
            if question_match:
                # Save previous question if exists
                if current_question and current_question.get("question") and current_question.get("tips"):
                    questions_with_tips.append(current_question)
                
                # Extract question text, removing any numbering
                question_text = question_match.group(2).strip()
                current_question = {"question": question_text, "tips": []}
                i += 1
                continue
            
            # Check for tips pattern
            tips_match = tips_pattern.match(line)
            if tips_match and current_question:
                # Extract tips text
                tips_text = tips_match.group(1).strip()
                
                # Try different delimiters for tips
                for delimiter in [", ", "; ", "\n- ", " • "]:
                    if delimiter in tips_text:
                        tips = [tip.strip() for tip in tips_text.split(delimiter) if tip.strip()]
                        if tips:
                            current_question["tips"] = tips
                            break
                
                # If no delimiter worked, treat as a single tip
                if not current_question["tips"] and tips_text:
                    current_question["tips"] = [tips_text]
                    
                # Look ahead for additional tips on subsequent lines
                j = i + 1
                while j < len(lines) and not question_pattern.match(lines[j].strip()):
                    next_line = lines[j].strip()
                    if next_line and not next_line.lower().startswith("tips:"):
                        # Check if this might be a continuation of tips
                        if next_line.startswith("-") or next_line.startswith("•"):
                            tip = next_line.lstrip("-•").strip()
                            if tip:
                                current_question["tips"].append(tip)
                    j += 1
                
                i = j
                continue
            
            # If we're here, the line didn't match our patterns
            # Check if it might be a tip without the "Tips:" prefix
            if current_question and line.startswith("-") or line.startswith("•"):
                tip = line.lstrip("-•").strip()
                if tip:
                    current_question["tips"].append(tip)
            
            i += 1

        # Add the last question if it exists
        if current_question and current_question.get("question") and current_question.get("tips"):
            questions_with_tips.append(current_question)

        # Handle case where we couldn't parse any questions
        if not questions_with_tips:
            print("Failed to parse questions from response, attempting fallback parsing")
            
            # Fallback: Try to extract questions and tips with minimal structure
            paragraphs = gemini_response.split("\n\n")
            for paragraph in paragraphs:
                lines = paragraph.strip().split("\n")
                if not lines:
                    continue
                    
                # First line might be a question
                potential_question = lines[0].strip()
                if re.search(r"^\d+[\.\)]|question|interview", potential_question.lower()):
                    # Clean up the question text
                    question_text = re.sub(r"^\d+[\.\)]?\s*", "", potential_question)
                    
                    # Look for tips in remaining lines
                    tips = []
                    for line in lines[1:]:
                        line = line.strip()
                        if line and not line.lower().startswith(("question", "interview")):
                            # Clean up the tip text
                            tip = re.sub(r"^[-•*]?\s*", "", line)
                            if tip:
                                tips.append(tip)
                    
                    if question_text and tips:
                        questions_with_tips.append({
                            "question": question_text,
                            "tips": tips
                        })

        # Ensure we have at least some questions
        if not questions_with_tips:
            print("WARNING: Could not parse any questions from the response")
            # Create a minimal valid response with an explanation
            questions_with_tips = [{
                "question": f"Common interview question for {role}",
                "tips": [
                    "Prepare specific examples from your experience",
                    "Research the company before the interview",
                    "Practice your answers out loud",
                    "Follow up with thoughtful questions for the interviewer"
                ]
            }]

        # Limit to 10 questions maximum
        questions_with_tips = questions_with_tips[:10]
        
        # Ensure each question has at least some tips
        for q in questions_with_tips:
            if not q["tips"]:
                q["tips"] = [
                    "Prepare specific examples",
                    "Be concise and clear in your response",
                    "Highlight relevant skills and experience"
                ]
            # Limit to 5 tips maximum per question
            q["tips"] = q["tips"][:5]

        print(f"Successfully parsed {len(questions_with_tips)} questions")
        return jsonify({"questions": questions_with_tips})
    except Exception as e:
        print(f"Error in get_interview_questions: {str(e)}")
        # Return a more user-friendly error message
        return jsonify({
            "error": "We couldn't generate interview questions at this time. Please try again later.",
            "questions": []  # Include an empty questions array for the frontend to handle gracefully
        }), 500

@app.route('/career_guidance', methods=['POST'])
def career_guidance():
    data = request.json
    program = data.get("program", "Unknown Program")

    prompt = f"""
    You are a career advisor. Provide career guidance for someone with a degree in {program}.
    Return the response in **valid JSON format** with the following structure:
    
    {{
        "keySkills": ["Skill 1", "Skill 2", "Skill 3"],
        "certifications": ["Certification 1", "Certification 2"],
        "careerPaths": ["Career Path 1", "Career Path 2"],
        "industryTrends": ["Trend 1", "Trend 2"]
    }}

    Do not include any extra text outside the JSON format.
    """

    response = get_gemini_response(prompt)
    print("Raw response:", response)  # Debugging: Print raw response

    # Clean the response by removing unwanted characters
    cleaned_response = response.strip('```json \n').strip('```')
    print("Cleaned response:", cleaned_response)  # Debugging: Print cleaned response

    try:
        structured_output = json.loads(cleaned_response)  # Convert to dictionary
        print("Parsed structured_output:", structured_output)  # Debugging: Check parsed JSON

        # Ensure expected structure
        expected_keys = ["keySkills", "certifications", "careerPaths", "industryTrends"]
        guidance_data = {key: structured_output.get(key, []) for key in expected_keys}

        # Validate that all expected values are lists
        for key in expected_keys:
            if not isinstance(guidance_data[key], list):
                print(f"Unexpected format for {key}: {type(guidance_data[key])}")  # Debugging
                guidance_data[key] = ["Invalid data format"]

        print("Final structured output:", guidance_data)  # Debugging: Check final output
        return jsonify(guidance_data)

    except json.JSONDecodeError as e:
        print("JSON parsing error:", e)  # Debugging: Show error
        return jsonify({"error": "Error parsing career guidance."})

if __name__ == '__main__':
    app.run(host="0.0.0.0",     port=int(os.environ.get("PORT", 5000)), debug=False)
    # Start the cleanup scheduler
    cleanup_cv_files()