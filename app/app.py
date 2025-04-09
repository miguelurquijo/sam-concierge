from flask import Flask, request, jsonify, render_template
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from loguru import logger
import os
import json
import time
import uuid

from .agent import create_agent, run_agent, analyze_conversation
from .utils import format_whatsapp_message, log_conversation
from .config import (
    TWILIO_ACCOUNT_SID, 
    TWILIO_AUTH_TOKEN, 
    DEBUG_MODE, 
    PORT, 
    MAX_CONVERSATION_HISTORY
)

# Initialize Flask app
app = Flask(__name__)

# Dictionary to store conversation contexts per user
conversation_contexts = {}

# Dictionary to store agent instances per user
agent_instances = {}

# Dictionary to store metrics
conversation_metrics = {}

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for receiving WhatsApp messages via Twilio"""
    # Get incoming message details
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    media_url = request.values.get('MediaUrl0', None)
    
    # Generate a unique message ID
    message_id = str(uuid.uuid4())
    timestamp = time.time()
    
    logger.info(f"Received message from {sender} [{message_id}]: {incoming_msg}")
    
    # Get or create conversation context for this user
    if sender not in conversation_contexts:
        conversation_contexts[sender] = []
        conversation_metrics[sender] = {
            "total_messages": 0,
            "total_tokens": 0,
            "session_start": timestamp,
            "last_activity": timestamp
        }
    else:
        conversation_metrics[sender]["last_activity"] = timestamp
    
    # Update metrics
    conversation_metrics[sender]["total_messages"] += 1
    
    # Handle media if present
    message_content = incoming_msg
    if media_url:
        message_content = f"{incoming_msg} [Media: {media_url}]"
    
    # Append user message to context
    user_message = {"role": "user", "content": message_content, "timestamp": timestamp, "id": message_id}
    conversation_contexts[sender].append(user_message)
    
    # Limit conversation history
    if len(conversation_contexts[sender]) > MAX_CONVERSATION_HISTORY * 2:  # *2 because we count pairs of messages
        conversation_contexts[sender] = conversation_contexts[sender][-MAX_CONVERSATION_HISTORY * 2:]
    
    # Process with AI agent
    try:
        # Get or create agent
        if sender not in agent_instances:
            agent_instances[sender] = create_agent(conversation_contexts[sender])
        
        # Process message
        start_time = time.time()
        response = run_agent(agent_instances[sender], message_content)
        processing_time = time.time() - start_time
        
        # Generate response ID
        response_id = str(uuid.uuid4())
        response_timestamp = time.time()
        
        # Add assistant response to context
        assistant_message = {
            "role": "assistant", 
            "content": response, 
            "timestamp": response_timestamp,
            "id": response_id,
            "processing_time": processing_time
        }
        conversation_contexts[sender].append(assistant_message)
        
        # Format response for WhatsApp
        formatted_response = format_whatsapp_message(response)
        
        # Create Twilio response
        twilio_resp = MessagingResponse()
        twilio_resp.message(formatted_response)
        
        # Log conversation for analysis
        log_conversation(
            user_id=sender,
            user_message=message_content,
            ai_response=response,
            processing_time=processing_time
        )
        
        logger.info(f"Sent response to {sender} [{response_id}] in {processing_time:.2f}s")
        return str(twilio_resp)
    
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        # Return a friendly error message
        twilio_resp = MessagingResponse()
        twilio_resp.message("Lo siento, estoy teniendo problemas técnicos en este momento. ¿Podrías intentarlo de nuevo en unos momentos?")
        return str(twilio_resp)

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "healthy",
        "active_conversations": len(conversation_contexts),
        "total_messages_processed": sum(m["total_messages"] for m in conversation_metrics.values())
    })

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Admin dashboard for monitoring the system"""
    if DEBUG_MODE:
        stats = {
            "active_conversations": len(conversation_contexts),
            "total_users": len(conversation_metrics),
            "total_messages": sum(m["total_messages"] for m in conversation_metrics.values()),
            "user_stats": []
        }
        
        for user_id, metrics in conversation_metrics.items():
            user_stats = {
                "user_id": user_id,
                "message_count": metrics["total_messages"],
                "conversation_length": len(conversation_contexts.get(user_id, [])),
                "last_activity": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(metrics["last_activity"]))
            }
            stats["user_stats"].append(user_stats)
        
        return render_template('dashboard.html', stats=stats)
    else:
        return jsonify({"error": "Dashboard only available in debug mode"})

@app.route('/reset/<user_id>', methods=['POST'])
def reset_conversation(user_id):
    """Reset a user's conversation context"""
    if DEBUG_MODE:
        if user_id in conversation_contexts:
            conversation_contexts[user_id] = []
            if user_id in agent_instances:
                del agent_instances[user_id]
            return jsonify({"status": "success", "message": f"Conversation reset for {user_id}"})
        else:
            return jsonify({"status": "error", "message": "User not found"})
    else:
        return jsonify({"error": "Reset only available in debug mode"})

@app.route('/analyze/<user_id>', methods=['GET'])
def analyze_user_conversation(user_id):
    """Analyze a user's conversation"""
    if DEBUG_MODE:
        if user_id in conversation_contexts:
            analysis = analyze_conversation(conversation_contexts[user_id])
            return jsonify(analysis)
        else:
            return jsonify({"status": "error", "message": "User not found"})
    else:
        return jsonify({"error": "Analysis only available in debug mode"})

def init_app():
    """Initialize the Flask application with required directories"""
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create a basic dashboard template if it doesn't exist
    dashboard_template = os.path.join('templates', 'dashboard.html')
    if not os.path.exists(dashboard_template):
        with open(dashboard_template, 'w') as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>LaHaus Concierge Dashboard</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    h1 { color: #4CAF50; }
                    .stats { margin-bottom: 20px; }
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #4CAF50; color: white; }
                    tr:nth-child(even) { background-color: #f2f2f2; }
                </style>
            </head>
            <body>
                <h1>LaHaus AI Concierge Dashboard</h1>
                <div class="stats">
                    <h2>System Stats</h2>
                    <p>Active Conversations: {{ stats.active_conversations }}</p>
                    <p>Total Users: {{ stats.total_users }}</p>
                    <p>Total Messages: {{ stats.total_messages }}</p>
                </div>
                <div class="users">
                    <h2>User Stats</h2>
                    <table>
                        <tr>
                            <th>User ID</th>
                            <th>Messages</th>
                            <th>Conversation Length</th>
                            <th>Last Activity</th>
                            <th>Actions</th>
                        </tr>
                        {% for user in stats.user_stats %}
                        <tr>
                            <td>{{ user.user_id }}</td>
                            <td>{{ user.message_count }}</td>
                            <td>{{ user.conversation_length }}</td>
                            <td>{{ user.last_activity }}</td>
                            <td>
                                <button onclick="resetConversation('{{ user.user_id }}')">Reset</button>
                                <button onclick="analyzeConversation('{{ user.user_id }}')">Analyze</button>
                            </td>
                        </tr>
                        {% endfor %}
                    </table>
                </div>
                <div id="analysis" style="display: none;">
                    <h2>Conversation Analysis</h2>
                    <pre id="analysis-content"></pre>
                </div>
                <script>
                    function resetConversation(userId) {
                        fetch('/reset/' + userId, { method: 'POST' })
                            .then(response => response.json())
                            .then(data => {
                                alert(data.message);
                                location.reload();
                            });
                    }
                    
                    function analyzeConversation(userId) {
                        fetch('/analyze/' + userId)
                            .then(response => response.json())
                            .then(data => {
                                document.getElementById('analysis').style.display = 'block';
                                document.getElementById('analysis-content').textContent = JSON.stringify(data, null, 2);
                            });
                    }
                </script>
            </body>
            </html>
            """)
    
    return app

if __name__ == '__main__':
    app = init_app()
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG_MODE)