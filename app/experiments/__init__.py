"""
Experiments package initialization.

This module provides functions to discover and register experiment modules.
Experiment modules are dynamically loaded and registered with the Flask app.
"""

import os
import importlib
import logging
from flask import Blueprint

# Set up logger
logger = logging.getLogger(__name__)

# Dictionary to store registered experiment modules
_experiments = {}

def register_experiment(experiment_type, module):
    """
    Register an experiment module.
    
    Args:
        experiment_type (str): Unique identifier for the experiment type
        module: The experiment module to register
    """
    if experiment_type in _experiments:
        logger.warning(f"Experiment type '{experiment_type}' already registered. Overwriting.")
    
    _experiments[experiment_type] = module
    logger.info(f"Registered experiment module: {experiment_type}")

def get_available_experiments():
    """
    Get a dictionary of all registered experiment types.
    
    Returns:
        dict: Dictionary of experiment types to their modules
    """
    return _experiments

def register_experiment_routes(app):
    """
    Register all experiment routes with the Flask app.
    
    Args:
        app: The Flask application instance
    """
    logger.info("Registering experiment routes...")
    
    experiments_path = os.path.dirname(__file__)
    
    # Loop through all Python modules in the experiments directory
    for filename in os.listdir(experiments_path):
        # Skip __init__.py and non-Python files
        if filename == "__init__.py" or not filename.endswith(".py"):
            continue
        
        module_name = filename[:-3]  # Remove .py extension
        
        try:
            # Import the module
            module = importlib.import_module(f"experiments.{module_name}")
            
            # Check if the module has the required register_blueprint function
            if hasattr(module, "register_blueprint"):
                blueprint = module.register_blueprint()
                
                if isinstance(blueprint, Blueprint):
                    # Register the blueprint with the app
                    app.register_blueprint(blueprint)
                    
                    # Register the experiment type if it defines one
                    if hasattr(module, "EXPERIMENT_TYPE"):
                        register_experiment(module.EXPERIMENT_TYPE, module)
                    else:
                        # Use the module name as the experiment type
                        register_experiment(module_name, module)
                        
                    logger.info(f"Registered experiment blueprint: {module_name}")
                else:
                    logger.warning(f"Module {module_name} register_blueprint() didn't return a Blueprint")
            else:
                logger.warning(f"Module {module_name} doesn't implement register_blueprint()")
                
        except Exception as e:
            logger.error(f"Error registering experiment module {module_name}: {e}")
    
    logger.info(f"Registered {len(_experiments)} experiment modules")