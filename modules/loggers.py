import logging
import os
from datetime import datetime

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # File handler for debug.log
        logging.FileHandler(
            f'logs/debug_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        # Stream handler for console output
        logging.StreamHandler()
    ])

# Create logger
logger = logging.getLogger('crag_leader')
