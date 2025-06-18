# app.py
from flask import Flask, jsonify # Import jsonify for JSON responses
from flask_cors import CORS
import os
from dotenv import load_dotenv
from datetime import datetime # Import datetime for timestamps

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

    This function initializes the Flask app, applies configurations,
    enables CORS, configures external APIs, and registers blueprints.
    """
    app = Flask(__name__)

    # Load configuration from the AppConfig object
    app.config.from_object(AppConfig)

    # Enable CORS for all origins. In a production environment,
    # it's recommended to restrict this to known frontend origins.
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Configure the Gemini API with the API key from environment variables.
    configure_gemini(app.config['GOOGLE_API_KEY'])

    # Ensure the temporary CVs directory exists.
    # This is critical for file storage operations.
    os.makedirs(app.config['CV_FOLDER'], exist_ok=True)

    # Register blueprints to organize routes into modular components.
    app.register_blueprint(career_bp)
    app.register_blueprint(cv_bp)
    app.register_blueprint(interview_bp)

    # Define a simple health check endpoint.
    # This is crucial for monitoring in production environments.
    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Health check endpoint for monitoring application status.
        Returns a JSON response indicating the app's health and relevant metrics.
        """
        try:
            # Attempt to count PDF files in the CV folder as an indicator of file system access.
            cv_files_count = len([f for f in os.listdir(app.config['CV_FOLDER']) if f.endswith('.pdf')])
        except Exception as e:
            # If counting files fails, log the error and report it in the health check.
            app.logger.error(f"Error accessing CV_FOLDER for health check: {e}")
            cv_files_count = "Error: Could not read folder"

        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "cv_files_count": cv_files_count,
            "message": "Application is running and responsive."
        })

    # Start the background task for cleaning up old CV files.
    # This runs on a separate thread to avoid blocking the main application.
    start_cleanup_scheduler(app)

    return app

# Entry point for running the Flask application
if __name__ == '__main__':
    app = create_app()
    # In a production deployment, use a production-ready WSGI server
    # like Gunicorn or uWSGI instead of app.run().
    app.run(debug=True, port=5000)
