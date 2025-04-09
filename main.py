from app.app import app
from app.config import init_config, PORT
import os

if __name__ == "__main__":
    # Initialize configuration
    init_config()
    
    # Run the Flask application
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=os.getenv("DEBUG_MODE", "False").lower() == "true"
    )