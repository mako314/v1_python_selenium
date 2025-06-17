import logging
import os

LOG_FILE = 'google_search.log'

def clear_log_file(log_path=None):
    """
    Clear the log file contents without deleting it.
    """
    path = log_path or LOG_FILE
    if os.path.exists(path):
        with open(path, 'w', encoding='utf-8'):
            pass  # Truncates the file
        
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    handler = logging.FileHandler('google_search.log', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

