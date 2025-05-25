import sys
import os
from pathlib import Path
from passlib.hash import bcrypt
import datetime

# Add the parent directory to the path to allow imports
parent_dir = str(Path(__file__).resolve().parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from db.database import get_user_by_username, add_user

class Auth:
    @staticmethod
    def hash_password(password):
        """Hash a password for storing."""
        return bcrypt.hash(password)
    
    @staticmethod
    def verify_password(stored_hash, provided_password):
        """Verify a stored password against one provided by user"""
        return bcrypt.verify(provided_password, stored_hash)
    
    @staticmethod
    def register_user(username, password, role, email, emp_code="", designation=""):
        """Register a new user"""
        # Hash the password
        hashed_password = Auth.hash_password(password)
        
        # Add the user to the database
        user_id = add_user(username, hashed_password, role, email, emp_code, designation)
        return user_id is not None
    
    @staticmethod
    def login(username, password):
        """Attempt to log in with username and password"""
        user = get_user_by_username(username)
        
        if not user:
            return None
        
        if Auth.verify_password(user['password_hash'], password):
            # Remove password hash from user data before returning
            user.pop('password_hash', None)
            return user
        
        return None
    
    @staticmethod
    def is_admin(user):
        """Check if the user is an admin"""
        return user and user['role'] == 'admin'
    
    @staticmethod
    def is_unit_leader(user):
        """Check if the user is a unit leader"""
        return user and user['role'] == 'unit_leader'
    
    @staticmethod
    def is_regular_user(user):
        """Check if the user is a regular user"""
        return user and user['role'] == 'user' 