import os
import time
from loguru import logger
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the log file path from environment variables
LOG_FILE_PATH = os.getenv('LOG_PATH')

def log_updated_within_15_minutes(filepath):
    if os.path.isfile(filepath):
        file_mtime = os.path.getmtime(filepath)
        last_modified_time = datetime.fromtimestamp(file_mtime)
        fifteen_minutes_ago = datetime.now() - timedelta(minutes=15)
        return last_modified_time > fifteen_minutes_ago
    else:
        logger.error(f"The log file '{filepath}' does not exist.")
        return False

while True:
    if log_updated_within_15_minutes(LOG_FILE_PATH):
        logger.info("Log file has been updated in the last 15 minutes.")
    else:
        logger.warning("Log file has NOT been updated in the last 15 minutes.")
    time.sleep(60)
