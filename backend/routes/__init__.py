"""
API routes module
"""
from .leaders import leaders_bp
from .auth import auth_bp
from .analytics import analytics_bp

__all__ = ['leaders_bp', 'auth_bp', 'analytics_bp']
