"""
Create Admin Script

This script creates the initial admin user for the Experiment Platform.
Run this script after setting up the database.
"""

import os
import logging
import argparse
from datetime import datetime
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_db_connection():
    """Create and return a connection to the PostgreSQL database."""
    import psycopg2
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'db'),
        database=os.getenv('DB_NAME', 'experiment_db'),
        user=os.getenv('DB_USER', 'user'),
        password=os.getenv('DB_PASSWORD', 'password')
    )
    conn.autocommit = True
    return conn

def create_admin_user(username, password, email=None):
    """
    Create an admin user.
    
    Args:
        username (str): Admin username
        password (str): Admin password
        email (str, optional): Admin email
    """
    logger.info(f"Creating admin user '{username}'...")
    
    # Hash the password
    password_hash = generate_password_hash(password)
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Check if user already exists
            cur.execute('SELECT 1 FROM users WHERE username = %s', (username,))
            if cur.fetchone():
                logger.info(f"User '{username}' already exists.")
                return
            
            # Create the user with admin role
            cur.execute(
                'INSERT INTO users (username, password_hash, email, role, created_at) '
                'VALUES (%s, %s, %s, %s, %s)',
                (username, password_hash, email, 'admin', datetime.now())
            )
            
            logger.info(f"Admin user '{username}' created successfully.")
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Create an admin user for the Experiment Platform.')
    parser.add_argument('username', help='Admin username')
    parser.add_argument('password', help='Admin password')
    parser.add_argument('--email', help='Admin email (optional)')
    
    args = parser.parse_args()
    
    # Ensure database tables exist
    from db.init_db import init_db
    init_db()
    
    # Create the admin user
    create_admin_user(args.username, args.password, args.email)