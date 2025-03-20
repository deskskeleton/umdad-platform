"""
Main application module for the Modular Experiment Platform.

This file defines the Flask application factory and sets up the core functionality
including routes, authentication, and experiment module loading.
"""

import os
import logging
import psycopg2
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection function
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

def create_app(test_config=None):
    """Create and configure the Flask application using the factory pattern."""
    app = Flask(__name__, instance_relative_config=True)
    
    # Load configuration
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
        DATABASE_HOST=os.getenv('DB_HOST', 'db'),
        DATABASE_NAME=os.getenv('DB_NAME', 'experiment_db'),
        DATABASE_USER=os.getenv('DB_USER', 'user'),
        DATABASE_PASSWORD=os.getenv('DB_PASSWORD', 'password'),
    )
    
    if test_config:
        # Load test configuration if passed
        app.config.update(test_config)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Register the admin blueprint
    from app.admin import register_admin_routes
    register_admin_routes(app)
    
    # Register experiment modules dynamically
    from app.experiments import get_available_experiments, register_experiment_routes
    available_experiments = get_available_experiments()
    register_experiment_routes(app)
    
    # Template context processor to add current year to all templates
    @app.context_processor
    def inject_current_year():
        """Add current year to all templates."""
        return {'current_year': datetime.now().year}
    
    # Home route
    @app.route('/')
    def home():
        """Landing page for the experiment platform."""
        return render_template('index.html')
    
    # Participant key validation route
    @app.route('/validate_key', methods=['POST'])
    def validate_key():
        """Validate a participant's experiment key."""
        key = request.form.get('key')
        if not key:
            flash('Please enter a key', 'error')
            return redirect(url_for('home'))
        
        # Import key validation function
        from app.auth import validate_key, mark_key_as_used
        
        # Validate the key
        key_data = validate_key(key)
        
        if not key_data:
            flash('Invalid key', 'error')
            return redirect(url_for('home'))
        
        if key_data['status'] != 'unused':
            flash('This key has already been used', 'error')
            return redirect(url_for('home'))
        
        # Mark key as used
        mark_key_as_used(key_data['id'])
        
        # Create participant record
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO participants (key_id, experiment_id, joined_at) VALUES (%s, %s, %s) RETURNING id',
                (key_data['id'], key_data['experiment_id'], datetime.now())
            )
            participant_id = cur.fetchone()[0]
            
            # Store in session
            session['participant_id'] = participant_id
            session['experiment_id'] = key_data['experiment_id']
            session['experiment_type'] = key_data['experiment_type']
            
            return redirect(url_for('experiment_start', exp_type=key_data['experiment_type']))
        except Exception as e:
            logger.error(f"Error creating participant record: {e}")
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('home'))
        finally:
            conn.close()
    
    # Experiment start route - redirects to the specific experiment module
    @app.route('/experiment/start/<exp_type>')
    def experiment_start(exp_type):
        """Starting point for an experiment, redirects to the specific module."""
        if 'participant_id' not in session:
            flash('Please enter a valid experiment key to begin', 'error')
            return redirect(url_for('home'))
        
        if exp_type not in available_experiments:
            return render_template('error.html', message='Experiment not found')
        
        # Redirect to the experiment's main route
        return redirect(url_for(f'{exp_type}.start'))
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        """Handle 404 errors."""
        return render_template('error.html', message='Page not found'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        """Handle 500 errors."""
        logger.error(f"Server error: {e}")
        return render_template('error.html', message='Server error. Please try again later.'), 500
    
    return app

# This is only used when running directly with python app/app.py
# For production, use the run.py script
if __name__ == '__main__':
    # Create database tables if they don't exist
    from app.db.init_db import init_db
    init_db()
    
    # Create and run the application
    app = create_app()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)