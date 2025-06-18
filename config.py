# config.py
import os

class AppConfig:
    """
    Configuration class for the Flask application.

    This class centralizes all application settings, making them
    easily manageable and accessible across modules. Environment
    variables are preferred for sensitive information.
    """
    # Google Gemini API Key. Loaded from environment variables for security.
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

    # Folder to store generated CVs temporarily.
    CV_FOLDER = 'temp_cvs'

    # Maximum age for CV files in hours before they are considered for cleanup.
    MAX_CV_AGE_HOURS = 24

    # Interval in seconds for the cleanup task to run. (e.g., 3600 seconds = 1 hour)
    CLEANUP_INTERVAL = 3600

    # Maximum number of CV files to keep in the temporary folder.
    # Oldest files are removed first if this limit is exceeded.
    MAX_CVS_STORED = 100

    # Default application name for PDF headers, etc.
    APP_NAME = os.getenv('APP_NAME', 'Professional CV Generator')
