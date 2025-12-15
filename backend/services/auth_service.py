"""
Authentication service for user management
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from flask_jwt_extended import create_access_token, create_refresh_token
from ..models.user import User, Role
from ..models.base import db

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling authentication and authorization"""

    @staticmethod
    def register_user(username: str, email: str, password: str, full_name: Optional[str] = None) -> Dict:
        """
        Register a new user

        Args:
            username: Username
            email: Email address
            password: Plain text password
            full_name: Full name (optional)

        Returns:
            Dictionary with user data and tokens

        Raises:
            ValueError: If username or email already exists
        """
        # Check if user exists
        if User.get_by_username(username):
            raise ValueError("Username already exists")

        if User.get_by_email(email):
            raise ValueError("Email already exists")

        # Create user with default 'user' role
        try:
            user = User.create_user(
                username=username,
                email=email,
                password=password,
                role_name='user',
                full_name=full_name
            )

            # Generate tokens
            access_token = create_access_token(identity=user.id)
            refresh_token = create_refresh_token(identity=user.id)

            logger.info(f"New user registered: {username}")

            return {
                'user': user.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token
            }

        except Exception as e:
            logger.error(f"Error registering user: {e}")
            db.session.rollback()
            raise

    @staticmethod
    def login_user(username: str, password: str) -> Dict:
        """
        Login user and generate tokens

        Args:
            username: Username or email
            password: Plain text password

        Returns:
            Dictionary with user data and tokens

        Raises:
            ValueError: If credentials are invalid
        """
        # Try to find user by username or email
        user = User.get_by_username(username) or User.get_by_email(username)

        if not user:
            raise ValueError("Invalid credentials")

        if not user.check_password(password):
            raise ValueError("Invalid credentials")

        if not user.is_active:
            raise ValueError("Account is deactivated")

        # Update last login
        user.update_last_login()

        # Generate tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        logger.info(f"User logged in: {username}")

        return {
            'user': user.to_dict(include_sensitive=True),
            'access_token': access_token,
            'refresh_token': refresh_token
        }

    @staticmethod
    def refresh_token(user_id: int) -> Dict:
        """
        Refresh access token

        Args:
            user_id: User ID

        Returns:
            Dictionary with new access token
        """
        access_token = create_access_token(identity=user_id)

        return {
            'access_token': access_token
        }

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """
        Get user by ID

        Args:
            user_id: User ID

        Returns:
            User object or None
        """
        return User.get_by_id(user_id)

    @staticmethod
    def initialize_roles():
        """Initialize default roles if they don't exist"""
        roles_config = [
            {
                'name': 'guest',
                'description': 'Guest user with read-only access',
                'permissions': ['view_leaders', 'search_leaders']
            },
            {
                'name': 'user',
                'description': 'Regular authenticated user',
                'permissions': ['view_leaders', 'search_leaders', 'view_facts', 'track_activity']
            },
            {
                'name': 'admin',
                'description': 'Administrator with full access',
                'permissions': [
                    'view_leaders', 'search_leaders', 'view_facts',
                    'create_leaders', 'update_leaders', 'delete_leaders',
                    'manage_users', 'view_analytics', 'track_activity'
                ]
            }
        ]

        for role_data in roles_config:
            existing_role = Role.get_by_name(role_data['name'])
            if not existing_role:
                role = Role(
                    name=role_data['name'],
                    description=role_data['description'],
                    permissions=role_data['permissions']
                )
                role.save()
                logger.info(f"Created role: {role_data['name']}")

    @staticmethod
    def create_admin_user(username: str, email: str, password: str, full_name: Optional[str] = None):
        """
        Create an admin user

        Args:
            username: Username
            email: Email address
            password: Plain text password
            full_name: Full name (optional)
        """
        try:
            user = User.create_user(
                username=username,
                email=email,
                password=password,
                role_name='admin',
                full_name=full_name
            )
            user.is_verified = True
            user.save()
            logger.info(f"Admin user created: {username}")
            return user
        except Exception as e:
            logger.error(f"Error creating admin user: {e}")
            db.session.rollback()
            raise
