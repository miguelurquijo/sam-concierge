import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')

# AI Model configuration
MODEL_NAME = os.getenv('MODEL_NAME', 'gpt-4o')
TEMPERATURE = float(os.getenv('TEMPERATURE', '0.5'))
MAX_TOKENS = int(os.getenv('MAX_TOKENS', '4096'))
FREQUENCY_PENALTY = float(os.getenv('FREQUENCY_PENALTY', '0.0'))
PRESENCE_PENALTY = float(os.getenv('PRESENCE_PENALTY', '0.0'))

# Application configuration
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
PORT = int(os.getenv('PORT', 5000))

# Paths
DATA_DIR = os.getenv('DATA_DIR', 'data')
LOG_DIR = os.getenv('LOG_DIR', 'logs')

# Default property search parameters
DEFAULT_SEARCH_LIMIT = int(os.getenv('DEFAULT_SEARCH_LIMIT', 5))
MAX_PROPERTIES_PER_RESPONSE = int(os.getenv('MAX_PROPERTIES_PER_RESPONSE', 3))

# Conversation parameters
MAX_CONVERSATION_HISTORY = int(os.getenv('MAX_CONVERSATION_HISTORY', 10))
SUMMARY_INTERVAL = int(os.getenv('SUMMARY_INTERVAL', 5))  # Summarize after this many messages

# Initialize configuration
def init_config():
    """Validate configuration and set up necessary directories"""
    required_vars = [
        'OPENAI_API_KEY',
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN'
    ]
    
    missing_vars = [var for var in required_vars if not globals().get(var)]
    
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            f"Please set these in a .env file or in your environment."
        )
    
    # Create necessary directories
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
