"""
Database initialization script.

This script creates the necessary tables in the PostgreSQL database.
It should be run when the application is first set up or when the database schema changes.
"""

import os
import logging
import psycopg2
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_db_connection():
    """Create and return a connection to the PostgreSQL database."""
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'db'),
        database=os.getenv('DB_NAME', 'experiment_db'),
        user=os.getenv('DB_USER', 'user'),
        password=os.getenv('DB_PASSWORD', 'password')
    )
    conn.autocommit = True
    return conn

def init_db():
    """Initialize the database with the required tables."""
    logger.info("Initializing database...")
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Create users table for admin access
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    email VARCHAR(100),
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create experiments table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS experiments (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    description TEXT,
                    parameters JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER REFERENCES users(id),
                    active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Create participant_keys table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS participant_keys (
                    id SERIAL PRIMARY KEY,
                    experiment_id INTEGER REFERENCES experiments(id) ON DELETE CASCADE,
                    key_value VARCHAR(50) UNIQUE NOT NULL,
                    status VARCHAR(20) DEFAULT 'unused',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER REFERENCES users(id),
                    used_at TIMESTAMP,
                    revoked_at TIMESTAMP,
                    revoked_by INTEGER REFERENCES users(id)
                )
            ''')
            
            # Create participants table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS participants (
                    id SERIAL PRIMARY KEY,
                    key_id INTEGER REFERENCES participant_keys(id),
                    experiment_id INTEGER REFERENCES experiments(id),
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')
            
            # Create experiment_sessions table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS experiment_sessions (
                    id SERIAL PRIMARY KEY,
                    participant_id INTEGER REFERENCES participants(id),
                    experiment_id INTEGER REFERENCES experiments(id),
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    data JSONB
                )
            ''')
            
            # Create experiment_results table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS experiment_results (
                    id SERIAL PRIMARY KEY,
                    session_id INTEGER REFERENCES experiment_sessions(id),
                    participant_id INTEGER REFERENCES participants(id),
                    experiment_id INTEGER REFERENCES experiments(id),
                    result_data JSONB,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    # Run database initialization if this script is executed directly
    init_db()
    logger.info("Database initialization complete")