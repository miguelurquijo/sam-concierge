from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from loguru import logger
import os

from .agent import create_agent, run_agent
from .utils import format_whatsapp_message
from .config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN

app = Flask(__name__)

# Dictionary to store conversation histories per user
conversation_contexts = {}

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for receiving WhatsApp messages via Twilio"""
    # Get incoming message details
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From', '')
    
    logger.info(f"Received message from {sender}: {incoming_msg}")
    
    # Get or create conversation context for this user
    if sender not in conversation_contexts:
        conversation_contexts[sender] = []
    
    # Append user message to context
    conversation_contexts[sender].append({"role": "user", "content": incoming_msg})
    
    # Process with AI agent
    try:
        agent = create_agent(conversation_contexts[sender])
        response = run_agent(agent, incoming_msg)
        
        # Add assistant response to context
        conversation_contexts[sender].append({"role": "assistant", "content": response})
        
        # Format response for WhatsApp
        formatted_response = format_whatsapp_message(response)
        
        # Create Twilio response
        twilio_resp = MessagingResponse()
        twilio_resp.message(formatted_response)
        
        logger.info(f"Sent response to {sender}: {response}")
        return str(twilio_resp)
    
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        # Return a friendly error message
        twilio_resp = MessagingResponse()
        twilio_resp.message("I'm having trouble understanding right now. Could you try again later?")
        return str(twilio_resp)

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(debug=True)
