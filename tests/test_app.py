"""
Tests for the main Flask application.

This module contains tests for app routes, configuration, and integration.
"""

import pytest
from app.app import create_app


def test_config():
    """Test configuration loading."""
    # Test that default configuration is loaded
    app = create_app()
    assert app.config['SECRET_KEY'] is not None
    
    # Test that test configuration is loaded
    test_config = {
        'TESTING': True,
        'SECRET_KEY': 'test-key',
    }
    app = create_app(test_config)
    assert app.config['TESTING'] is True
    assert app.config['SECRET_KEY'] == 'test-key'


def test_home_page(client):
    """Test that the home page loads."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Experiment Platform' in response.data


def test_validate_key_form(client):
    """Test the key validation form submission."""
    # Test with no key (should return to home with error)
    response = client.post('/validate_key', data={})
    assert response.status_code == 302  # redirect
    
    # Follow redirect and check for error message
    response = client.post('/validate_key', data={}, follow_redirects=True)
    assert response.status_code == 200
    assert b'Please enter a key' in response.data
    
    # Test with invalid key (would need to mock database connection for full test)
    response = client.post('/validate_key', data={'key': 'invalid-key'}, follow_redirects=True)
    assert response.status_code == 200
    # The exact error message depends on validation logic and might need mocking


def test_experiment_start_unauthorized(client):
    """Test that experiment start requires authentication."""
    # Try to access experiment start without being logged in
    response = client.get('/experiment/start/prisoners_dilemma', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please enter a valid experiment key' in response.data


def test_error_handlers(client):
    """Test error handlers."""
    # Test 404 handler
    response = client.get('/nonexistent_page')
    assert response.status_code == 404
    assert b'Page not found' in response.data


def test_admin_routes_require_login(client):
    """Test that admin routes require authentication."""
    # Try to access admin dashboard without being logged in
    response = client.get('/admin/dashboard', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in' in response.data or b'Login' in response.data
    
    # Try to access new experiment page without being logged in
    response = client.get('/admin/new_experiment', follow_redirects=True)
    assert response.status_code == 200
    assert b'Please log in' in response.data or b'Login' in response.data 