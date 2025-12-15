"""
Permission checking decorators
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from ..services.auth_service import AuthService


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)

        if not user or user.role.name != 'admin':
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403

        return f(*args, **kwargs)
    return decorated_function


def permission_required(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = get_jwt_identity()
            user = AuthService.get_user_by_id(user_id)

            if not user or not user.has_permission(permission):
                return jsonify({
                    'success': False,
                    'error': f'Permission required: {permission}'
                }), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator
