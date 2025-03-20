"""
Key Manager for Experiment Platform

This module handles the generation, validation, and management of experiment keys.
Keys are used to authenticate participants for specific experiments.
"""

import os
import logging
import secrets
import hashlib
import psycopg2
from datetime import datetime

# Set up logger
logger = logging.getLogger(__name__)

def generate_key(length=16):
    """
    Generate a cryptographically secure random key.
    
    Args:
        length (int): Length of the key in bytes (default: 16)
        
    Returns:
        str: A random hexadecimal string
    """
    return secrets.token_hex(length)

def create_keys_for_experiment(experiment_id, count, conn=None):
    """
    Generate and store multiple keys for an experiment.
    
    Args:
        experiment_id (int): ID of the experiment
        count (int): Number of keys to generate
        conn (psycopg2.connection, optional): Database connection
        
    Returns:
        list: List of generated keys
    """
    generated_keys = []
    close_conn = False
    
    if conn is None:
        from app import get_db_connection
        conn = get_db_connection()
        close_conn = True
    
    try:
        cur = conn.cursor()
        
        # Generate and store each key
        for _ in range(count):
            key = generate_key()
            
            # Check if key already exists (extremely unlikely but good practice)
            cur.execute('SELECT 1 FROM participant_keys WHERE key_value = %s', (key,))
            if cur.fetchone():
                # In the highly unlikely event of a collision, try again
                continue
                
            # Store the key in the database
            cur.execute(
                'INSERT INTO participant_keys (experiment_id, key_value, created_at) '
                'VALUES (%s, %s, %s)',
                (experiment_id, key, datetime.now())
            )
            
            generated_keys.append(key)
        
        conn.commit()
        logger.info(f"Generated {len(generated_keys)} keys for experiment {experiment_id}")
        
        return generated_keys
        
    except Exception as e:
        logger.error(f"Error generating keys: {e}")
        conn.rollback()
        raise
    finally:
        if close_conn:
            conn.close()

def validate_key(key, conn=None):
    """
    Validate if a key exists and is unused.
    
    Args:
        key (str): The key to validate
        conn (psycopg2.connection, optional): Database connection
        
    Returns:
        tuple: (valid, experiment_id, key_id) tuple or (False, None, None) if invalid
    """
    close_conn = False
    
    if conn is None:
        from app import get_db_connection
        conn = get_db_connection()
        close_conn = True
    
    try:
        cur = conn.cursor()
        
        # Check if key exists and is unused
        cur.execute(
            'SELECT id, experiment_id, status FROM participant_keys WHERE key_value = %s',
            (key,)
        )
        result = cur.fetchone()
        
        if not result:
            logger.warning(f"Invalid key attempted: {key}")
            return (False, None, None)
        
        key_id, experiment_id, status = result
        
        if status != 'unused':
            logger.warning(f"Used key attempted: {key}")
            return (False, None, None)
        
        # Key is valid and unused
        return (True, experiment_id, key_id)
        
    except Exception as e:
        logger.error(f"Error validating key: {e}")
        return (False, None, None)
    finally:
        if close_conn:
            conn.close()

def mark_key_as_used(key_id, conn=None):
    """
    Mark a key as used after successful validation.
    
    Args:
        key_id (int): ID of the key
        conn (psycopg2.connection, optional): Database connection
        
    Returns:
        bool: True if successful, False otherwise
    """
    close_conn = False
    
    if conn is None:
        from app import get_db_connection
        conn = get_db_connection()
        close_conn = True
    
    try:
        cur = conn.cursor()
        
        # Update key status to used
        cur.execute(
            'UPDATE participant_keys SET status = %s, used_at = %s WHERE id = %s',
            ('used', datetime.now(), key_id)
        )
        
        if cur.rowcount == 0:
            logger.error(f"Key ID {key_id} not found when marking as used")
            return False
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Error marking key as used: {e}")
        conn.rollback()
        return False
    finally:
        if close_conn:
            conn.close()

def revoke_key(key, conn=None):
    """
    Revoke a key to prevent its use.
    
    Args:
        key (str): The key to revoke
        conn (psycopg2.connection, optional): Database connection
        
    Returns:
        bool: True if successful, False otherwise
    """
    close_conn = False
    
    if conn is None:
        from app import get_db_connection
        conn = get_db_connection()
        close_conn = True
    
    try:
        cur = conn.cursor()
        
        # Update key status to revoked
        cur.execute(
            'UPDATE participant_keys SET status = %s WHERE key_value = %s',
            ('revoked', key)
        )
        
        if cur.rowcount == 0:
            logger.error(f"Key not found when revoking: {key}")
            return False
        
        conn.commit()
        logger.info(f"Key revoked: {key}")
        return True
        
    except Exception as e:
        logger.error(f"Error revoking key: {e}")
        conn.rollback()
        return False
    finally:
        if close_conn:
            conn.close()

def get_keys_for_experiment(experiment_id, conn=None):
    """
    Get all keys for a specific experiment.
    
    Args:
        experiment_id (int): ID of the experiment
        conn (psycopg2.connection, optional): Database connection
        
    Returns:
        list: List of key dictionaries with id, value, status, and timestamps
    """
    close_conn = False
    
    if conn is None:
        from app import get_db_connection
        conn = get_db_connection()
        close_conn = True
    
    try:
        cur = conn.cursor()
        
        cur.execute(
            'SELECT id, key_value, status, created_at, used_at FROM participant_keys '
            'WHERE experiment_id = %s',
            (experiment_id,)
        )
        
        keys = []
        for row in cur.fetchall():
            keys.append({
                'id': row[0],
                'key': row[1],
                'status': row[2],
                'created_at': row[3],
                'used_at': row[4]
            })
        
        return keys
        
    except Exception as e:
        logger.error(f"Error retrieving keys for experiment {experiment_id}: {e}")
        return []
    finally:
        if close_conn:
            conn.close()