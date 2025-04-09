import json
import os
from datetime import datetime
from loguru import logger

def load_json_data(filepath):
    """Load data from a JSON file
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        Parsed JSON data or None if file doesn't exist or is invalid
    """
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning(f"File not found: {filepath}")
            return None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {filepath}")
        return None
    except Exception as e:
        logger.error(f"Error loading JSON file {filepath}: {str(e)}")
        return None

def save_json_data(data, filepath):
    """Save data to a JSON file
    
    Args:
        data: The data to save
        filepath: Path where to save the JSON file
        
    Returns:
        Boolean indicating success or failure
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON file {filepath}: {str(e)}")
        return False

def format_whatsapp_message(message):
    """Format a message for WhatsApp, handling any special formatting needs
    
    Args:
        message: The message to format
        
    Returns:
        WhatsApp-formatted message
    """
    # Currently just passes through, but we could add more formatting logic
    # like handling newlines, formatting text, etc.
    return message

def log_conversation(user_id, user_message, ai_response, log_dir='logs'):
    """Log conversation exchange to a file
    
    Args:
        user_id: Identifier for the user
        user_message: Message from the user
        ai_response: Response from the AI
        log_dir: Directory to store logs
    """
    try:
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Create filename based on date
        today = datetime.now().strftime('%Y-%m-%d')
        log_file = os.path.join(log_dir, f"conversation_{today}.log")
        
        # Format the log entry
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] User: {user_id}\n"
        log_entry += f"User: {user_message}\n"
        log_entry += f"AI: {ai_response}\n"
        log_entry += "-" * 50 + "\n"
        
        # Append to log file
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
            
    except Exception as e:
        logger.error(f"Error logging conversation: {str(e)}")
