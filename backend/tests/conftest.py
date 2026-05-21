"""
Pytest configuration and fixtures.

Heavy fixtures that rely on the enhanced application stack (Flask, SQLAlchemy,
JWT, etc.) are registered conditionally so that lightweight unit tests can run
in environments where only ``requests``/``pytest`` are installed.
"""
import os
import sys

import pytest

# Make ``backend`` importable as a top-level package.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from app_enhanced import create_app, initialize_leaders_data
    from models.base import db as _db
    from models import Leader, User, Role
    from services.auth_service import AuthService
except Exception:  # pragma: no cover - optional stack
    create_app = None  # type: ignore[assignment]
    initialize_leaders_data = None  # type: ignore[assignment]
    _db = None  # type: ignore[assignment]
    Leader = User = Role = None  # type: ignore[assignment,misc]
    AuthService = None  # type: ignore[assignment,misc]


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    if create_app is None:
        pytest.skip("enhanced application stack is unavailable")
    return create_app('testing')


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


@pytest.fixture(scope='function')
def seeded_db(db, app):
    """Database fixture pre-populated with the canonical set of leaders."""
    if initialize_leaders_data is None:
        pytest.skip("enhanced application stack is unavailable")
    initialize_leaders_data(app)
    return db


@pytest.fixture
def admin_user(db):
    """Create admin user for testing"""
    return AuthService.create_admin_user(
        username='testadmin',
        email='admin@test.com',
        password='testpass123',
        full_name='Test Admin'
    )


@pytest.fixture
def regular_user(db):
    """Create regular user for testing"""
    return User.create_user(
        username='testuser',
        email='user@test.com',
        password='testpass123',
        role_name='user',
        full_name='Test User'
    )


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
