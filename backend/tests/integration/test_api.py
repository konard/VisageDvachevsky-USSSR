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


def test_get_leaders_exposes_archive_media_fields(client, seeded_db):
    """Leaders API should expose portrait, video and category metadata for archive cards"""
    response = client.get('/api/leaders/')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True

    leader = data['data'][0]
    assert 'portrait_url' in leader
    assert 'video_id' in leader
    assert 'category' in leader


def test_get_leaders_returns_expanded_roster_with_categories(client, seeded_db):
    """Seeded roster should expose the full set of 36 figures grouped by domain."""
    response = client.get('/api/leaders/')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True

    leaders = data['data']
    assert len(leaders) >= 36

    categories = {leader.get('category') for leader in leaders}
    expected_categories = {'politics', 'military', 'space', 'science', 'culture', 'sports', 'labor'}
    missing = expected_categories - categories
    assert not missing, f'Missing categories: {missing}'


def test_get_leaders_preserves_expected_portrait_assignments(client, seeded_db):
    """Specific historical figures should keep their intended portraits."""
    expected_portrait_fragments = {
        'Владимир Ильич Ленин': '01_lenin',
        'Иосиф Виссарионович Сталин': '02_stalin',
        'Никита Сергеевич Хрущёв': '03_khrushchev',
        'Леонид Ильич Брежнев': '04_brezhnev',
        'Юрий Владимирович Андропов': '05_andropov',
        'Константин Устинович Черненко': '06_chernenko',
        'Михаил Сергеевич Горбачёв': '07_gorbachev',
        'Георгий Константинович Жуков': '08_zhukov',
        'Юрий Алексеевич Гагарин': '09_gagarin',
        'Сергей Павлович Королёв': '10_korolev',
        'Валентина Владимировна Терешкова': '11_tereshkova',
        'Алексей Григорьевич Стаханов': '12_stakhanov',
        'Андрей Дмитриевич Сахаров': '13_sakharov',
        'Игорь Васильевич Курчатов': '14_kurchatov',
        'Дмитрий Дмитриевич Шостакович': '15_shostakovich',
        'Сергей Михайлович Эйзенштейн': '16_eisenstein',
        'Михаил Александрович Шолохов': '17_sholokhov',
        'Владимир Семёнович Высоцкий': '18_vysotsky',
        'Лев Иванович Яшин': '19_yashin',
        'Майя Михайловна Плисецкая': '20_plisetskaya',
        'Михаил Тимофеевич Калашников': '21_kalashnikov',
        'Александр Исаевич Солженицын': '22_solzhenitsyn',
        'Алексей Архипович Леонов': '23_leonov',
        'Константин Константинович Рокоссовский': '24_rokossovsky',
        'Андрей Николаевич Туполев': '25_tupolev',
        'Пётр Леонидович Капица': '26_kapitsa',
        'Лев Давидович Ландау': '27_landau',
        'Галина Сергеевна Уланова': '28_ulanova',
        'Булат Шалвович Окуджава': '29_okudzhava',
        'Михаил Иванович Калинин': '30_kalinin',
        'Вячеслав Михайлович Молотов': '31_molotov',
        'Семён Михайлович Будённый': '32_budyonny',
        'Валерий Павлович Чкалов': '33_chkalov',
        'Иван Дмитриевич Папанин': '34_papanin',
        'Трофим Денисович Лысенко': '35_lysenko',
        'Анна Андреевна Ахматова': '36_akhmatova',
    }

    response = client.get('/api/leaders/')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True

    portraits_by_name = {leader['name_ru']: leader['portrait_url'] for leader in data['data']}

    for name, fragment in expected_portrait_fragments.items():
        assert name in portraits_by_name
        assert portraits_by_name[name]
        assert fragment in portraits_by_name[name]


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


def test_available_videos_endpoint(client):
    """Endpoint should return a list of available video IDs (may be empty in test env)."""
    response = client.get('/api/videos/available')

    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'available' in data
    assert isinstance(data['available'], list)
    # All entries must be integers
    for vid_id in data['available']:
        assert isinstance(vid_id, int)


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
