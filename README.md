# LaHaus AI Concierge

An AI-powered WhatsApp concierge service for LaHaus real estate, combining natural language processing with a semantic property search engine.

## Project Overview

This project creates an intelligent assistant that helps potential home buyers find properties through WhatsApp. The system allows users to describe their property preferences conversationally, then uses AI to match them with relevant listings from LaHaus's inventory.

## Key Features

- WhatsApp integration via Twilio
- Conversational AI agent powered by OpenAI's GPT-4o
- Natural language property search with semantic understanding
- Context-aware conversation management
- Personalized property recommendations

## Technical Components

1. **WhatsApp Integration**: Uses Twilio's API to handle WhatsApp messages
2. **AI Conversation Agent**: Powered by OpenAI and LangChain
3. **Semantic Property Search**: Matches natural language queries to properties
4. **Response Templates**: WhatsApp-friendly formatting for property information

## Getting Started

### Prerequisites

- Python 3.9+
- Twilio account with WhatsApp integration
- OpenAI API key

### Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and add your API keys:
   ```
   cp .env.example .env
   ```
5. Start the development server:
   ```
   python -m app.app
   ```

### Development

The project is structured into modular components:

- `app.py`: Main Flask application with webhook endpoints
- `agent.py`: LangChain agent configuration
- `search.py`: Property search functionality
- `templates.py`: WhatsApp message templates
- `utils.py`: Helper functions
- `config.py`: Configuration variables

## Deployment

For production deployment:

1. Set up a proper WSGI server (e.g., Gunicorn)
2. Configure Twilio to point to your deployment URL
3. Set environment variables for API keys and configuration

## Future Enhancements

- Vector database integration for improved semantic search
- User preference tracking
- Integration with LaHaus booking system
- Analytics and conversation effectiveness monitoring