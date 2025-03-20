"""
Tests for the Prisoner's Dilemma experiment module.

This module contains tests for the game logic, session management, and result calculation.
"""

import pytest
import json
from flask import session
from app.experiments.prisoners_dilemma import calculate_payoff, process_decision

def test_calculate_payoff():
    """Test the payoff calculation for different decision combinations."""
    # Define a test payoff matrix
    payoff_matrix = {
        "cooperate,cooperate": [3, 3],
        "cooperate,defect": [0, 5],
        "defect,cooperate": [5, 0],
        "defect,defect": [1, 1]
    }
    
    # Test all possible combinations
    assert calculate_payoff("cooperate", "cooperate", payoff_matrix) == (3, 3)
    assert calculate_payoff("cooperate", "defect", payoff_matrix) == (0, 5)
    assert calculate_payoff("defect", "cooperate", payoff_matrix) == (5, 0)
    assert calculate_payoff("defect", "defect", payoff_matrix) == (1, 1)

def test_process_decision(app, client, monkeypatch):
    """Test processing a player's decision."""
    # Mock database connection
    class MockDB:
        def __init__(self):
            self.executed_queries = []
            self.data = {}
        
        def execute(self, query, params=None):
            self.executed_queries.append((query, params))
            return self
        
        def fetchone(self):
            return None
        
        def commit(self):
            pass
        
        def close(self):
            pass
    
    mock_db = MockDB()
    
    # Mock the get_db_connection function
    def mock_get_db_connection():
        return mock_db
    
    # Patch the database connection
    monkeypatch.setattr('app.experiments.prisoners_dilemma.get_db_connection', mock_get_db_connection)
    
    # Set up a test session with experiment parameters
    with app.test_request_context():
        # Initialize session data
        session['participant_id'] = 1
        session['experiment_id'] = 2
        session['round'] = 1
        session['experiment_data'] = {
            'rounds': 3,
            'payoff_matrix': {
                "cooperate,cooperate": [3, 3],
                "cooperate,defect": [0, 5],
                "defect,cooperate": [5, 0],
                "defect,defect": [1, 1]
            },
            'opponent_strategy': 'tit_for_tat',
            'opponent_initial': 'cooperate'
        }
        
        # Test processing a cooperate decision
        result = process_decision('cooperate')
        
        # Check that the decision was processed correctly
        assert result['player_decision'] == 'cooperate'
        assert result['opponent_decision'] == 'cooperate'  # tit_for_tat starting with cooperate
        assert result['player_score'] == 3
        assert result['opponent_score'] == 3
        
        # Update session for next round
        session['round'] = 2
        session['previous_opponent_decision'] = 'cooperate'
        
        # Test processing a defect decision
        result = process_decision('defect')
        
        # Check that the decision was processed correctly 
        assert result['player_decision'] == 'defect'
        assert result['opponent_decision'] == 'cooperate'  # tit_for_tat follows previous round
        assert result['player_score'] == 5
        assert result['opponent_score'] == 0
        
        # Check that the database was updated with the decisions
        insert_query = "INSERT INTO participant_decisions (participant_id, experiment_id, round_number, decision, metadata) VALUES (%s, %s, %s, %s, %s)"
        assert any(q[0] == insert_query for q in mock_db.executed_queries)

def test_experiment_completion(app, client, monkeypatch):
    """Test completing an experiment session."""
    # Mock database connection
    class MockDB:
        def __init__(self):
            self.executed_queries = []
            self.data = {}
        
        def execute(self, query, params=None):
            self.executed_queries.append((query, params))
            return self
        
        def fetchone(self):
            return None
        
        def commit(self):
            pass
        
        def close(self):
            pass
    
    mock_db = MockDB()
    
    # Mock the get_db_connection function
    def mock_get_db_connection():
        return mock_db
    
    # Patch the database connection
    monkeypatch.setattr('app.experiments.prisoners_dilemma.get_db_connection', mock_get_db_connection)
    
    # Set up a test session with experiment parameters
    with app.test_request_context():
        # Initialize session data
        session['participant_id'] = 1
        session['experiment_id'] = 2
        session['round'] = 3  # Last round
        session['total_rounds'] = 3
        session['experiment_data'] = {
            'rounds': 3,
            'payoff_matrix': {
                "cooperate,cooperate": [3, 3],
                "cooperate,defect": [0, 5],
                "defect,cooperate": [5, 0],
                "defect,defect": [1, 1]
            },
            'opponent_strategy': 'tit_for_tat',
            'opponent_initial': 'cooperate',
            'rounds_data': [
                {'round': 1, 'player_decision': 'cooperate', 'opponent_decision': 'cooperate', 'player_score': 3, 'opponent_score': 3},
                {'round': 2, 'player_decision': 'defect', 'opponent_decision': 'cooperate', 'player_score': 5, 'opponent_score': 0}
            ]
        }
        session['previous_opponent_decision'] = 'cooperate'
        
        # Process the final decision
        result = process_decision('cooperate')
        
        # Check the result
        assert result['player_decision'] == 'cooperate'
        assert result['opponent_decision'] == 'defect'  # tit_for_tat responds to player's previous defect
        assert result['player_score'] == 0
        assert result['opponent_score'] == 5
        
        # Check if round data was updated
        assert len(session['experiment_data']['rounds_data']) == 3
        
        # Check that the experiment_results table was updated
        update_query = "INSERT INTO experiment_results (participant_id, experiment_id, result_data) VALUES (%s, %s, %s)"
        assert any(q[0] == update_query for q in mock_db.executed_queries)
        
        # Check that the experiment is marked as completed
        update_participant_query = "UPDATE participants SET completed_at = %s WHERE id = %s"
        assert any(q[0] == update_participant_query for q in mock_db.executed_queries) 