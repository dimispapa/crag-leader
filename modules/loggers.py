import sys
import logging
import os

# Only enable debug logging if DEBUG environment variable is set to true
DEBUG_MODE = os.environ.get('DEBUG').lower() == 'true'

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout if DEBUG_MODE else open(os.devnull, 'w'))

# Set higher log levels for third-party libraries
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('google').setLevel(logging.WARNING)

# Create logger
logger = logging.getLogger('crag_leader')


# Optional: Add filter to exclude logs from showing in the terminal
class ExcludeConsoleFilter(logging.Filter):

    def filter(self, record):
        return False


# Add filter to console output but allow Heroku to capture it
console_handler = logging.StreamHandler(sys.stdout)
# console_handler.addFilter(ExcludeConsoleFilter())
logger.addHandler(console_handler)

# Prevent the logger from propagating to the root logger
# This ensures logs don't show up in the console
# logger.propagate = False
