import sys
import logging
import os
from datetime import datetime

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure logging to write to stdout
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # This will go to Heroku logs
)

# Create logger
logger = logging.getLogger('crag_leader')


# Optional: Add filter to exclude logs from showing in the terminal
class ExcludeConsoleFilter(logging.Filter):

    def filter(self, record):
        return False


# Add filter to console output but allow Heroku to capture it
console_handler = logging.StreamHandler(sys.stdout)
console_handler.addFilter(ExcludeConsoleFilter())
logger.addHandler(console_handler)

# Prevent the logger from propagating to the root logger
# This ensures logs don't show up in the console
logger.propagate = False
