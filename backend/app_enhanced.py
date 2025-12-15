"""
Enhanced Flask application for USSR Leaders Platform
Production-ready with authentication, caching, rate limiting, and comprehensive logging
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_migrate import Migrate

# Import configuration
from config import get_config

# Import models and database
from models.base import db
from models import Leader, User, Role, ActivityLog

# Import services
from services.auth_service import AuthService

# Import routes
from routes import leaders_bp, auth_bp, analytics_bp


def create_app(config_name=None):
    """Application factory pattern"""

    app = Flask(__name__,
                template_folder='../frontend/templates',
                static_folder='../frontend/static')

    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)

    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    jwt = JWTManager(app)
    bcrypt = Bcrypt(app)
    migrate = Migrate(app, db)

    # Initialize caching
    cache = Cache(app, config={
        'CACHE_TYPE': app.config['CACHE_TYPE'],
        'CACHE_DEFAULT_TIMEOUT': app.config['CACHE_DEFAULT_TIMEOUT']
    })

    # Initialize rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=app.config['RATELIMIT_STORAGE_URI'],
        strategy=app.config['RATELIMIT_STRATEGY'],
        default_limits=[app.config['RATELIMIT_DEFAULT']]
    )

    # Setup logging
    setup_logging(app)

    # Register blueprints
    app.register_blueprint(leaders_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(analytics_bp)

    # Register error handlers
    register_error_handlers(app)

    # Register CLI commands
    register_cli_commands(app)

    # Main route
    @app.route('/')
    def index():
        """Render main page"""
        return render_template('index.html')

    # Video serving route
    @app.route('/videos/<path:filename>')
    def serve_video(filename):
        """Serve video files"""
        videos_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'videos')
        return send_from_directory(videos_dir, filename)

    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring"""
        return jsonify({
            'status': 'healthy',
            'app': app.config['APP_NAME'],
            'version': app.config['APP_VERSION']
        }), 200

    # Create tables and initialize data
    with app.app_context():
        db.create_all()
        initialize_database(app)

    app.logger.info(f"{app.config['APP_NAME']} v{app.config['APP_VERSION']} started")

    return app


def setup_logging(app):
    """Configure comprehensive logging"""

    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(app.config['LOG_FILE'])
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # File handler with rotation
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(app.config['LOG_FORMAT']))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(app.config['LOG_FORMAT']))
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    app.logger.addHandler(console_handler)

    app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
    app.logger.info('Logging configured')


def register_error_handlers(app):
    """Register custom error handlers"""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 'Bad request',
            'message': str(error)
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'success': False,
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'success': False,
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Not found',
            'message': 'Resource not found'
        }), 404

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'success': False,
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.'
        }), 429

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Internal server error: {error}')
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500


def initialize_database(app):
    """Initialize database with default data"""

    # Initialize roles
    AuthService.initialize_roles()
    app.logger.info('Roles initialized')

    # Check if we need to create default admin
    admin = User.get_by_username('admin')
    if not admin:
        try:
            AuthService.create_admin_user(
                username='admin',
                email='admin@usssr-leaders.local',
                password=os.getenv('ADMIN_PASSWORD', 'admin123'),  # Change in production!
                full_name='System Administrator'
            )
            app.logger.info('Default admin user created')
        except Exception as e:
            app.logger.error(f'Failed to create admin user: {e}')

    # Initialize leaders data if empty
    if Leader.query.count() == 0:
        initialize_leaders_data(app)


def initialize_leaders_data(app):
    """Initialize leaders data"""

    leaders_data = [
        {
            'id': 1,
            'name_ru': 'Владимир Ильич Ленин',
            'name_en': 'Vladimir Ilyich Lenin',
            'slug': 'lenin',
            'birth_year': 1870,
            'birth_place': 'Симбирск',
            'death_year': 1924,
            'death_place': 'под Москвой',
            'position': 'Председатель Совета народных комиссаров',
            'achievements': 'Организовал Октябрьскую революцию и создал первое в мире социалистическое государство.',
            'short_description': 'Основатель Советского государства и теоретик марксизма-ленинизма',
            'years_in_power_start': 1917,
            'years_in_power_end': 1924,
            'historical_significance': 10,
            'video_id': 1,
            'is_published': True
        },
        {
            'id': 2,
            'name_ru': 'Иосиф Виссарионович Сталин',
            'name_en': 'Joseph Vissarionovich Stalin',
            'slug': 'stalin',
            'birth_year': 1878,
            'birth_place': 'Гори (Грузия)',
            'death_year': 1953,
            'death_place': 'под Москвой (Кунцево)',
            'position': 'Генеральный секретарь ЦК ВКП(б)',
            'achievements': 'Провёл индустриализацию и коллективизацию страны. Одержал победу во Второй мировой войне и сделал СССР сверхдержавой.',
            'short_description': 'Руководитель СССР в период индустриализации и Великой Отечественной войны',
            'years_in_power_start': 1924,
            'years_in_power_end': 1953,
            'historical_significance': 10,
            'video_id': 2,
            'is_published': True
        },
        {
            'id': 3,
            'name_ru': 'Никита Сергеевич Хрущёв',
            'name_en': 'Nikita Sergeyevich Khrushchev',
            'slug': 'khrushchev',
            'birth_year': 1894,
            'birth_place': 'Калиновка (Россия)',
            'death_year': 1971,
            'death_place': 'Москва',
            'position': 'Первый секретарь ЦК КПСС',
            'achievements': 'Провёл десталинизацию и ослабил репрессии. Участвовал в Карибском кризисе и запустил советскую космическую программу.',
            'short_description': 'Инициатор десталинизации и космических достижений СССР',
            'years_in_power_start': 1953,
            'years_in_power_end': 1964,
            'historical_significance': 8,
            'video_id': 3,
            'is_published': True
        },
        {
            'id': 4,
            'name_ru': 'Леонид Ильич Брежнев',
            'name_en': 'Leonid Ilyich Brezhnev',
            'slug': 'brezhnev',
            'birth_year': 1906,
            'birth_place': 'Каменское (Украина)',
            'death_year': 1982,
            'death_place': 'Москва',
            'position': 'Генеральный секретарь ЦК КПСС',
            'achievements': 'Период стабильности и "эпохи застоя". Укрепил военную мощь СССР и расширил влияние на международной арене.',
            'short_description': 'Руководитель СССР в период застоя и военного паритета с США',
            'years_in_power_start': 1964,
            'years_in_power_end': 1982,
            'historical_significance': 7,
            'video_id': 4,
            'is_published': True
        },
        {
            'id': 5,
            'name_ru': 'Юрий Владимирович Андропов',
            'name_en': 'Yuri Vladimirovich Andropov',
            'slug': 'andropov',
            'birth_year': 1914,
            'birth_place': 'село Нивки (ныне Украина)',
            'death_year': 1984,
            'death_place': 'Москва',
            'position': 'Генеральный секретарь ЦК КПСС',
            'achievements': 'Боролся с коррупцией и улучшал дисциплину. Начал реформы для укрепления порядка и экономической стабилизации.',
            'short_description': 'Бывший глава КГБ, инициатор борьбы с коррупцией',
            'years_in_power_start': 1982,
            'years_in_power_end': 1984,
            'historical_significance': 6,
            'video_id': 5,
            'is_published': True
        },
        {
            'id': 6,
            'name_ru': 'Константин Устинович Черненко',
            'name_en': 'Konstantin Ustinovich Chernenko',
            'slug': 'chernenko',
            'birth_year': 1911,
            'birth_place': 'село Привольное (Россия)',
            'death_year': 1985,
            'death_place': 'Москва',
            'position': 'Генеральный секретарь ЦК КПСС',
            'achievements': 'Правил недолго, продолжал политику застоя. Отличался консерватизмом и отсутствием серьёзных реформ.',
            'short_description': 'Последний лидер старой гвардии перед перестройкой',
            'years_in_power_start': 1984,
            'years_in_power_end': 1985,
            'historical_significance': 5,
            'video_id': 6,
            'is_published': True
        },
        {
            'id': 7,
            'name_ru': 'Михаил Сергеевич Горбачёв',
            'name_en': 'Mikhail Sergeyevich Gorbachev',
            'slug': 'gorbachev',
            'birth_year': 1931,
            'birth_place': 'село Привольное (Россия)',
            'death_year': 2022,
            'death_place': 'Москва',
            'position': 'Генеральный секретарь ЦК КПСС и Президент СССР',
            'achievements': 'Провёл реформы "перестройка" и "гласность", демократизация и распад СССР. Символ конца советской эпохи.',
            'short_description': 'Последний лидер СССР, лауреат Нобелевской премии мира',
            'years_in_power_start': 1985,
            'years_in_power_end': 1991,
            'historical_significance': 10,
            'video_id': 7,
            'is_published': True
        }
    ]

    for leader_data in leaders_data:
        leader = Leader(**leader_data)
        db.session.add(leader)

    try:
        db.session.commit()
        app.logger.info(f'Initialized {len(leaders_data)} leaders')
    except Exception as e:
        app.logger.error(f'Error initializing leaders: {e}')
        db.session.rollback()


def register_cli_commands(app):
    """Register custom CLI commands"""

    @app.cli.command('init-db')
    def init_db():
        """Initialize the database"""
        db.create_all()
        initialize_database(app)
        print('Database initialized!')

    @app.cli.command('create-admin')
    def create_admin():
        """Create an admin user"""
        username = input('Enter username: ')
        email = input('Enter email: ')
        password = input('Enter password: ')
        full_name = input('Enter full name (optional): ')

        try:
            AuthService.create_admin_user(
                username=username,
                email=email,
                password=password,
                full_name=full_name if full_name else None
            )
            print(f'Admin user "{username}" created successfully!')
        except Exception as e:
            print(f'Error: {e}')


# Create application instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true')
