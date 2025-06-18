# utils/cleanup_utils.py
import os
import shutil
from datetime import datetime
from threading import Timer

def cleanup_cv_files(app):
    """
    Cleans up old or excessive CV files from the temporary storage directory.

    This function is designed to run periodically as a background task.
    It removes files older than a configured age and ensures the total
    number of stored CVs does not exceed a defined maximum.

    Args:
        app: The Flask application instance, used to access app.config and app.logger.
    """
    with app.app_context(): # Essential for accessing app.config within a background thread
        try:
            now = datetime.now()
            cv_files = []

            # Collect all PDF files in the CV_FOLDER along with their creation times.
            for filename in os.listdir(app.config['CV_FOLDER']):
                if filename.endswith('.pdf'):
                    filepath = os.path.join(app.config['CV_FOLDER'], filename)
                    # Use os.path.getctime for creation time (or getmtime for modification time)
                    # Creation time is often more suitable for cleanup policies.
                    created_time = datetime.fromtimestamp(os.path.getctime(filepath))
                    age_hours = (now - created_time).total_seconds() / 3600
                    cv_files.append((filepath, created_time, age_hours))

            # Sort files by creation time (oldest first) to prioritize deletion of older files.
            cv_files.sort(key=lambda x: x[1])

            deleted_count = 0
            # Iterate and delete files that are too old or if the storage limit is exceeded.
            for filepath, _, age_hours in cv_files:
                if (age_hours > app.config['MAX_CV_AGE_HOURS'] or
                    len(cv_files) - deleted_count > app.config['MAX_CVS_STORED']):
                    try:
                        os.remove(filepath)
                        deleted_count += 1
                        app.logger.info(f"Deleted old/excess CV file: {filepath}")
                    except OSError as e:
                        # Log specific OS errors during deletion (e.g., file in use, permissions).
                        app.logger.error(f"Error deleting file {filepath}: {str(e)}")
                    except Exception as e:
                        # Catch any other unexpected errors during file deletion.
                        app.logger.error(f"An unexpected error occurred deleting {filepath}: {str(e)}")

            app.logger.info(f"CV cleanup complete. Deleted {deleted_count} files.")

        except Exception as e:
            # Log any high-level errors that prevent the cleanup process from running.
            app.logger.error(f"Error during CV cleanup process: {str(e)}", exc_info=True)

        finally:
            # Schedule the next cleanup run. This ensures the cleanup runs continuously.
            # The timer is re-scheduled *after* the current run completes (or fails).
            Timer(app.config['CLEANUP_INTERVAL'], cleanup_cv_files, args=[app]).start()

def start_cleanup_scheduler(app):
    """
    Initializes and starts the periodic CV file cleanup scheduler.

    This function should be called once during application startup.
    """
    # Start the first cleanup task immediately or after a short delay.
    # We pass the app context to the cleanup function to ensure it can access app.config.
    Timer(app.config['CLEANUP_INTERVAL'], cleanup_cv_files, args=[app]).start()
    app.logger.info(f"CV cleanup scheduler started. Runs every {app.config['CLEANUP_INTERVAL']} seconds.")

