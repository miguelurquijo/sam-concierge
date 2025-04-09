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

def log_conversation(user_id, user_message, ai_response, processing_time=None, log_dir='logs'):
    """Log conversation exchange to a file and structured JSON.
    
    Args:
        user_id: Identifier for the user
        user_message: Message from the user
        ai_response: Response from the AI
        processing_time: Time taken to process the message (in seconds)
        log_dir: Directory to store logs
    """
    try:
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Generate timestamp
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        date_str = timestamp.strftime('%Y-%m-%d')
        
        # 1. Log to human-readable text file
        log_file = os.path.join(log_dir, f"conversation_{date_str}.log")
        log_entry = f"[{timestamp_str}] User: {user_id}\n"
        log_entry += f"User: {user_message}\n"
        log_entry += f"AI: {ai_response}\n"
        if processing_time:
            log_entry += f"Processing time: {processing_time:.2f}s\n"
        log_entry += "-" * 50 + "\n"
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        # 2. Log to structured JSON for analytics
        json_log_dir = os.path.join(log_dir, 'json')
        os.makedirs(json_log_dir, exist_ok=True)
        
        json_log_file = os.path.join(json_log_dir, f"conversation_{date_str}.jsonl")
        
        # Create structured log entry
        structured_entry = {
            "timestamp": timestamp_str,
            "user_id": user_id,
            "user_message": user_message,
            "ai_response": ai_response,
            "processing_time": processing_time,
            "message_length": {
                "user": len(user_message),
                "ai": len(ai_response)
            }
        }
        
        # Append to JSON Lines file
        with open(json_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(structured_entry, ensure_ascii=False) + '\n')
            
    except Exception as e:
        logger.error(f"Error logging conversation: {str(e)}")

def analyze_logs(log_dir='logs', days=1):
    """Analyze conversation logs for insights.
    
    Args:
        log_dir: Directory containing logs
        days: Number of days to analyze
        
    Returns:
        Dictionary with analysis results
    """
    try:
        json_log_dir = os.path.join(log_dir, 'json')
        if not os.path.exists(json_log_dir):
            return {"error": "No log data available"}
        
        # Get log files from the last N days
        now = datetime.now()
        log_files = []
        
        for i in range(days):
            date_str = (now - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
            log_file = os.path.join(json_log_dir, f"conversation_{date_str}.jsonl")
            if os.path.exists(log_file):
                log_files.append(log_file)
        
        if not log_files:
            return {"error": f"No log data available for the last {days} days"}
        
        # Analyze logs
        conversations = {}
        total_messages = 0
        total_processing_time = 0
        user_message_lengths = []
        ai_message_lengths = []
        
        for log_file in log_files:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        user_id = entry.get("user_id")
                        
                        # Track per-user stats
                        if user_id not in conversations:
                            conversations[user_id] = {
                                "message_count": 0,
                                "avg_response_time": 0
                            }
                        
                        conversations[user_id]["message_count"] += 1
                        
                        # Track processing time
                        if entry.get("processing_time"):
                            total_processing_time += entry["processing_time"]
                            
                            # Update average response time for this user
                            prev_count = conversations[user_id]["message_count"] - 1
                            prev_avg = conversations[user_id]["avg_response_time"]
                            new_avg = (prev_avg * prev_count + entry["processing_time"]) / conversations[user_id]["message_count"]
                            conversations[user_id]["avg_response_time"] = new_avg
                        
                        # Track message lengths
                        if "message_length" in entry:
                            if "user" in entry["message_length"]:
                                user_message_lengths.append(entry["message_length"]["user"])
                            if "ai" in entry["message_length"]:
                                ai_message_lengths.append(entry["message_length"]["ai"])
                        
                        total_messages += 1
                        
                    except json.JSONDecodeError:
                        continue
        
        # Calculate averages
        avg_user_message_length = sum(user_message_lengths) / len(user_message_lengths) if user_message_lengths else 0
        avg_ai_message_length = sum(ai_message_lengths) / len(ai_message_lengths) if ai_message_lengths else 0
        avg_processing_time = total_processing_time / total_messages if total_messages > 0 else 0
        
        # Return analysis results
        return {
            "total_users": len(conversations),
            "total_messages": total_messages,
            "avg_processing_time": avg_processing_time,
            "avg_user_message_length": avg_user_message_length,
            "avg_ai_message_length": avg_ai_message_length,
            "users": [
                {
                    "user_id": user_id,
                    "message_count": stats["message_count"],
                    "avg_response_time": stats["avg_response_time"]
                }
                for user_id, stats in conversations.items()
            ]
        }
        
    except Exception as e:
        logger.error(f"Error analyzing logs: {str(e)}")
        return {"error": f"Error analyzing logs: {str(e)}"}

def extract_emoji_from_text(text):
    """Extract emojis from text.
    
    Args:
        text: Text string to analyze
        
    Returns:
        List of emojis found in the text
    """
    import re
    # This pattern is a simplified version and may not catch all emojis
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F700-\U0001F77F"  # alchemical symbols
                               u"\U0001F780-\U0001F7FF"  # Geometric Shapes
                               u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
                               u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                               u"\U0001FA00-\U0001FA6F"  # Chess Symbols
                               u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
                               u"\U00002702-\U000027B0"  # Dingbats
                               u"\U000024C2-\U0001F251" 
                               "]+", flags=re.UNICODE)
    
    return emoji_pattern.findall(text)
