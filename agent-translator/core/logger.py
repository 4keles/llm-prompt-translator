import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

# Initialize the global logger instance
logger = logging.getLogger("TranslatorLogger")
logger.setLevel(logging.DEBUG)

# Ensure the logs directory exists at the root of the project
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logs_dir = os.path.join(base_dir, "logs")
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir, exist_ok=True)

# Generate a filename based on the current date
current_date = datetime.now().strftime("%Y-%m-%d")
log_filename = os.path.join(logs_dir, f"translator_{current_date}.log")

# Setup a file handler that rotates daily
file_handler = TimedRotatingFileHandler(
    filename=log_filename, 
    when="midnight", 
    interval=1, 
    backupCount=30, # Keep logs for 30 days
    encoding="utf-8"
)

# Standard logging format
formatter = logging.Formatter(
    fmt="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG) # Write everything to file

# Prevent multiple handlers from being attached if initialized multiple times
if not logger.handlers:
    logger.addHandler(file_handler)

def get_logger():
    """Returns the globally configured logger instance."""
    return logger
