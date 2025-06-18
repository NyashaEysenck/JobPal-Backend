# routes/cv_routes.py
from flask import Blueprint, request, jsonify, send_from_directory, current_app
import os
import uuid
from datetime import datetime
from services.cv_service import generate_cv_pdf

# Create a Blueprint for CV-related routes.
cv_bp = Blueprint('cv', __name__)

@cv_bp.route('/generate-cv', methods=['POST'])
def generate_cv():
    """
    Endpoint to generate a CV PDF from provided JSON data.

    Expects a JSON payload containing CV details (e.g., name, education, experience).
    A unique filename is generated, and the PDF is stored temporarily.
    """
    try:
        data = request.get_json()

        # Basic validation: ensure 'name' is provided.
        if not data or not data.get('name'):
            return jsonify({"error": "Invalid data", "details": "Name is required for CV generation."}), 400

        # Generate a unique filename to avoid collisions and enable easy cleanup.
        filename = f"cv_{uuid.uuid4().hex}.pdf"
        filepath = os.path.join(current_app.config['CV_FOLDER'], filename)

        # Call the service layer to handle the PDF generation logic.
        generate_cv_pdf(data, filepath)

        # Return details for downloading the generated CV.
        return jsonify({
            "success": True,
            "filename": filename,
            "downloadUrl": f"/download-cv/{filename}",
            "message": "CV generated successfully. Use the downloadUrl to retrieve it."
        }), 201 # HTTP 201 Created

    except Exception as e:
        # Log the error and return a generic error message to the client.
        current_app.logger.error(f"Error generating CV: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Failed to generate CV",
            "details": "An internal server error occurred."
        }), 500

@cv_bp.route('/download-cv/<filename>', methods=['GET'])
def download_cv(filename):
    """
    Endpoint to download a previously generated CV PDF.

    Includes security checks to prevent directory traversal attacks.
    """
    try:
        # Basic security check: ensure filename is safe and ends with .pdf.
        # This prevents directory traversal attacks.
        if not filename.endswith('.pdf') or '..' in filename or '/' in filename:
            current_app.logger.warning(f"Attempted download with invalid filename: {filename}")
            return jsonify({"error": "Invalid filename provided."}), 400

        # Serve the file from the configured CV folder.
        return send_from_directory(
            directory=current_app.config['CV_FOLDER'],
            path=filename,
            as_attachment=True, # Forces download rather than display in browser
            download_name=f"cv_{datetime.now().strftime('%Y%m%d')}.pdf", # Suggests a friendly download name
            mimetype='application/pdf' # Specifies content type
        )

    except FileNotFoundError:
        # Handle cases where the requested CV file does not exist.
        current_app.logger.warning(f"Attempted to download non-existent CV: {filename}")
        return jsonify({"error": "CV not found."}), 404
    except Exception as e:
        # Catch any other unexpected errors during file serving.
        current_app.logger.error(f"Error downloading CV {filename}: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to download CV."}), 500

