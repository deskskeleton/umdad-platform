"""
Admin Routes for Experiment Platform

This module provides the routes and functionality for the admin interface.
Administrators can create experiments, generate keys, and view results.
"""

import logging
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash

from auth.key_manager import create_keys_for_experiment, get_keys_for_experiment, revoke_key

# Set up logger
logger = logging.getLogger(__name__)

# Define blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Middleware to check for admin authentication
@admin_bp.before_request
def check_admin_auth():
    """Check if the user is authenticated as an admin."""
    # Skip auth check for login page
    if request.path == '/admin/login':
        return
    
    # Check if user is logged in as admin
    if 'admin_id' not in session:
        return redirect(url_for('admin.login'))

# Admin login page
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle admin login."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please provide both username and password', 'error')
            return render_template('admin/login.html')
        
        from app import get_db_connection
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute('SELECT id, password_hash, role FROM users WHERE username = %s', (username,))
            user = cur.fetchone()
            
            if user and check_password_hash(user[1], password):
                # Store user ID and role in session
                session['admin_id'] = user[0]
                session['admin_role'] = user[2]
                
                # Update last login time
                cur.execute(
                    'UPDATE users SET last_login = %s WHERE id = %s',
                    (datetime.now(), user[0])
                )
                conn.commit()
                
                return redirect(url_for('admin.dashboard'))
            else:
                flash('Invalid username or password', 'error')
                return render_template('admin/login.html')
        except Exception as e:
            logger.error(f"Error during login: {e}")
            flash('An error occurred during login', 'error')
            return render_template('admin/login.html')
        finally:
            conn.close()
    
    return render_template('admin/login.html')

# Admin logout
@admin_bp.route('/logout')
def logout():
    """Handle admin logout."""
    session.pop('admin_id', None)
    session.pop('admin_role', None)
    return redirect(url_for('admin.login'))

# Admin dashboard
@admin_bp.route('/')
def dashboard():
    """Display the admin dashboard."""
    from app import get_db_connection
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # Get all experiments
        cur.execute('SELECT id, type, name, created_at FROM experiments ORDER BY created_at DESC')
        experiments = cur.fetchall()
        
        # Get active participant count
        cur.execute('SELECT COUNT(*) FROM participants WHERE completed_at IS NULL')
        active_participants = cur.fetchone()[0]
        
        # Get total experiment count
        cur.execute('SELECT COUNT(*) FROM experiments')
        experiment_count = cur.fetchone()[0]
        
        # Get admin user info
        cur.execute('SELECT username, role FROM users WHERE id = %s', (session['admin_id'],))
        admin = cur.fetchone()
        
        return render_template(
            'admin/dashboard.html',
            experiments=experiments,
            active_participants=active_participants,
            experiment_count=experiment_count,
            admin=admin
        )
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash('An error occurred while loading the dashboard', 'error')
        return render_template('admin/dashboard.html')
    finally:
        conn.close()

# Create new experiment
@admin_bp.route('/experiments/new', methods=['GET', 'POST'])
def new_experiment():
    """Create a new experiment."""
    if request.method == 'POST':
        name = request.form.get('name')
        exp_type = request.form.get('type')
        description = request.form.get('description')
        
        # Parse parameters from form (assuming JSON)
        parameters_json = request.form.get('parameters', '{}')
        try:
            parameters = json.loads(parameters_json)
        except json.JSONDecodeError:
            flash('Invalid parameters JSON format', 'error')
            return render_template('admin/new_experiment.html')
        
        from app import get_db_connection
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            
            # Insert new experiment
            cur.execute(
                'INSERT INTO experiments (type, name, description, parameters, created_at) '
                'VALUES (%s, %s, %s, %s, %s) RETURNING id',
                (exp_type, name, description, json.dumps(parameters), datetime.now())
            )
            experiment_id = cur.fetchone()[0]
            conn.commit()
            
            # Generate initial keys if specified
            key_count = request.form.get('key_count')
            if key_count and key_count.isdigit() and int(key_count) > 0:
                create_keys_for_experiment(experiment_id, int(key_count), conn)
            
            flash(f'Experiment "{name}" created successfully', 'success')
            return redirect(url_for('admin.view_experiment', experiment_id=experiment_id))
        except Exception as e:
            logger.error(f"Error creating experiment: {e}")
            conn.rollback()
            flash('An error occurred while creating the experiment', 'error')
            return render_template('admin/new_experiment.html')
        finally:
            conn.close()
    
    # GET request - show form
    return render_template('admin/new_experiment.html')

# View experiment details
@admin_bp.route('/experiments/<int:experiment_id>')
def view_experiment(experiment_id):
    """View experiment details."""
    from app import get_db_connection
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # Get experiment details
        cur.execute(
            'SELECT id, type, name, description, parameters, created_at FROM experiments WHERE id = %s',
            (experiment_id,)
        )
        experiment = cur.fetchone()
        
        if not experiment:
            flash('Experiment not found', 'error')
            return redirect(url_for('admin.dashboard'))
        
        # Get participant count
        cur.execute('SELECT COUNT(*) FROM participants WHERE experiment_id = %s', (experiment_id,))
        participant_count = cur.fetchone()[0]
        
        # Get keys
        keys = get_keys_for_experiment(experiment_id, conn)
        
        # Get completed rounds
        cur.execute(
            'SELECT COUNT(*) FROM experiment_rounds WHERE experiment_id = %s AND status = %s',
            (experiment_id, 'completed')
        )
        completed_rounds = cur.fetchone()[0]
        
        return render_template(
            'admin/view_experiment.html',
            experiment=experiment,
            participant_count=participant_count,
            keys=keys,
            completed_rounds=completed_rounds
        )
    except Exception as e:
        logger.error(f"Error viewing experiment {experiment_id}: {e}")
        flash('An error occurred while loading the experiment details', 'error')
        return redirect(url_for('admin.dashboard'))
    finally:
        conn.close()

# Generate keys for an experiment
@admin_bp.route('/experiments/<int:experiment_id>/keys/generate', methods=['POST'])
def generate_keys(experiment_id):
    """Generate new keys for an experiment."""
    count = request.form.get('count')
    
    if not count or not count.isdigit() or int(count) <= 0:
        flash('Please provide a valid count', 'error')
        return redirect(url_for('admin.view_experiment', experiment_id=experiment_id))
    
    count = int(count)
    
    try:
        keys = create_keys_for_experiment(experiment_id, count)
        flash(f'Generated {len(keys)} new keys successfully', 'success')
    except Exception as e:
        logger.error(f"Error generating keys: {e}")
        flash('An error occurred while generating keys', 'error')
    
    return redirect(url_for('admin.view_experiment', experiment_id=experiment_id))

# Revoke a key
@admin_bp.route('/keys/<key>/revoke', methods=['POST'])
def revoke_key_route(key):
    """Revoke a specific key."""
    try:
        if revoke_key(key):
            flash('Key revoked successfully', 'success')
        else:
            flash('Key not found or already revoked', 'error')
    except Exception as e:
        logger.error(f"Error revoking key {key}: {e}")
        flash('An error occurred while revoking the key', 'error')
    
    return redirect(request.referrer or url_for('admin.dashboard'))

# API endpoint to get experiment results
@admin_bp.route('/api/experiments/<int:experiment_id>/results')
def experiment_results_api(experiment_id):
    """API endpoint to get experiment results."""
    from app import get_db_connection
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # Get all rounds for this experiment
        cur.execute(
            'SELECT er.id, er.round_number, er.started_at, er.completed_at, rr.results '
            'FROM experiment_rounds er '
            'LEFT JOIN round_results rr ON er.id = rr.round_id '
            'WHERE er.experiment_id = %s '
            'ORDER BY er.round_number',
            (experiment_id,)
        )
        
        rounds = []
        for row in cur.fetchall():
            round_id, round_number, started_at, completed_at, results = row
            rounds.append({
                'id': round_id,
                'round_number': round_number,
                'started_at': started_at.isoformat() if started_at else None,
                'completed_at': completed_at.isoformat() if completed_at else None,
                'results': results
            })
        
        # Get participant information
        cur.execute(
            'SELECT p.id, p.participant_type, p.joined_at, p.completed_at, pk.key_value '
            'FROM participants p '
            'JOIN participant_keys pk ON p.key_id = pk.id '
            'WHERE p.experiment_id = %s',
            (experiment_id,)
        )
        
        participants = []
        for row in cur.fetchall():
            p_id, p_type, joined_at, completed_at, key = row
            participants.append({
                'id': p_id,
                'type': p_type,
                'joined_at': joined_at.isoformat() if joined_at else None,
                'completed_at': completed_at.isoformat() if completed_at else None,
                'key': key
            })
        
        # Get experiment details
        cur.execute(
            'SELECT type, name, description, parameters, created_at FROM experiments WHERE id = %s',
            (experiment_id,)
        )
        exp = cur.fetchone()
        if not exp:
            return jsonify({'error': 'Experiment not found'}), 404
        
        experiment = {
            'id': experiment_id,
            'type': exp[0],
            'name': exp[1],
            'description': exp[2],
            'parameters': exp[3],
            'created_at': exp[4].isoformat() if exp[4] else None
        }
        
        return jsonify({
            'experiment': experiment,
            'rounds': rounds,
            'participants': participants
        })
    except Exception as e:
        logger.error(f"Error fetching experiment results: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# Register admin user (restricted to existing admins)
@admin_bp.route('/users/register', methods=['GET', 'POST'])
def register_user():
    """Register a new admin or researcher user."""
    # Check if user has admin role
    if session.get('admin_role') != 'admin':
        flash('Only administrators can register new users', 'error')
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        role = request.form.get('role', 'researcher')
        
        if not username or not password:
            flash('Please provide username and password', 'error')
            return render_template('admin/register_user.html')
        
        # Validate role
        if role not in ['admin', 'researcher']:
            role = 'researcher'  # Default to researcher if invalid
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        from app import get_db_connection
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            
            # Check if username already exists
            cur.execute('SELECT 1 FROM users WHERE username = %s', (username,))
            if cur.fetchone():
                flash('Username already exists', 'error')
                return render_template('admin/register_user.html')
            
            # Check if email already exists (if provided)
            if email:
                cur.execute('SELECT 1 FROM users WHERE email = %s', (email,))
                if cur.fetchone():
                    flash('Email already exists', 'error')
                    return render_template('admin/register_user.html')
            
            # Insert new user
            cur.execute(
                'INSERT INTO users (username, password_hash, email, role, created_at) '
                'VALUES (%s, %s, %s, %s, %s)',
                (username, password_hash, email, role, datetime.now())
            )
            conn.commit()
            
            flash(f'User {username} registered successfully', 'success')
            return redirect(url_for('admin.dashboard'))
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            conn.rollback()
            flash('An error occurred while registering the user', 'error')
            return render_template('admin/register_user.html')
        finally:
            conn.close()
    
    # GET request - show form
    return render_template('admin/register_user.html')

def register_admin_routes(app):
    """Register the admin blueprint with the Flask app."""
    app.register_blueprint(admin_bp)
    logger.info("Registered admin routes")