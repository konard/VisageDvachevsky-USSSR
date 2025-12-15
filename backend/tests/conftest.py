"""
Pytest configuration and fixtures
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app_enhanced import create_app
from models.base import db as _db
from models import Leader, User, Role
from services.auth_service import AuthService


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    app = create_app('testing')
    return app


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='function')
def db(app):
    """Create database for testing"""
    with app.app_context():
        _db.create_all()
        AuthService.initialize_roles()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def admin_user(db):
    """Create admin user for testing"""
    user = AuthService.create_admin_user(
        username='testadmin',
        email='admin@test.com',
        password='testpass123',
        full_name='Test Admin'
    )
    return user


@pytest.fixture
def regular_user(db):
    """Create regular user for testing"""
    user = User.create_user(
        username='testuser',
        email='user@test.com',
        password='testpass123',
        role_name='user',
        full_name='Test User'
    )
    return user


@pytest.fixture
def sample_leader(db):
    """Create sample leader for testing"""
    leader = Leader(
        name_ru='Тестовый Лидер',
        name_en='Test Leader',
        slug='test-leader',
        birth_year=1900,
        birth_place='Москва',
        position='Тестовая должность',
        achievements='Тестовые достижения',
        is_published=True
    )
    leader.save()
    return leader
