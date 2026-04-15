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
                biography TEXT,
                legacy TEXT,
                short_description TEXT,
                years_in_power_start INTEGER,
                years_in_power_end INTEGER,
                historical_significance INTEGER DEFAULT 5,
                video_id INTEGER,
                portrait_url TEXT
            )
        ''')

        # Add new columns to existing schema if they don't exist
        columns_to_add = [
            ('biography', 'TEXT'),
            ('legacy', 'TEXT'),
            ('short_description', 'TEXT'),
            ('years_in_power_start', 'INTEGER'),
            ('years_in_power_end', 'INTEGER'),
            ('historical_significance', 'INTEGER DEFAULT 5'),
        ]
        existing = {row[1] for row in cursor.execute("PRAGMA table_info(leaders)")}
        for col, col_type in columns_to_add:
            if col not in existing:
                cursor.execute(f'ALTER TABLE leaders ADD COLUMN {col} {col_type}')

        conn.commit()
        conn.close()

    def initialize_data(self):
        """Initialize database with USSR leaders data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        existing = {row[1] for row in cursor.execute("PRAGMA table_info(leaders)")}
        if 'portrait_url' not in existing:
            cursor.execute('ALTER TABLE leaders ADD COLUMN portrait_url TEXT')

        # Check if data already exists
        cursor.execute('SELECT COUNT(*) FROM leaders')
        if cursor.fetchone()[0] > 0:
            # Update existing rows with new fields if they are NULL
            self._update_extended_fields(cursor)
            conn.commit()
            conn.close()
            return

        leaders_data = self._get_leaders_data()

        for leader in leaders_data:
            cursor.execute('''
                INSERT INTO leaders (
                    id, name_ru, name_en, birth_year, birth_place,
                    death_year, death_place, position, achievements,
                    biography, legacy, short_description,
                    years_in_power_start, years_in_power_end,
                    historical_significance, video_id, portrait_url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                leader['id'], leader['name_ru'], leader['name_en'],
                leader['birth_year'], leader['birth_place'],
                leader['death_year'], leader['death_place'],
                leader['position'], leader['achievements'],
                leader.get('biography'), leader.get('legacy'),
                leader.get('short_description'),
                leader.get('years_in_power_start'),
                leader.get('years_in_power_end'),
                leader.get('historical_significance', 5),
                leader['video_id'],
                leader.get('portrait_url')
            ))

        conn.commit()
        conn.close()

    def _update_extended_fields(self, cursor):
        """Update existing rows with extended data fields"""
        leaders_data = self._get_leaders_data()
        for leader in leaders_data:
            cursor.execute('''
                UPDATE leaders SET
                    biography = COALESCE(biography, ?),
                    legacy = COALESCE(legacy, ?),
                    short_description = COALESCE(short_description, ?),
                    years_in_power_start = COALESCE(years_in_power_start, ?),
                    years_in_power_end = COALESCE(years_in_power_end, ?),
                    historical_significance = COALESCE(historical_significance, ?),
                    portrait_url = COALESCE(portrait_url, ?)
                WHERE id = ?
            ''', (
                leader.get('biography'),
                leader.get('legacy'),
                leader.get('short_description'),
                leader.get('years_in_power_start'),
                leader.get('years_in_power_end'),
                leader.get('historical_significance', 5),
                leader.get('portrait_url'),
                leader['id']
            ))

    def _get_leaders_data(self):
        """Return full leaders data including extended fields"""
        return [
            {
                'id': 1,
                'name_ru': 'Владимир Ильич Ленин',
                'name_en': 'Vladimir Ilyich Lenin',
                'birth_year': 1870,
                'birth_place': 'Симбирск',
                'death_year': 1924,
                'death_place': 'под Москвой',
                'position': 'Председатель Совета народных комиссаров',
                'achievements': 'Организовал Октябрьскую революцию и создал первое в мире социалистическое государство. Заложил основы советской государственности, провёл национализацию промышленности и заключил Брестский мир.',
                'biography': (
                    'Владимир Ильич Ульянов (Ленин) родился в 1870 году в Симбирске в семье инспектора '
                    'народных училищ. Окончил юридический факультет Казанского университета. '
                    'После казни старшего брата Александра за участие в заговоре против царя '
                    'встал на путь революционной борьбы. Создал партию большевиков и в 1917 году '
                    'возглавил Октябрьскую революцию. Стал первым руководителем советского государства, '
                    'провёл радикальные реформы в экономике и политике. Скончался в 1924 году, оставив '
                    'после себя обширное теоретическое наследие.'
                ),
                'legacy': (
                    'Ленин стал основателем первого в мире государства, провозгласившего целью построение '
                    'социализма. Его идеи повлияли на политические движения по всему миру. Тело вождя '
                    'было сохранено в мавзолее на Красной площади. Ленинизм как политическая идеология '
                    'определял курс СССР на протяжении всей его истории.'
                ),
                'short_description': 'Основатель советского государства и вождь Октябрьской революции',
                'years_in_power_start': 1917,
                'years_in_power_end': 1924,
                'historical_significance': 10,
                'video_id': 1,
                'portrait_url': 'https://upload.wikimedia.org/wikipedia/commons/7/79/Vladimir_Lenin.jpg'
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
                'achievements': (
                    'Провёл индустриализацию и коллективизацию страны, превратив СССР в '
                    'промышленную державу. Одержал победу во Второй мировой войне и сделал СССР '
                    'ядерной сверхдержавой. Создал разветвлённый государственный аппарат управления.'
                ),
                'biography': (
                    'Иосиф Джугашвили родился в 1878 году в грузинском городе Гори. Учился в '
                    'православной семинарии, но был отчислен. Вступив в революционное движение, '
                    'неоднократно арестовывался и ссылался. После революции 1917 года вошёл '
                    'в ближайшее окружение Ленина. К концу 1920-х годов сосредоточил в своих '
                    'руках всю полноту власти и установил тоталитарный режим. Провёл масштабные '
                    'репрессии, унёсшие жизни миллионов людей. В годы Великой Отечественной войны '
                    'лично руководил военными операциями. Скончался в марте 1953 года.'
                ),
                'legacy': (
                    'Сталин остаётся самой противоречивой фигурой советской истории. Индустриализация '
                    'и победа во Второй мировой войне — с одной стороны, репрессии и ГУЛАГ — '
                    'с другой. Его правление изменило облик СССР и всего мирового порядка XX века. '
                    'Дискуссии о его роли не утихают по сей день.'
                ),
                'short_description': 'Генеральный секретарь, вождь советского народа в годы Второй мировой войны',
                'years_in_power_start': 1924,
                'years_in_power_end': 1953,
                'historical_significance': 10,
                'video_id': 2,
                'portrait_url': 'https://upload.wikimedia.org/wikipedia/commons/3/38/Stalin_Full_Image.jpg'
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
                'achievements': (
                    'Провёл десталинизацию и значительно ослабил политические репрессии. '
                    'Запустил советскую космическую программу — Спутник и первый полёт человека в космос. '
                    'Инициировал массовое жилищное строительство («хрущёвки»). '
                    'Первым из советских лидеров посетил США.'
                ),
                'biography': (
                    'Никита Хрущёв родился в крестьянской семье в Калиновке. Получив лишь начальное '
                    'образование, он сделал карьеру через партийные структуры. В 1938 году стал '
                    'первым секретарём Украины. После смерти Сталина в 1953 году выдвинулся на '
                    'первые позиции в партии. В 1956 году на XX съезде КПСС произнёс знаменитый '
                    '«Секретный доклад» о преступлениях сталинизма. Его правление ознаменовалось '
                    '«оттепелью» — либерализацией общественной жизни. В октябре 1964 года был '
                    'отстранён от власти в результате заговора коллег.'
                ),
                'legacy': (
                    'Хрущёв дал толчок советской космической программе и положил конец наиболее '
                    'жестоким формам сталинского террора. «Оттепель» открыла пространство для '
                    'культурного самовыражения. Вместе с тем его политика отличалась '
                    'непоследовательностью: провал сельскохозяйственных реформ и Карибский кризис '
                    'стали серьёзными испытаниями для страны.'
                ),
                'short_description': 'Инициатор оттепели и десталинизации, покоритель космоса',
                'years_in_power_start': 1953,
                'years_in_power_end': 1964,
                'historical_significance': 8,
                'video_id': 3,
                'portrait_url': 'https://upload.wikimedia.org/wikipedia/commons/7/70/Nikita_Khrushchev_1963.jpg'
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
                'achievements': (
                    'Обеспечил длительный период внутренней стабильности. Достиг паритета с США '
                    'в области ядерного оружия. Укрепил военную мощь и расширил международное '
                    'влияние СССР. Подписал Хельсинкские соглашения об основах европейской '
                    'безопасности.'
                ),
                'biography': (
                    'Леонид Брежнев родился в Каменском (ныне Днепродзержинск) в рабочей семье. '
                    'В годы Великой Отечественной войны служил политработником. Стремительно '
                    'поднявшись по партийной лестнице, в 1964 году возглавил заговор против '
                    'Хрущёва и занял пост Генерального секретаря. Правил страной 18 лет — '
                    'дольше всех советских лидеров после Сталина. В последние годы жизни '
                    'страдал тяжёлыми недугами, что предопределило «геронтократию» позднего СССР.'
                ),
                'legacy': (
                    'Эпоха Брежнева вошла в историю как «период застоя» — время относительного '
                    'потребительского благополучия при нарастающем экономическом и идеологическом '
                    'кризисе. Доктрина Брежнева (о праве СССР вмешиваться во внутренние дела '
                    'социалистических стран) привела к вводу войск в Чехословакию (1968) и '
                    'Афганистан (1979).'
                ),
                'short_description': 'Символ эпохи стабильности и «застоя», руководивший страной 18 лет',
                'years_in_power_start': 1964,
                'years_in_power_end': 1982,
                'historical_significance': 7,
                'video_id': 4,
                'portrait_url': 'https://upload.wikimedia.org/wikipedia/commons/6/68/RIAN_archive_850809_Leonid_Brezhnev.jpg'
            },
            {
                'id': 5,
                'name_ru': 'Юрий Владимирович Андропов',
                'name_en': 'Yuri Vladimirovich Andropov',
                'birth_year': 1914,
                'birth_place': 'село Нагутское (Россия)',
                'death_year': 1984,
                'death_place': 'Москва',
                'position': 'Генеральный секретарь ЦК КПСС, бывший председатель КГБ',
                'achievements': (
                    'Начал кампанию по борьбе с коррупцией и укреплению трудовой дисциплины. '
                    'Предпринял первые попытки экономических реформ. Выдвинул в политбюро '
                    'молодых реформаторов — в том числе Михаила Горбачёва.'
                ),
                'biography': (
                    'Юрий Андропов работал комсомольским и партийным функционером, в 1967 году '
                    'возглавил КГБ СССР, которым руководил 15 лет. Прославился эффективными '
                    'операциями против диссидентов и иностранных спецслужб. После смерти '
                    'Брежнева в 1982 году занял пост Генерального секретаря, но руководил '
                    'страной лишь 15 месяцев: тяжёлая болезнь почек не позволила ему реализовать '
                    'задуманные преобразования. Скончался в феврале 1984 года.'
                ),
                'legacy': (
                    'Несмотря на краткость правления, Андропов запомнился как человек, '
                    'попытавшийся встряхнуть погрязшую в коррупции систему. Он привлёк к власти '
                    'новое поколение политиков, в том числе Горбачёва, что предопределило '
                    'будущие реформы. Многие историки задаются вопросом: каким был бы СССР, '
                    'доживи Андропов до полноценного срока?'
                ),
                'short_description': 'Бывший шеф КГБ, начавший борьбу с коррупцией и выдвинувший реформаторов',
                'years_in_power_start': 1982,
                'years_in_power_end': 1984,
                'historical_significance': 6,
                'video_id': 5,
                'portrait_url': 'https://upload.wikimedia.org/wikipedia/commons/2/25/Yuri_Andropov_1974.jpg'
            },
            {
                'id': 6,
                'name_ru': 'Константин Устинович Черненко',
                'name_en': 'Konstantin Ustinovich Chernenko',
                'birth_year': 1911,
                'birth_place': 'село Большая Тесь (Россия)',
                'death_year': 1985,
                'death_place': 'Москва',
                'position': 'Генеральный секретарь ЦК КПСС',
                'achievements': (
                    'Поддерживал стабильность государственной системы в переходный период. '
                    'Продолжал политику Брежнева. Организовал бойкот Олимпийских игр в '
                    'Лос-Анджелесе в 1984 году. Скончался после 13 месяцев у власти.'
                ),
                'biography': (
                    'Константин Черненко происходил из Сибири, начинал рядовым пограничником. '
                    'Сблизился с Брежневым в годы работы в Молдавии и стал его ближайшим '
                    'политическим союзником. После смерти Андропова в 1984 году, несмотря на '
                    'тяжёлую болезнь лёгких, был избран Генеральным секретарём как компромиссная '
                    'фигура партийного консерватизма. Его краткое правление (13 месяцев) '
                    'воспринималось современниками как символ дряхления советской системы.'
                ),
                'legacy': (
                    'Черненко стал последним советским лидером «старой закалки»: его правление '
                    'наглядно показало, что система нуждается в радикальном обновлении. '
                    'После его смерти к власти пришёл значительно более молодой Горбачёв, '
                    'открывший эпоху перестройки. Три Генеральных секретаря за три года '
                    '(Брежнев, Андропов, Черненко) стали символом кризиса советского '
                    'геронтократического правления.'
                ),
                'short_description': 'Последний из советских лидеров старой закалки, правивший 13 месяцев',
                'years_in_power_start': 1984,
                'years_in_power_end': 1985,
                'historical_significance': 4,
                'video_id': 6,
                'portrait_url': 'https://upload.wikimedia.org/wikipedia/commons/7/7a/Konstantin_Chernenko_1985.jpg'
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
                'achievements': (
                    'Провёл политику «гласности» (свободы слова) и «перестройки» (экономических '
                    'реформ). Завершил холодную войну и вывел советские войска из Афганистана. '
                    'Получил Нобелевскую премию мира в 1990 году. Допустил '
                    'демократизацию политической жизни.'
                ),
                'biography': (
                    'Михаил Горбачёв вырос в крестьянской семье на Ставрополье. Окончил '
                    'юридический факультет МГУ. Сделал стремительную партийную карьеру — '
                    'во многом благодаря поддержке Андропова. В марте 1985 года избран '
                    'Генеральным секретарём. Провозгласил курс на перестройку и гласность, '
                    'открыв СССР навстречу свободному слову и рыночным отношениям. '
                    'В 1991 году подписал Беловежские соглашения, юридически оформившие '
                    'распад СССР, и в декабре того же года сложил полномочия президента.'
                ),
                'legacy': (
                    'Горбачёв — самая противоречивая фигура позднесоветской истории. '
                    'На Западе он чтится как человек, покончивший с холодной войной и '
                    'освободивший Восточную Европу. В России его оценки диаметрально '
                    'противоположны: одни считают его реформатором, другие — виновником '
                    'распада СССР. Нобелевская премия мира, полученная им в 1990 году, '
                    'отразила его роль в прекращении ядерного противостояния.'
                ),
                'short_description': 'Архитектор перестройки, завершивший холодную войну и Нобелевский лауреат',
                'years_in_power_start': 1985,
                'years_in_power_end': 1991,
                'historical_significance': 9,
                'video_id': 7,
                'portrait_url': 'https://upload.wikimedia.org/wikipedia/commons/5/59/Gorbachev_1987.jpg'
            },
            {
                'id': 8,
                'name_ru': 'Георгий Константинович Жуков',
                'name_en': 'Georgy Konstantinovich Zhukov',
                'birth_year': 1896,
                'birth_place': 'Стрелковка (Россия)',
                'death_year': 1974,
                'death_place': 'Москва',
                'position': 'Маршал Советского Союза, заместитель министра обороны СССР',
                'achievements': (
                    'Координировал ключевые операции Великой Отечественной войны, включая оборону Москвы, '
                    'Сталинград, Курскую битву и штурм Берлина. Стал одним из главных символов военной '
                    'победы СССР.'
                ),
                'biography': (
                    'Георгий Жуков происходил из крестьянской семьи и служил в царской армии, а затем '
                    'сделал карьеру в Красной армии. Во время Второй мировой войны возглавлял фронты и '
                    'ставку по наиболее критическим направлениям. После войны занимал высокие посты в '
                    'министерстве обороны, периодически попадая в политическую опалу.'
                ),
                'legacy': (
                    'Жуков остался в памяти как наиболее известный полководец СССР XX века. Его военная '
                    'репутация превратилась в часть государственного мифа о победе, а мемуары стали одним '
                    'из важнейших свидетельств эпохи.'
                ),
                'short_description': 'Маршал Победы и главный символ советского военного триумфа',
                'years_in_power_start': 1941,
                'years_in_power_end': 1945,
                'historical_significance': 9,
                'video_id': 8,
                'portrait_url': 'https://upload.wikimedia.org/wikipedia/commons/f/f7/Zhukov_LIFE.jpg'
            },
            {
                'id': 9,
                'name_ru': 'Юрий Алексеевич Гагарин',
                'name_en': 'Yuri Alekseyevich Gagarin',
                'birth_year': 1934,
                'birth_place': 'Клушино (Россия)',
                'death_year': 1968,
                'death_place': 'Киржачский район',
                'position': 'Лётчик-космонавт СССР, Герой Советского Союза',
                'achievements': (
                    '12 апреля 1961 года первым в истории человечества совершил орбитальный полёт в '
                    'космос на корабле «Восток-1», став глобальным символом научного прорыва СССР.'
                ),
                'biography': (
                    'Юрий Гагарин родился в Смоленской области, окончил ремесленное училище и Оренбургское '
                    'лётное училище. После отбора в первый отряд космонавтов прошёл интенсивную подготовку '
                    'и был выбран для первого пилотируемого старта.'
                ),
                'legacy': (
                    'Гагарин стал лицом советской космической мечты и одной из самых узнаваемых фигур '
                    'Холодной войны. Его образ использовался как доказательство технологического лидерства СССР.'
                ),
                'short_description': 'Первый космонавт планеты и главное лицо советского космического рывка',
                'years_in_power_start': 1961,
                'years_in_power_end': 1961,
                'historical_significance': 10,
                'video_id': 9,
                'portrait_url': 'https://upload.wikimedia.org/wikipedia/commons/6/6f/Yuri_Gagarin_%281961%29.jpg'
            },
            {
                'id': 10,
                'name_ru': 'Сергей Павлович Королёв',
                'name_en': 'Sergei Pavlovich Korolev',
                'birth_year': 1907,
                'birth_place': 'Житомир',
                'death_year': 1966,
                'death_place': 'Москва',
                'position': 'Главный конструктор советской космической программы',
                'achievements': (
                    'Руководил созданием ракеты Р-7, запуском первого спутника и программой первых '
                    'пилотируемых космических полётов, обеспечив СССР лидерство в ранней космической гонке.'
                ),
                'biography': (
                    'Сергей Королёв получил инженерное образование, пережил арест и лагеря в конце 1930-х, '
                    'после чего был возвращён к работе в оборонной промышленности. После войны возглавил '
                    'ключевые ракетно-космические проекты страны.'
                ),
                'legacy': (
                    'Королёв стал архитектором советской космической программы. Его имя долгое время '
                    'оставалось засекреченным, но именно он сформировал технологическую базу советских '
                    'космических побед.'
                ),
                'short_description': 'Главный конструктор, превративший СССР в космическую сверхдержаву',
                'years_in_power_start': 1957,
                'years_in_power_end': 1966,
                'historical_significance': 9,
                'video_id': 10,
                'portrait_url': 'https://upload.wikimedia.org/wikipedia/commons/e/e0/Sergey_Korolyov.jpg'
            },
            {
                'id': 11,
                'name_ru': 'Валентина Владимировна Терешкова',
                'name_en': 'Valentina Vladimirovna Tereshkova',
                'birth_year': 1937,
                'birth_place': 'Большое Масленниково (Россия)',
                'death_year': None,
                'death_place': None,
                'position': 'Лётчик-космонавт СССР, первая женщина-космонавт',
                'achievements': (
                    'В 1963 году совершила полёт на корабле «Восток-6» и стала первой женщиной в космосе, '
                    'укрепив образ СССР как лидера в освоении космоса и социального прогресса.'
                ),
                'biography': (
                    'Валентина Терешкова работала на текстильной фабрике и занималась парашютным спортом, '
                    'что привело её в отряд космонавтов. После исторического полёта стала мировой знаменитостью '
                    'и участвовала в общественно-политической жизни страны.'
                ),
                'legacy': (
                    'Терешкова стала важнейшей фигурой советской визуальной и политической пропаганды 1960-х. '
                    'Её полёт символизировал открытие космоса не только для мужчин, но и для женщин.'
                ),
                'short_description': 'Первая женщина в космосе и символ советского технологического оптимизма',
                'years_in_power_start': 1963,
                'years_in_power_end': 1963,
                'historical_significance': 8,
                'video_id': 11,
                'portrait_url': 'https://upload.wikimedia.org/wikipedia/commons/0/00/RIAN_archive_612748_Valentina_Tereshkova.jpg'
            },
            {
                'id': 12,
                'name_ru': 'Алексей Григорьевич Стаханов',
                'name_en': 'Alexey Grigoryevich Stakhanov',
                'birth_year': 1906,
                'birth_place': 'Орловская губерния',
                'death_year': 1977,
                'death_place': 'Торез',
                'position': 'Шахтёр, символ стахановского движения',
                'achievements': (
                    'Рекордной добычей угля в 1935 году дал имя массовому движению за перевыполнение норм, '
                    'которое стало одним из ключевых трудовых мифов сталинской индустриализации.'
                ),
                'biography': (
                    'Алексей Стаханов работал на шахтах Донбасса. После публикации его рекорда советская '
                    'пресса превратила шахтёра в модель нового социалистического героя труда.'
                ),
                'legacy': (
                    'Имя Стаханова стало нарицательным для ударного труда и дисциплины. Его образ десятилетиями '
                    'использовался на плакатах, в кинохронике и производственной агитации.'
                ),
                'short_description': 'Лицо трудового героизма и главный персонаж индустриальной пропаганды 1930-х',
                'years_in_power_start': 1935,
                'years_in_power_end': 1935,
                'historical_significance': 7,
                'video_id': 12,
                'portrait_url': 'https://upload.wikimedia.org/wikipedia/commons/2/2d/Alexey_Stakhanov.jpg'
            }
        ]

    def get_all_leaders(self):
        """Get all leaders from database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM leaders ORDER BY id')

        leaders = []
        for row in cursor.fetchall():
            leader = dict(row)
            # Add years_in_power nested object for JS compatibility
            if leader.get('years_in_power_start'):
                leader['years_in_power'] = {
                    'start': leader['years_in_power_start'],
                    'end': leader.get('years_in_power_end')
                }
            leaders.append(leader)

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
            leader = dict(row)
            if leader.get('years_in_power_start'):
                leader['years_in_power'] = {
                    'start': leader['years_in_power_start'],
                    'end': leader.get('years_in_power_end')
                }
            return leader
        return None
