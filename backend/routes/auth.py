"""
Authentication API routes
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.auth_service import AuthService
from ..middleware.decorators import rate_limit
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
@rate_limit("5 per hour")
def register():
    """Register a new user"""
    try:
        data = request.get_json()

        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        result = AuthService.register_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            full_name=data.get('full_name')
        )

        return jsonify({
            'success': True,
            'data': result
        }), 201

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        return jsonify({
            'success': False,
            'error': 'Registration failed'
        }), 500


@auth_bp.route('/login', methods=['POST'])
@rate_limit("10 per hour")
def login():
    """Login user"""
    try:
        data = request.get_json()

        if 'username' not in data or 'password' not in data:
            return jsonify({
                'success': False,
                'error': 'Username and password required'
            }), 400

        result = AuthService.login_user(
            username=data['username'],
            password=data['password']
        )

        return jsonify({
            'success': True,
            'data': result
        }), 200

    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 401
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return jsonify({
            'success': False,
            'error': 'Login failed'
        }), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information"""
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)

        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        return jsonify({
            'success': True,
            'data': user.to_dict(include_sensitive=True)
        }), 200

    except Exception as e:
        logger.error(f"Error fetching current user: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch user'
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        user_id = get_jwt_identity()
        result = AuthService.refresh_token(user_id)

        return jsonify({
            'success': True,
            'data': result
        }), 200

    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return jsonify({
            'success': False,
            'error': 'Token refresh failed'
        }), 500
