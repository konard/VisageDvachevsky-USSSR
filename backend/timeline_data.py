"""Chronology of significant events 1917-1991 used by /api/timeline."""

# Each event:
#   year, month (optional), title, description, category, leader_ids
# Categories mirror the leader categories so the same colour-coding can be reused.
EVENTS = [
    {
        'year': 1917, 'month': 11,
        'title': 'Октябрьская революция',
        'description': 'Большевики во главе с Лениным взяли власть в Петрограде.',
        'category': 'politics', 'leader_ids': [1]
    },
    {
        'year': 1918, 'month': 3,
        'title': 'Брестский мир',
        'description': 'Советская Россия вышла из Первой мировой войны.',
        'category': 'politics', 'leader_ids': [1, 31]
    },
    {
        'year': 1919, 'month': 11,
        'title': 'Первая конная Будённого',
        'description': 'Кавалерийский корпус развёрнут в Первую конную армию.',
        'category': 'military', 'leader_ids': [32]
    },
    {
        'year': 1922, 'month': 12,
        'title': 'Образование СССР',
        'description': 'Подписан Договор об образовании Союза ССР из четырёх республик.',
        'category': 'politics', 'leader_ids': [1, 30]
    },
    {
        'year': 1924, 'month': 1,
        'title': 'Смерть Ленина',
        'description': 'Скончался в Горках 21 января, мумия выставлена в Мавзолее.',
        'category': 'politics', 'leader_ids': [1, 2]
    },
    {
        'year': 1929,
        'title': 'Старт первой пятилетки',
        'description': 'Запущена форсированная индустриализация и коллективизация.',
        'category': 'politics', 'leader_ids': [2]
    },
    {
        'year': 1933,
        'title': 'Дрейф «Челюскина» и зарождение полярной эпопеи',
        'description': 'Папанин и полярники Главсевморпути готовят дрейфующие станции.',
        'category': 'labor', 'leader_ids': [34]
    },
    {
        'year': 1935, 'month': 8,
        'title': 'Рекорд Стаханова',
        'description': 'В шахте «Центральная-Ирмино» за смену добыто 102 тонны угля.',
        'category': 'labor', 'leader_ids': [12]
    },
    {
        'year': 1936, 'month': 12,
        'title': 'Сталинская конституция',
        'description': 'Принят новый Основной Закон СССР с декларацией прав граждан.',
        'category': 'politics', 'leader_ids': [2, 30, 31]
    },
    {
        'year': 1937, 'month': 5,
        'title': 'Дрейфующая станция «Северный полюс-1»',
        'description': 'Папанин с тремя товарищами высажен у Северного полюса.',
        'category': 'labor', 'leader_ids': [34]
    },
    {
        'year': 1937, 'month': 6,
        'title': 'Перелёт Чкалова через полюс',
        'description': 'Москва — Северный полюс — Ванкувер за 63 часа.',
        'category': 'science', 'leader_ids': [33]
    },
    {
        'year': 1938, 'month': 8,
        'title': 'Открытие сверхтекучести',
        'description': 'Пётр Капица обнаружил сверхтекучесть гелия-II.',
        'category': 'science', 'leader_ids': [26, 27]
    },
    {
        'year': 1939, 'month': 8,
        'title': 'Пакт Молотова — Риббентропа',
        'description': 'Подписан советско-германский договор о ненападении.',
        'category': 'politics', 'leader_ids': [2, 31]
    },
    {
        'year': 1941, 'month': 6,
        'title': 'Начало Великой Отечественной',
        'description': '22 июня нацистская Германия напала на СССР.',
        'category': 'military', 'leader_ids': [2, 8, 31]
    },
    {
        'year': 1941, 'month': 12,
        'title': 'Битва под Москвой',
        'description': 'Контрнаступление советских войск отбросило вермахт от столицы.',
        'category': 'military', 'leader_ids': [8, 24]
    },
    {
        'year': 1943, 'month': 2,
        'title': 'Сталинградская победа',
        'description': 'Капитуляция 6-й армии Паулюса — перелом войны.',
        'category': 'military', 'leader_ids': [8, 24]
    },
    {
        'year': 1945, 'month': 5,
        'title': 'День Победы',
        'description': '9 мая — Акт о капитуляции Германии подписан в Берлине.',
        'category': 'military', 'leader_ids': [2, 8, 24]
    },
    {
        'year': 1947, 'month': 7,
        'title': 'Принят на вооружение АК-47',
        'description': 'Автомат Калашникова стал основным стрелковым оружием армии.',
        'category': 'military', 'leader_ids': [21]
    },
    {
        'year': 1948, 'month': 8,
        'title': 'Сессия ВАСХНИЛ и разгром генетики',
        'description': 'Лысенко объявил классическую генетику «буржуазной лженаукой».',
        'category': 'science', 'leader_ids': [35]
    },
    {
        'year': 1949, 'month': 8,
        'title': 'Первое испытание советской атомной бомбы',
        'description': 'РДС-1 успешно испытан на Семипалатинском полигоне.',
        'category': 'science', 'leader_ids': [14, 13]
    },
    {
        'year': 1953, 'month': 3,
        'title': 'Смерть Сталина',
        'description': 'Скончался на Ближней даче в Кунцево, начался конец эпохи.',
        'category': 'politics', 'leader_ids': [2, 3]
    },
    {
        'year': 1956, 'month': 2,
        'title': '«Секретный доклад» Хрущёва',
        'description': 'XX съезд КПСС: разоблачение культа личности Сталина.',
        'category': 'politics', 'leader_ids': [3]
    },
    {
        'year': 1957, 'month': 10,
        'title': 'Запуск первого спутника',
        'description': 'СССР открыл космическую эру: Спутник-1 на орбите Земли.',
        'category': 'space', 'leader_ids': [10]
    },
    {
        'year': 1961, 'month': 4,
        'title': 'Полёт Гагарина',
        'description': '12 апреля — первый полёт человека в космос на «Востоке».',
        'category': 'space', 'leader_ids': [9, 10]
    },
    {
        'year': 1962, 'month': 10,
        'title': 'Карибский кризис',
        'description': 'Ракеты на Кубе чуть не привели мир к ядерной войне.',
        'category': 'politics', 'leader_ids': [3]
    },
    {
        'year': 1962, 'month': 11,
        'title': '«Один день Ивана Денисовича»',
        'description': 'Журнал «Новый мир» напечатал повесть Солженицына.',
        'category': 'culture', 'leader_ids': [22]
    },
    {
        'year': 1963, 'month': 6,
        'title': 'Полёт Терешковой',
        'description': '16 июня — первая женщина в космосе на корабле «Восток-6».',
        'category': 'space', 'leader_ids': [11]
    },
    {
        'year': 1964, 'month': 10,
        'title': 'Отставка Хрущёва',
        'description': 'Пленум ЦК освободил Хрущёва, к власти пришёл Брежнев.',
        'category': 'politics', 'leader_ids': [3, 4]
    },
    {
        'year': 1965, 'month': 3,
        'title': 'Выход в открытый космос',
        'description': '18 марта — Алексей Леонов вышел из «Восхода-2» в скафандре.',
        'category': 'space', 'leader_ids': [23]
    },
    {
        'year': 1973,
        'title': 'Выход «Архипелага ГУЛАГ»',
        'description': 'В Париже опубликован первый том исследования Солженицына.',
        'category': 'culture', 'leader_ids': [22]
    },
    {
        'year': 1975, 'month': 7,
        'title': 'Союз — Аполлон',
        'description': 'Первая международная стыковка: Леонов и советский экипаж.',
        'category': 'space', 'leader_ids': [23]
    },
    {
        'year': 1978,
        'title': 'Нобелевская премия Капицы',
        'description': 'За исследования в области физики низких температур.',
        'category': 'science', 'leader_ids': [26]
    },
    {
        'year': 1980, 'month': 1,
        'title': 'Ссылка Сахарова в Горький',
        'description': 'Академик отправлен в ссылку за протест против ввода войск в Афганистан.',
        'category': 'science', 'leader_ids': [13]
    },
    {
        'year': 1982, 'month': 11,
        'title': 'Смерть Брежнева',
        'description': 'Эпоха застоя завершилась, к власти пришёл Андропов.',
        'category': 'politics', 'leader_ids': [4, 5]
    },
    {
        'year': 1985, 'month': 3,
        'title': 'Перестройка',
        'description': 'Горбачёв провозгласил курс на ускорение и гласность.',
        'category': 'politics', 'leader_ids': [7]
    },
    {
        'year': 1986, 'month': 4,
        'title': 'Авария на Чернобыльской АЭС',
        'description': '26 апреля — крупнейшая техногенная катастрофа XX века.',
        'category': 'science', 'leader_ids': [7]
    },
    {
        'year': 1989, 'month': 5,
        'title': 'I Съезд народных депутатов',
        'description': 'Первый свободно избранный парламент СССР, дебаты в прямом эфире.',
        'category': 'politics', 'leader_ids': [7, 13]
    },
    {
        'year': 1991, 'month': 12,
        'title': 'Распад СССР',
        'description': 'Беловежские соглашения завершили историю Союза.',
        'category': 'politics', 'leader_ids': [7]
    },
]


def get_timeline():
    """Return the canonical timeline of events sorted chronologically."""
    sorted_events = sorted(
        EVENTS,
        key=lambda e: (e.get('year', 0), e.get('month') or 0),
    )
    return list(sorted_events)
