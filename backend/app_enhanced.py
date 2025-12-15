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
            'birth_place': 'Симбирск (ныне Ульяновск)',
            'death_year': 1924,
            'death_place': 'Горки Ленинские, под Москвой',
            'position': 'Председатель Совета народных комиссаров РСФСР и СССР',
            'achievements': 'Организовал Октябрьскую революцию 1917 года и создал первое в мире социалистическое государство. Провёл национализацию промышленности, заключил Брестский мир, создал Красную Армию.',
            'biography': 'Владимир Ильич Ульянов (Ленин) родился в 1870 году в семье инспектора народных училищ. Получил юридическое образование, но посвятил жизнь революционной деятельности. Развил марксистскую теорию применительно к российским условиям, создав учение, позже названное марксизмом-ленинизмом. Руководил большевистской партией с момента её создания. После Февральской революции 1917 года вернулся в Россию из эмиграции и возглавил Октябрьское вооружённое восстание, в результате которого к власти пришли большевики. Как глава первого советского правительства провёл радикальные социально-экономические преобразования: национализацию земли и промышленности, отделение церкви от государства, создание новой системы управления. В период Гражданской войны (1918-1922) отстоял советскую власть. В 1921 году ввёл Новую экономическую политику (НЭП), частично вернув рыночные отношения. Сыграл ключевую роль в образовании СССР в 1922 году.',
            'legacy': 'Ленин создал первое в мире государство рабочих и крестьян, заложил основы плановой экономики и однопартийной политической системы. Его идеи оказали глубокое влияние на мировое коммунистическое и рабочее движение XX века.',
            'short_description': 'Основатель Советского государства, теоретик марксизма-ленинизма и вождь Октябрьской революции',
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
            'birth_place': 'Гори, Тифлисская губерния (Грузия)',
            'death_year': 1953,
            'death_place': 'Ближняя дача в Кунцево, под Москвой',
            'position': 'Генеральный секретарь ЦК ВКП(б), затем КПСС, Председатель Совета министров СССР',
            'achievements': 'Провёл форсированную индустриализацию и коллективизацию сельского хозяйства, превратив СССР в мощную промышленную державу. Руководил страной во время Великой Отечественной войны (1941-1945), одержав победу над нацистской Германией. Превратил СССР в ядерную сверхдержаву и одну из двух ведущих мировых держав.',
            'biography': 'Иосиф Виссарионович Джугашвили (Сталин) родился в 1878 году в семье сапожника в Грузии. Учился в духовной семинарии, но был исключён за революционную деятельность. С начала XX века участвовал в революционном движении, неоднократно арестовывался и ссылался. После смерти Ленина в 1924 году в результате внутрипартийной борьбы постепенно сосредоточил в своих руках всю полноту власти. С конца 1920-х годов начал политику форсированной индустриализации - создание тяжёлой промышленности, строительство заводов, электростанций, развитие науки и образования. Одновременно провёл коллективизацию сельского хозяйства - объединение крестьянских хозяйств в колхозы. В 1930-е годы осуществил массовые политические репрессии против действительных и мнимых противников. Во время Великой Отечественной войны как Верховный Главнокомандующий руководил вооружёнными силами СССР. После войны восстановил разрушенную экономику, создал ядерное оружие, расширил влияние СССР в Восточной Европе и Азии.',
            'legacy': 'Сталин превратил СССР в индустриальную сверхдержаву с мощной экономикой и армией. Под его руководством была одержана победа в Великой Отечественной войне. Вместе с тем его правление сопровождалось массовыми репрессиями и нарушениями прав человека. Создал тоталитарную политическую систему и культ личности.',
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
            'birth_place': 'Калиновка, Курская губерния (Россия)',
            'death_year': 1971,
            'death_place': 'Москва',
            'position': 'Первый секретарь ЦК КПСС, Председатель Совета министров СССР',
            'achievements': 'Провёл десталинизацию общества - разоблачил культ личности Сталина и ослабил политические репрессии. Руководил СССР в период Карибского кризиса (1962). Под его руководством СССР запустил первый искусственный спутник Земли (1957) и первого человека в космос - Юрия Гагарина (1961). Начал программу массового жилищного строительства ("хрущёвки").',
            'biography': 'Никита Сергеевич Хрущёв родился в 1894 году в крестьянской семье. Работал слесарем, участвовал в Гражданской войне. Сделал партийную карьеру, руководил Московской партийной организацией, участвовал в индустриализации. Во время войны был членом военных советов на различных фронтах. После смерти Сталина в 1953 году в результате внутрипартийной борьбы стал главой партии и государства. На XX съезде КПСС в 1956 году выступил с докладом о культе личности Сталина, что положило начало процессу десталинизации. Провёл экономические реформы, расширил права союзных республик, улучшил отношения с Западом ("оттепель"). Развивал космическую программу, добившись выдающихся успехов. Начал массовое жилищное строительство, значительно улучшив жилищные условия миллионов советских граждан. В 1962 году пережил острейший международный кризис из-за размещения советских ракет на Кубе. Был снят с должности в 1964 году из-за волюнтаристских решений и неудач в экономике.',
            'legacy': 'Хрущёв начал процесс либерализации советского общества, реабилитировал многих репрессированных, ослабил политический контроль. Превратил СССР в космическую державу. Период его правления известен как "оттепель" - время относительной свободы в культуре и науке.',
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
            'birth_place': 'Каменское (ныне Днепродзержинск), Украина',
            'death_year': 1982,
            'death_place': 'Москва',
            'position': 'Генеральный секретарь ЦК КПСС, Председатель Президиума Верховного Совета СССР',
            'achievements': 'Обеспечил период стабильности и предсказуемости в жизни страны. Укрепил военную мощь СССР, достигнув военно-стратегического паритета с США. Расширил влияние СССР в странах третьего мира. Подписал договоры об ограничении стратегических вооружений (ОСВ-1 и ОСВ-2), Заключительный акт СБСЕ в Хельсинки (1975). Провёл экономические реформы 1965 года (реформа Косыгина).',
            'biography': 'Леонид Ильич Брежнев родился в 1906 году в рабочей семье. Получил инженерное образование, работал на металлургическом заводе. Сделал партийную карьеру на Украине. Во время Великой Отечественной войны служил в политических органах армии, дослужился до генерал-майора. После войны руководил партийными организациями в Молдавии и Казахстане. В 1964 году возглавил заговор против Хрущёва и стал Первым секретарём ЦК КПСС (с 1966 - Генеральным секретарём). Его правление характеризовалось стабильностью и отсутствием резких изменений. Была достигнута политика разрядки с Западом, подписаны важные международные соглашения. Укреплена обороноспособность страны, достигнут военный паритет с США. Однако к концу правления в экономике нарастали застойные явления - замедление темпов роста, дефицит товаров, технологическое отставание от Запада. Усилилась коррупция и бюрократизация. Была создана развитая система социального обеспечения, но свобода слова и инакомыслие подавлялись.',
            'legacy': 'Период правления Брежнева (1964-1982) называют "эпохой застоя" из-за замедления экономического роста и нарастания кризисных явлений. Вместе с тем это была эпоха стабильности и уверенности в завтрашнем дне для большинства граждан. СССР достиг пика своей военной и геополитической мощи.',
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
            'birth_place': 'станция Нагутская (ныне Ставропольский край)',
            'death_year': 1984,
            'death_place': 'Москва',
            'position': 'Генеральный секретарь ЦК КПСС, бывший Председатель КГБ СССР',
            'achievements': 'Начал кампанию по укреплению трудовой дисциплины и борьбе с коррупцией. Провёл экономический эксперимент на пяти промышленных предприятиях для повышения эффективности производства. Усилил борьбу с диссидентством. Попытался начать умеренные экономические реформы, которые позднее были продолжены при Горбачёве.',
            'biography': 'Юрий Владимирович Андропов родился в 1914 году. Начал трудовую деятельность телеграфистом, затем работал на судоверфи. Получил высшее образование заочно. С 1940 года на партийной работе в Карелии. После войны работал в ЦК КПСС по международным вопросам. В 1954-1957 годах - посол в Венгрии, где наблюдал венгерское восстание 1956 года. С 1967 по 1982 год возглавлял КГБ СССР - дольше всех в истории этой организации. Под его руководством КГБ активно боролся с диссидентским движением, но при этом избегал массовых репрессий сталинского типа. После смерти Брежнева в ноябре 1982 года стал Генеральным секретарём ЦК КПСС. Начал кампанию по укреплению дисциплины и порядка, борьбе с коррупцией и нетрудовыми доходами. Провёл чистки партийного аппарата, пытался начать экономические реформы. Однако тяжёлая болезнь не позволила реализовать задуманные планы.',
            'legacy': 'Андропов правил всего 15 месяцев, но успел начать процессы обновления, которые позднее вылились в перестройку. Его попытки укрепления дисциплины и борьбы с коррупцией были популярны в обществе. Считается, что при более длительном правлении мог бы провести умеренные реформы.',
            'short_description': 'Бывший глава КГБ, инициатор борьбы с коррупцией и укрепления дисциплины',
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
            'birth_place': 'село Большая Тёсь, Енисейская губерния (ныне Красноярский край)',
            'death_year': 1985,
            'death_place': 'Москва',
            'position': 'Генеральный секретарь ЦК КПСС, Председатель Президиума Верховного Совета СССР',
            'achievements': 'Продолжил политику своих предшественников, сохраняя консервативный курс. Под его руководством велись переговоры по разоружению с США. Поддерживал стабильность в управлении страной в сложный переходный период. Уделял внимание социальным программам и улучшению условий жизни населения.',
            'biography': 'Константин Устинович Черненко родился в 1911 году в крестьянской семье в Сибири. В юности работал в сельском хозяйстве. Вступил в комсомол, затем в партию. Прошёл путь от рядового партийного работника до руководителя. Большую часть карьеры провёл в партийных органах, занимаясь идеологической работой. С 1960 года работал в аппарате ЦК КПСС. Был близким соратником Брежнева, заведовал Общим отделом ЦК. После смерти Андропова в феврале 1984 года был избран Генеральным секретарём ЦК КПСС, став самым возрастным руководителем СССР (72 года). Его правление продолжалось всего 13 месяцев и было отмечено консерватизмом и продолжением прежней политики. Из-за тяжёлой болезни фактически не мог активно руководить страной. Это был период нарастания кризисных явлений в экономике и ожидания перемен.',
            'legacy': 'Черненко стал последним представителем брежневской "старой гвардии" у власти. Его кратковременное правление рассматривается как переходный период между эпохой застоя и началом перестройки. Не оставил значительного следа в истории из-за краткости правления и тяжёлой болезни.',
            'short_description': 'Последний лидер старой гвардии, переходная фигура перед перестройкой',
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
            'birth_place': 'село Привольное, Ставропольский край',
            'death_year': 2022,
            'death_place': 'Москва',
            'position': 'Генеральный секретарь ЦК КПСС, Президент СССР',
            'achievements': 'Инициировал масштабные реформы "перестройка" и "гласность", которые привели к демократизации общества. Прекратил холодную войну, вывел советские войска из Афганистана. Допустил объединение Германии. Получил Нобелевскую премию мира (1990) за вклад в окончание холодной войны. Ввёл многопартийность и свободу слова. Не смог предотвратить распад СССР, который прекратил существование 26 декабря 1991 года.',
            'biography': 'Михаил Сергеевич Горбачёв родился в 1931 году в крестьянской семье на Ставрополье. Работал механизатором, окончил юридический факультет МГУ. Сделал партийную карьеру в Ставропольском крае. Попал в поле зрения Москвы благодаря поддержке Андропова. В 1978 году стал секретарём ЦК по сельскому хозяйству, в 1980 - членом Политбюро. После смерти Черненко в марте 1985 года был избран Генеральным секретарём ЦК КПСС, став самым молодым руководителем с 1920-х годов (54 года). Начал политику перестройки - реформирования советской системы. Провозгласил курс на гласность (свободу слова), демократизацию и ускорение социально-экономического развития. Начал переговоры с США о сокращении вооружений, улучшил отношения с Западом, что привело к окончанию холодной войны. В 1990 году стал первым и единственным Президентом СССР. Однако реформы привели к экономическому кризису, межнациональным конфликтам и распаду СССР. После путча ГКЧП в августе 1991 года фактически потерял власть. 25 декабря 1991 года объявил о своей отставке.',
            'legacy': 'Горбачёв - одна из самых противоречивых фигур в истории. На Западе его ценят за окончание холодной войны и демократизацию. В России многие винят его в развале СССР и экономическом кризисе 1990-х. Его реформы положили конец советской системе и открыли новую эпоху в истории России и мира.',
            'short_description': 'Последний лидер СССР, инициатор перестройки, лауреат Нобелевской премии мира',
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
