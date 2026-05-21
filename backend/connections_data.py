"""Static graph of historical relationships used by /api/connections.

Edges describe pairs of personalities from the roster and their relationship
type (`type` field).  The graph is intentionally curated, not auto-generated,
so each link can be verified by a historian.
"""

# Type code -> display label (Russian).
LINK_TYPES = {
    'successor':       'преемник',
    'colleague':       'соратник',
    'mentor':          'наставник',
    'student':         'ученик',
    'team':            'команда',
    'rival':           'оппонент',
    'family':          'семья',
    'commander':       'подчинение',
}

EDGES = [
    # Кремлёвские генсеки — преемственность во главе государства.
    {'source': 1,  'target': 2,  'type': 'successor', 'label': 'Сталин — преемник Ленина'},
    {'source': 2,  'target': 3,  'type': 'successor', 'label': 'Хрущёв пришёл к власти после смерти Сталина'},
    {'source': 3,  'target': 4,  'type': 'successor', 'label': 'Брежнев сменил Хрущёва в 1964 году'},
    {'source': 4,  'target': 5,  'type': 'successor', 'label': 'Андропов возглавил партию после Брежнева'},
    {'source': 5,  'target': 6,  'type': 'successor', 'label': 'Черненко пришёл после Андропова'},
    {'source': 6,  'target': 7,  'type': 'successor', 'label': 'Горбачёв сменил Черненко'},

    # Соратники и оппоненты Сталина.
    {'source': 2,  'target': 30, 'type': 'colleague', 'label': 'Калинин — формальный глава государства при Сталине'},
    {'source': 2,  'target': 31, 'type': 'colleague', 'label': 'Молотов — глава правительства и НКИД'},
    {'source': 2,  'target': 8,  'type': 'commander','label': 'Жуков — Верховный главком и его маршал'},
    {'source': 2,  'target': 32, 'type': 'commander','label': 'Будённый — один из первых маршалов СССР'},

    # Военная команда Второй мировой.
    {'source': 8,  'target': 24, 'type': 'team',     'label': 'Жуков и Рокоссовский — командующие фронтов'},
    {'source': 8,  'target': 32, 'type': 'colleague','label': 'Жуков и Будённый прошли вместе Первую конную'},
    {'source': 32, 'target': 24, 'type': 'colleague','label': 'Маршалы Гражданской и Великой Отечественной'},

    # Космическая команда — конструкторы и космонавты.
    {'source': 10, 'target': 9,  'type': 'mentor',   'label': 'Королёв подготовил первый отряд космонавтов'},
    {'source': 10, 'target': 11, 'type': 'mentor',   'label': 'Королёв одобрил полёт Терешковой'},
    {'source': 10, 'target': 23, 'type': 'mentor',   'label': 'Королёв вёл программу «Восход» с Леоновым'},
    {'source': 9,  'target': 11, 'type': 'team',     'label': 'Гагарин и Терешкова — первый и шестая в космосе'},
    {'source': 9,  'target': 23, 'type': 'team',     'label': 'Гагарин и Леонов — первый отряд космонавтов'},
    {'source': 11, 'target': 23, 'type': 'team',     'label': 'Терешкова и Леонов — отряд «Звёздного городка»'},

    # Атомный проект.
    {'source': 14, 'target': 13, 'type': 'mentor',   'label': 'Курчатов привлёк Сахарова к работе над термоядерным оружием'},
    {'source': 14, 'target': 26, 'type': 'colleague','label': 'Курчатов и Капица — лидеры физики 1940-х'},

    # Физическая школа Капицы — Ландау.
    {'source': 26, 'target': 27, 'type': 'mentor',   'label': 'Капица пригласил Ландау в Институт физических проблем'},
    {'source': 27, 'target': 13, 'type': 'colleague','label': 'Ландау и Сахаров — теоретики Института'},

    # Авиаконструктор и испытатель.
    {'source': 25, 'target': 33, 'type': 'team',     'label': 'Туполев и Чкалов: связка КБ и испытательной бригады'},

    # Культурный круг 1960-х.
    {'source': 18, 'target': 29, 'type': 'colleague','label': 'Высоцкий и Окуджава — авторская песня'},
    {'source': 22, 'target': 36, 'type': 'colleague','label': 'Солженицын и Ахматова обменивались письмами'},
    {'source': 15, 'target': 22, 'type': 'colleague','label': 'Шостакович и Солженицын — фигуры культурной оппозиции'},

    # Сцены Большого: балет и кино.
    {'source': 28, 'target': 20, 'type': 'mentor',   'label': 'Уланова стала наставницей Плисецкой и поколения после неё'},
    {'source': 16, 'target': 15, 'type': 'colleague','label': 'Эйзенштейн и Шостакович — совместная работа над фильмами'},

    # Полярники, стахановцы, лысенковщина — социально-экономический контур.
    {'source': 12, 'target': 34, 'type': 'colleague','label': 'Стаханов и Папанин — символы трудового подвига 1930-х'},
    {'source': 35, 'target': 14, 'type': 'rival',    'label': 'Лысенко противостоял Курчатову и научному истеблишменту'},

    # Литература и Гулаг.
    {'source': 22, 'target': 17, 'type': 'rival',    'label': 'Солженицын и Шолохов — спор о подлинности «Тихого Дона»'},
]

# Curated set of nodes that appear in the graph (subset of full roster
# to keep the visualisation readable).
NODE_IDS = sorted({eid for edge in EDGES for eid in (edge['source'], edge['target'])})


def get_connections():
    """Return graph payload: nodes (ids) + edges + link-type legend."""
    return {
        'node_ids': NODE_IDS,
        'edges': EDGES,
        'link_types': LINK_TYPES,
    }
