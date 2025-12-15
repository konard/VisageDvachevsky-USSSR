"""
Integration tests for API endpoints
"""
import pytest
import json


def test_get_leaders(client, sample_leader):
    """Test getting all leaders"""
    response = client.get('/api/leaders/')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['count'] >= 1


def test_get_leader_by_id(client, sample_leader):
    """Test getting a specific leader"""
    response = client.get(f'/api/leaders/{sample_leader.id}')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert data['data']['id'] == sample_leader.id


def test_search_leaders(client, sample_leader):
    """Test searching leaders"""
    response = client.get('/api/leaders/search?q=Test')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'


def test_login(client, regular_user):
    """Test user login"""
    response = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert 'access_token' in data['data']


def test_login_invalid_credentials(client, db):
    """Test login with invalid credentials"""
    response = client.post('/api/auth/login', json={
        'username': 'nonexistent',
        'password': 'wrongpass'
    })

    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['success'] == False
