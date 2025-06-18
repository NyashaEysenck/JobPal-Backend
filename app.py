from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from the .env file at the very start
load_dotenv()

# Import configuration and services
from config import AppConfig
from routes.career_routes import career_bp
from routes.cv_routes import cv_bp
from routes.interview_routes import interview_bp
from services.gemini_service import configure_gemini
from utils.cleanup_utils import start_cleanup_scheduler

def create_app():
    """
    Creates and configures the Flask application instance.
    ... (rest of your create_app function remains the same)
    """
    app = Flask(__name__)
    app.config.from_object(AppConfig)
    CORS(app, resources={r"/*": {"origins": "*"}})
    configure_gemini(app.config['GOOGLE_API_KEY'])
    os.makedirs(app.config['CV_FOLDER'], exist_ok=True)
    app.register_blueprint(career_bp)
    app.register_blueprint(cv_bp)
    app.register_blueprint(interview_bp)

    @app.route('/health', methods=['GET'])
    def health_check():
        try:
            cv_files_count = len([f for f in os.listdir(app.config['CV_FOLDER']) if f.endswith('.pdf')])
        except Exception as e:
            app.logger.error(f"Error accessing CV_FOLDER for health check: {e}")
            cv_files_count = "Error: Could not read folder"
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "cv_files_count": cv_files_count,
            "message": "Application is running and responsive."
        })
    start_cleanup_scheduler(app)
    return app

# --- MODIFIED PART STARTS HERE ---
# Create the Flask application instance globally
app = create_app()

# Entry point for running the Flask application locally (optional for Heroku)
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
# --- MODIFIED PART ENDS HERE ---
