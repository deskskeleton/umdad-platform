"""
Tests for the authentication module.

This module contains tests for key generation, validation, and management.
"""

import pytest
from app.auth import generate_key, validate_key, mark_key_as_used, revoke_key

# Mock database connection and cursor for testing
class MockCursor:
    def __init__(self):
        self.executed_queries = []
        self.fetchone_results = {}
        self.fetchall_results = {}
    
    def execute(self, query, params=None):
        self.executed_queries.append((query, params))
        return self
    
    def fetchone(self):
        query = self.executed_queries[-1][0]
        return self.fetchone_results.get(query)
    
    def fetchall(self):
        query = self.executed_queries[-1][0]
        return self.fetchall_results.get(query, [])

class MockConnection:
    def __init__(self):
        self.cursor_instance = MockCursor()
    
    def cursor(self):
        return self.cursor_instance
    
    def commit(self):
        pass
    
    def close(self):
        pass

# Tests for key generation
def test_generate_key_length():
    """Test that generated keys have the expected length."""
    key = generate_key()
    # Default key length should be 16 characters
    assert len(key) == 16

def test_generate_key_uniqueness():
    """Test that generated keys are unique."""
    keys = [generate_key() for _ in range(100)]
    # All generated keys should be unique
    assert len(keys) == len(set(keys))

# Tests for key validation
def test_validate_key_valid(monkeypatch):
    """Test validating a valid key."""
    # Mock the database connection
    mock_conn = MockConnection()
    mock_cursor = mock_conn.cursor_instance
    
    # Set up mock response for a valid key
    valid_key_query = "SELECT id, experiment_id, status FROM participant_keys WHERE key_value = %s"
    mock_cursor.fetchone_results[valid_key_query] = (1, 2, 'unused')
    
    # Mock the experiment type query
    experiment_query = "SELECT type FROM experiments WHERE id = %s"
    mock_cursor.fetchone_results[experiment_query] = ('prisoners_dilemma',)
    
    # Mock the get_db_connection function
    def mock_get_db_connection():
        return mock_conn
    
    monkeypatch.setattr('app.auth.key_manager.get_db_connection', mock_get_db_connection)
    
    # Test the validate_key function
    result = validate_key('valid-key-12345')
    
    # Assert that we got a valid result
    assert result is not None
    assert result['id'] == 1
    assert result['experiment_id'] == 2
    assert result['status'] == 'unused'
    assert result['experiment_type'] == 'prisoners_dilemma'

def test_validate_key_invalid(monkeypatch):
    """Test validating an invalid key."""
    # Mock the database connection
    mock_conn = MockConnection()
    mock_cursor = mock_conn.cursor_instance
    
    # Set up mock response for an invalid key (no result)
    mock_cursor.fetchone_results = {}
    
    # Mock the get_db_connection function
    def mock_get_db_connection():
        return mock_conn
    
    monkeypatch.setattr('app.auth.key_manager.get_db_connection', mock_get_db_connection)
    
    # Test the validate_key function
    result = validate_key('invalid-key')
    
    # Assert that we got None as the result
    assert result is None

# Tests for marking a key as used
def test_mark_key_as_used(monkeypatch):
    """Test marking a key as used."""
    # Mock the database connection
    mock_conn = MockConnection()
    mock_cursor = mock_conn.cursor_instance
    
    # Mock the get_db_connection function
    def mock_get_db_connection():
        return mock_conn
    
    monkeypatch.setattr('app.auth.key_manager.get_db_connection', mock_get_db_connection)
    
    # Test marking a key as used
    mark_key_as_used(1)
    
    # Check that the correct query was executed
    expected_query = "UPDATE participant_keys SET status = %s, used_at = %s WHERE id = %s"
    assert any(q[0] == expected_query for q in mock_cursor.executed_queries)

# Tests for revoking a key
def test_revoke_key(monkeypatch):
    """Test revoking a key."""
    # Mock the database connection
    mock_conn = MockConnection()
    mock_cursor = mock_conn.cursor_instance
    
    # Mock the get_db_connection function
    def mock_get_db_connection():
        return mock_conn
    
    monkeypatch.setattr('app.auth.key_manager.get_db_connection', mock_get_db_connection)
    
    # Test revoking a key
    revoke_key(1, 2)  # key_id, admin_id
    
    # Check that the correct query was executed
    expected_query = "UPDATE participant_keys SET status = %s, revoked_at = %s, revoked_by = %s WHERE id = %s"
    assert any(q[0] == expected_query for q in mock_cursor.executed_queries) 