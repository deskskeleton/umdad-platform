"""
Authentication package initialization.

This package contains modules for authentication and key management.
"""

# Import key_manager to make it available when importing the package
from .key_manager import (
    generate_key,
    create_keys_for_experiment,
    validate_key,
    mark_key_as_used,
    revoke_key,
    get_keys_for_experiment
)