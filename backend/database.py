"""
Database module for USSR Leaders Platform
"""
import sqlite3
import json
import os

class Database:
    """Database handler for leader information"""

    def __init__(self, db_path='leaders.db'):
        """Initialize database connection"""
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaders (
                id INTEGER PRIMARY KEY,
                name_ru TEXT NOT NULL,
                name_en TEXT NOT NULL,
                birth_year INTEGER,
                birth_place TEXT,
                death_year INTEGER,
                death_place TEXT,
                position TEXT,
                achievements TEXT,
                video_id INTEGER,
                portrait_url TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def initialize_data(self):
        """Initialize database with USSR leaders data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if data already exists
        cursor.execute('SELECT COUNT(*) FROM leaders')
        if cursor.fetchone()[0] > 0:
            conn.close()
            return

        leaders_data = [
            {
                'id': 1,
                'name_ru': 'Владимир Ильич Ленин',
                'name_en': 'Vladimir Ilyich Lenin',
                'birth_year': 1870,
                'birth_place': 'Симбирск',
                'death_year': 1924,
                'death_place': 'под Москвой',
                'position': 'Председатель Совета народных комиссаров',
                'achievements': 'Организовал Октябрьскую революцию и создал первое в мире социалистическое государство.',
                'video_id': 1
            },
            {
                'id': 2,
                'name_ru': 'Иосиф Виссарионович Сталин',
                'name_en': 'Joseph Vissarionovich Stalin',
                'birth_year': 1878,
                'birth_place': 'Гори (Грузия)',
                'death_year': 1953,
                'death_place': 'под Москвой (Кунцево)',
                'position': 'Генеральный секретарь ЦК ВКП(б)',
                'achievements': 'Провёл индустриализацию и коллективизацию страны. Одержал победу во Второй мировой войне и сделал СССР сверхдержавой.',
                'video_id': 2
            },
            {
                'id': 3,
                'name_ru': 'Никита Сергеевич Хрущёв',
                'name_en': 'Nikita Sergeyevich Khrushchev',
                'birth_year': 1894,
                'birth_place': 'Калиновка (Россия)',
                'death_year': 1971,
                'death_place': 'Москва',
                'position': 'Первый секретарь ЦК КПСС и председатель Совета министров СССР',
                'achievements': 'Провёл десталинизацию и ослабил репрессии. Участвовал в Карибском кризисе и запустил советскую космическую программу.',
                'video_id': 3
            },
            {
                'id': 4,
                'name_ru': 'Леонид Ильич Брежнев',
                'name_en': 'Leonid Ilyich Brezhnev',
                'birth_year': 1906,
                'birth_place': 'Каменское (Украина)',
                'death_year': 1982,
                'death_place': 'Москва',
                'position': 'Генеральный секретарь ЦК КПСС',
                'achievements': 'Закрепил период стабильности, но началась «эпоха застоя» с экономическим и политическим упадком. Укрепил военную мощь и расширил влияние СССР на международной арене.',
                'video_id': 4
            },
            {
                'id': 5,
                'name_ru': 'Юрий Владимирович Андропов',
                'name_en': 'Yuri Vladimirovich Andropov',
                'birth_year': 1914,
                'birth_place': 'село Нивки (ныне Украина)',
                'death_year': 1984,
                'death_place': 'Москва',
                'position': 'Генеральный секретарь ЦК КПСС, бывший глава КГБ',
                'achievements': 'Пытался бороться с коррупцией и улучшить дисциплину в стране. Правил недолго, но начал реформы, направленные на укрепление порядка и экономическую стабилизацию.',
                'video_id': 5
            },
            {
                'id': 6,
                'name_ru': 'Константин Устинович Черненко',
                'name_en': 'Konstantin Ustinovich Chernenko',
                'birth_year': 1911,
                'birth_place': 'село Привольное (Россия)',
                'death_year': 1985,
                'death_place': 'Москва',
                'position': 'Генеральный секретарь ЦК КПСС',
                'achievements': 'Правил недолго, продолжал политику застоя. Его руководство отличалось консерватизмом и отсутствием серьёзных реформ.',
                'video_id': 6
            },
            {
                'id': 7,
                'name_ru': 'Михаил Сергеевич Горбачёв',
                'name_en': 'Mikhail Sergeyevich Gorbachev',
                'birth_year': 1931,
                'birth_place': 'село Привольное (Россия)',
                'death_year': 2022,
                'death_place': 'Москва',
                'position': 'Генеральный секретарь ЦК КПСС и первый Президент СССР',
                'achievements': 'Провёл реформы «перестройка» и «гласность», которые привели к демократизации и распаду СССР. Стал символом конца советской эпохи и перехода к новому этапу в истории России.',
                'video_id': 7
            }
        ]

        for leader in leaders_data:
            cursor.execute('''
                INSERT INTO leaders (id, name_ru, name_en, birth_year, birth_place,
                                   death_year, death_place, position, achievements, video_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (leader['id'], leader['name_ru'], leader['name_en'],
                  leader['birth_year'], leader['birth_place'],
                  leader['death_year'], leader['death_place'],
                  leader['position'], leader['achievements'], leader['video_id']))

        conn.commit()
        conn.close()

    def get_all_leaders(self):
        """Get all leaders from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM leaders ORDER BY id')

        leaders = []
        for row in cursor.fetchall():
            leaders.append(dict(row))

        conn.close()
        return leaders

    def get_leader_by_id(self, leader_id):
        """Get leader by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM leaders WHERE id = ?', (leader_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None
