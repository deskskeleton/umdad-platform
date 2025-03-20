#!/usr/bin/env python3
"""
Run script for the Experiment Platform application.

This script initializes and runs the Flask application with the configuration
specified in environment variables or .env file.
"""

import os
import logging
from dotenv import load_dotenv
from app.app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get configuration from environment variables
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    host = os.getenv("HOST", "0.0.0.0")
    
    # Create and run the application
    app = create_app()
    
    logger.info(f"Starting Experiment Platform on {host}:{port} (Debug: {debug})")
    app.run(host=host, port=port, debug=debug)