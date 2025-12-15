"""
Unit tests for database models
"""
import pytest
from models import Leader, User, Role


def test_leader_creation(db):
    """Test creating a leader"""
    leader = Leader(
        name_ru='Владимир Ленин',
        name_en='Vladimir Lenin',
        slug='lenin',
        birth_year=1870,
        is_published=True
    )
    leader.save()

    assert leader.id is not None
    assert leader.name_ru == 'Владимир Ленин'
    assert leader.is_published == True


def test_leader_to_dict(sample_leader):
    """Test leader serialization"""
    data = sample_leader.to_dict()

    assert data['id'] == sample_leader.id
    assert data['name_ru'] == sample_leader.name_ru
    assert data['slug'] == sample_leader.slug


def test_user_password_hashing(db):
    """Test password hashing"""
    user = User.create_user(
        username='testuser',
        email='test@example.com',
        password='secretpassword',
        role_name='user'
    )

    assert user.password_hash != 'secretpassword'
    assert user.check_password('secretpassword')
    assert not user.check_password('wrongpassword')


def test_role_permissions(db):
    """Test role permissions"""
    admin_role = Role.get_by_name('admin')
    user_role = Role.get_by_name('user')

    assert admin_role.has_permission('create_leaders')
    assert not user_role.has_permission('create_leaders')
