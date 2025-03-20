"""
Pytest configuration and fixtures for the Modular Experiment Platform tests.

This module contains shared fixtures that can be used across different test modules.
"""

import os
import pytest
from app.app import create_app
import tempfile
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Create a temporary file to use as a database
    db_fd, db_path = tempfile.mkstemp()
    
    # Configuration for testing
    test_config = {
        'TESTING': True,
        'SECRET_KEY': 'test-key',
        'DATABASE_HOST': 'localhost',
        'DATABASE_NAME': 'test_experiment_db',
        'DATABASE_USER': 'test_user',
        'DATABASE_PASSWORD': 'test_password',
    }
    
    # Create app with test config
    app = create_app(test_config)
    
    # Establish an application context
    with app.app_context():
        pass  # We'll add database initialization here later
        
    yield app
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A CLI test runner for the app."""
    return app.test_cli_runner()


@pytest.fixture
def auth_key():
    """Generate a test authentication key."""
    return "test-auth-key-12345"


# Additional fixtures can be added here as needed
# For example, fixtures for test database, experiment sessions, etc. 