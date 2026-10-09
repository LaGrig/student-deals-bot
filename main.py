import os
import json
import time
import re
import html
from urllib.parse import urlparse
import feedparser
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
HISTORY_FILE = "data/processed_ids.json"
ACTIVE_POSTS_FILE = "data/active_posts.json"

CHANNEL_USERNAME = TELEGRAM_CHAT_ID.replace("@", "") if TELEGRAM_CHAT_ID else "discounts4students"

# 24 выверенные программы: полный охват всех 16 категорий из навигатора
EVERGREEN_DEALS = [
    {
        'id': 'sk_trains_free',
        'title': 'Бесплатные поезда по Словакии для студентов (ŽSSK)',
        'category': 'Транспорт и Путешествия',
        'main_tag': 'словакия',
        'benefit': '100% бесплатно во 2-м классе всех поездов ŽSSK',
        'duration': 'На весь период дневной формы обучения (до 26 лет)',
        'region': '🇸🇰 Словакия (Кошице, Братислава, Татры)',
        'requirements': 'Студенческий билет с чипом ISIC (вузы TUKE, UPJŠ и др.)',
        'description': 'Легендарная льгота в Словакии: бесплатный проезд во всех поездах государственной железной дороги по всей стране. Поездки из Кошице в горы Высокие Татры, Братиславу или к границам не стоят ни цента.',
        'how_to': '1. Оформите студенческий ISIC в вашем вузе (TUKE, UPJŠ).\n2. В кассе ŽSSK на вокзале Кошице оформите регистрацию (Preukaz pre študenta).\n3. Оформляйте бесплатные нулевые билеты на сайте zssk.sk или в приложении Ideme vlakom.',
        'link': 'https://www.zssk.sk/bezplatna-preprava/studenti/',
        'extra_tags': ['кошице', 'поезда', 'isic']
    },
    {
        'id': 'kosice_dpmk_transport',
        'title': 'Студенческий проездной в Кошице (DPMK) со скидкой 50%',
        'category': 'Транспорт и Город',
        'main_tag': 'кошице',
        'benefit': 'Скидка 50% на все билеты и месячные проездные',
        'duration': 'На учебный год (продление по ISIC)',
        'region': '🇸🇰 Кошице (Словакия)',
        'requirements': 'Студенческая карта ISIC с активированным транспортным чипом',
        'description': 'Городской транспорт Кошице (трамваи и автобусы DPMK) для студентов стоит ровно вполовину дешевле. Выгоднее всего оформить электронный проездной (Mesačník) прямо на карту ISIC.',
        'how_to': '1. Активируйте транспортный чип ISIC в университетском терминале.\n2. В приложении DPMK или в кассах на Bardejovská / Rooseveltova пополните студенческий проездной.',
        'link': 'https://www.dpmk.sk/prepravny-poriadok/vybavovanie-studentskych-zliav',
        'extra_tags': ['словакия', 'транспорт', 'dpmk']
    },
    {
        'id': 'sk_isic_jedalne',
        'title': 'Студенческие обеды в Кошице по ISIC за €2–€3',
        'category': 'Питание и Общежития',
        'main_tag': 'кошице',
        'benefit': 'Государственная дотация на каждое блюдо (экономия 60%)',
        'duration': 'Каждый учебный семестр',
        'region': '🇸🇰 Кошице (столовые TUKE и UPJŠ)',
        'requirements': 'Карта студента ISIC соответствующего университета',
        'description': 'Министерство образования Словакии субсидирует горячее питание для студентов. В университетских столовых Кошице полноценный комплексный обед стоит от €2 до €3.50.',
        'how_to': '1. Пополните баланс питания через портал jedalen.tuke.sk или в кассе столовой.\n2. Приложите карту ISIC на раздаче.',
        'link': 'https://jedalen.tuke.sk/',
        'extra_tags': ['словакия', 'еда', 'isic']
    },
    {
        'id': 'kosice_tabacka_usmev',
        'title': 'Студенческий досуг в Кошице: Tabačka Kulturfabrik и Kino Úsmev',
        'category': 'Культура и Ивенты',
        'main_tag': 'ивенты',
        'benefit': 'Билеты в кино, на концерты и фестивали со скидкой до 40%',
        'duration': 'Постоянно при предъявлении карты',
        'region': '🇸🇰 Кошице (Gorkého 2 / Kasárenské námestie)',
        'requirements': 'Студенческий билет или карта ISIC',
        'description': 'Главные точки культурной жизни Кошице: Tabačka Kulturfabrik и Kino Úsmev предлагают специальные студенческие тарифы на европейское кино, лекции, спектакли и концерты.',
        'how_to': 'Выбирайте тариф «Študent / ISIC» при покупке онлайн на сайтах площадок или покажите ISIC в кассе.',
        'link': 'https://tabacka.sk/',
        'extra_tags': ['кошице', 'словакия', 'кино']
    },
    {
        'id': 'sk_student_brigady',
        'title': 'Работа для студентов в Словакии (Dohoda o brigádnickej práci)',
        'category': 'Работа и Карьера',
        'main_tag': 'работа',
        'benefit': 'Освобождение от налогов на доход до €200 в месяц (чистая зарплата)',
        'duration': 'До 26 лет при дневной форме обучения',
        'region': '🇸🇰 Словакия (Кошице, Прешов и др.)',
        'requirements': 'Справка об учёбе (Potvrdenie o návšteve školy) и возраст до 26 лет',
        'description': 'Специальный тип трудового договора для студентов (Dohoda). Позволяет легально подрабатывать до 20 часов в неделю. При подаче заявления на налоговое исключение (Odvodová úľava) с первых €200 заработка в месяц не удерживаются страховые взносы.',
        'how_to': 'Ищите вакансии с пометкой «Brigáda» на официальном словацком портале Profesia.sk в разделе Košice.',
        'link': 'https://www.profesia.sk/praca/kosice/brigady/',
        'extra_tags': ['словакия', 'кошице', 'стажировки']
    },
    {
        'id': 'flixbus_regiojet_discounts',
        'title': 'Скидки 10–15% на FlixBus и поезда RegioJet по Европе',
        'category': 'Путешествия по Европе',
        'main_tag': 'путешествия',
        'benefit': 'Скидка 10%–15% на автобусы и поезда по всей Европе',
        'duration': 'Круглый год',
        'region': '🇪🇺 Вся Европа (маршруты из Кошице в Вену, Прагу, Будапешт)',
        'requirements': 'Действующая карта ISIC',
        'description': 'Дешёвые путешествия по Европе прямо из Кошице. Автобусы FlixBus и поезда RegioJet соединяют Кошице с Прагой, Братиславой, Будапештом, Краковом и Веной.',
        'how_to': '1. Авторизуйтесь на словацком портале isic.sk в разделе льгот.\n2. Сгенерируйте промокод на поездку FlixBus или привяжите ISIC в профиле RegioJet.',
        'link': 'https://isic.sk/zlavy-na-slovensku/',
        'extra_tags': ['европа', 'поезда', 'flixbus']
    },
    {
        'id': 'europe_isic_benefits',
        'title': 'Карта ISIC в Европе: бесплатные музеи, скидки на хостелы и паромы',
        'category': 'Путешествия и Музеи',
        'main_tag': 'европа',
        'benefit': 'Скидки до 50% или бесплатный вход в 150 000 локаций',
        'duration': 'В течение срока действия карты',
        'region': '🇪🇺 Все страны Европейского Союза',
        'requirements': 'Международное удостоверение студента ISIC',
        'description': 'Ваш студенческий билет ISIC словацкого вуза — ключ к скидкам по всей Европе. Музеи, галереи и достопримечательности часто делают вход для студентов бесплатным или за полцены.',
        'how_to': 'Перед поездкой проверяйте список скидок в конкретном городе через международную базу скидок ISIC.',
        'link': 'https://www.isic.org/discounts/',
        'extra_tags': ['путешествия', 'isic', 'скидки']
    },
    {
        'id': 'lowcost_flights_kosice',
        'title': 'Дешёвые перелёты по Европе из Кошице, Будапешта и Кракова',
        'category': 'Авиабилеты и Лоукостеры',
        'main_tag': 'авиа',
        'benefit': 'Прямые билеты от €15 в Лондон, Милан, Рим, Вену',
        'duration': 'Сезонные распродажи лоукостеров',
        'region': '🇸🇰 Кошице (KSC), 🇭🇺 Будапешт (BUD), 🇵🇱 Краков (KRK)',
        'requirements': 'Паспорт / ВНЖ студента',
        'description': 'Из аэропорта Кошице летают прямые рейсы Wizz Air и Ryanair. Прямой автобус из Кошице доставляет прямо в аэропорт Будапешта (2.5 часа) и Кракова, откуда открывается сеть сотен рейсов по €10–€25.',
        'how_to': 'Следите за расписанием и новыми прямыми направлениями на официальном сайте аэропорта Кошице.',
        'link': 'https://www.airportkosice.sk/sk',
        'extra_tags': ['путешествия', 'европа', 'билеты']
    },
    {
        'id': 'fusion_360_edu',
        'title': 'Autodesk Fusion 360 (CAD / 3D-моделирование) бесплатно',
        'category': 'Инженерия и CAD',
        'main_tag': 'cad',
        'benefit': 'Бесплатная образовательная подписка (экономия $680/год)',
        'duration': '1 год с возможностью ежегодного продления на время учёбы',
        'region': '🌍 Global (актуально для студентов TUKE и технических вузов)',
        'requirements': 'Университетская почта или студенческий билет ISIC',
        'description': 'Профессиональный облачный пакет для 3D-проектирования, моделирования деталей, симуляции нагрузок и подготовки к ЧПУ-обработке.',
        'how_to': '1. Перейдите на образовательный портал Autodesk.\n2. Зарегистрируйтесь с почтой вуза (@tuke.sk) или загрузите фото ISIC.\n3. Скачайте и активируйте лицензию.',
        'link': 'https://www.autodesk.com/education/edu-software/overview',
        'extra_tags': ['софт', '3d', 'инженерия']
    },
    {
        'id': 'jetbrains_all_products',
        'title': 'JetBrains All Products Pack (Профессиональные IDE)',
        'category': 'Разработка и IT',
        'main_tag': 'dev',
        'benefit': 'Бесплатный доступ ко всем IDE: IntelliJ IDEA Ultimate, PyCharm Pro, WebStorm, CLion (экономия $289/год)',
        'duration': '1 год с ежегодным продлением на весь срок учёбы',
        'region': '🌍 Global',
        'requirements': 'Студенческая университетская почта или карта ISIC',
        'description': 'Полный пакет профессиональных сред разработки от JetBrains для программистов и студентов IT-специальностей без функциональных ограничений.',
        'how_to': '1. Откройте страницу JetBrains for Students.\n2. Подайте заявку, указав университетскую почту.\n3. Получите активацию в профиле JetBrains Account.',
        'link': 'https://www.jetbrains.com/community/education/#students',
        'extra_tags': ['программирование', 'софт', 'jetbrains']
    },
    {
        'id': 'github_student_pack',
        'title': 'GitHub Student Developer Pack (включая Copilot Pro)',
        'category': 'Инструменты Разработки и ИИ',
        'main_tag': 'ИИ',
        'benefit': 'Бесплатный доступ к GitHub Copilot, доменам .me, облачным серверам (ценность свыше $1000)',
        'duration': 'На всё время обучения',
        'region': '🌍 Global',
        'requirements': 'Аккаунт GitHub + подтверждение статуса студента',
        'description': 'Главный набор студента-разработчика: интеллектуальный ИИ-ассистент GitHub Copilot, бесплатные домены Namecheap, серверы DigitalOcean и десятки премиум-инструментов.',
        'how_to': '1. Войдите в GitHub и перейдите в GitHub Education.\n2. Добавьте студенческую почту и загрузите фото расписания или карты ISIC.\n3. Получите одобрение и доступ к пакету преимуществ.',
        'link': 'https://education.github.com/pack',
        'extra_tags': ['разработка', 'copilot', 'софт']
    },
    {
        'id': 'azure_students',
        'title': 'Microsoft Azure for Students ($100 на серверы и ИИ)',
        'category': 'Облачные Технологии и Серверы',
        'main_tag': 'ИИ',
        'benefit': '$100 стартового баланса на облачные сервисы + бесплатные службы без привязки банковской карты',
        'duration': '12 месяцев с возможностью продления',
        'region': '🌍 Global',
        'requirements': 'Студенческий адрес электронной почты',
        'description': 'Облачная инфраструктура для учебных проектов, развертывания веб-сайтов, баз данных и запуска моделей машинного обучения без риска списания денег.',
        'how_to': '1. Перейдите на страницу Azure for Students.\n2. Нажмите «Start free» и пройдите верификацию через студенческий email.\n3. Создавайте виртуальные машины и тестируйте ИИ.',
        'link': 'https://azure.microsoft.com/free/students/',
        'extra_tags': ['облако', 'azure', 'серверы']
    },
    {
        'id': 'figma_education',
        'title': 'Figma Professional для студентов',
        'category': 'Дизайн и Интерфейсы',
        'main_tag': 'дизайн',
        'benefit': 'Бесплатный профессиональный тариф Figma Pro и FigJam (экономия $144/год)',
        'duration': 'До 2 лет с возможностью повторной верификации',
        'region': '🌍 Global',
        'requirements': 'Студенческий статус (название вуза и подтверждение)',
        'description': 'Инструмент для UX/UI-дизайна, совместного прототипирования мобильных приложений, веб-сайтов и интерактивных досок FigJam для командной работы.',
        'how_to': '1. Войдите в аккаунт Figma и перейдите на страницу Education.\n2. Заполните короткую форму с указанием вуза и загрузите студенческий.\n3. Команда получит статус Professional бесплатно.',
        'link': 'https://www.figma.com/education/',
        'extra_tags': ['figma', 'uiux', 'дизайн']
    },
    {
        'id': 'canva_pro_student',
        'title': 'Canva Pro для студентов',
        'category': 'Графика и Презентации',
        'main_tag': 'дизайн',
        'benefit': 'Премиальные шаблоны, удаление фона, генеративный ИИ и миллионы фото бесплатно',
        'duration': 'На период учёбы',
        'region': '🌍 Global',
        'requirements': 'Образовательная почта или доступ через университетский домен',
        'description': 'Сервис для оформления рефератов, презентаций курсовых, постеров студенческих мероприятий и постов для соцсетей.',
        'how_to': 'Перейдите на страницу Canva for Education и зарегистрируйтесь по университетскому адресу.',
        'link': 'https://www.canva.com/education/',
        'extra_tags': ['canva', 'графика', 'презентации']
    },
    {
        'id': 'notion_education',
        'title': 'Notion Plus Plan for Education',
        'category': 'Продуктивность и Заметки',
        'main_tag': 'продуктивность',
        'benefit': 'Бесплатный тариф Plus с неограниченным хранилищем файлов (экономия $120/год)',
        'duration': 'Бессрочно на весь период студенчества',
        'region': '🌍 Global',
        'requirements': 'Студенческая почта вуза',
        'description': 'Универсальное рабочее пространство для ведения конспектов лекций, базы знаний по предметам, расписания дедлайнов и подготовки к экзаменам.',
        'how_to': '1. Создайте аккаунт Notion.\n2. В настройках смените email на студенческий.\n3. В разделе Upgrade выберите тариф «Get free Education plan».',
        'link': 'https://www.notion.so/product/notion-for-education',
        'extra_tags': ['notion', 'заметки', 'учеба']
    },
    {
        'id': 'coursera_student',
        'title': 'Coursera for Campus (Студенческий доступ)',
        'category': 'Онлайн-Обучение',
        'main_tag': 'продуктивность',
        'benefit': 'Бесплатный доступ к курсам ведущих мировых университетов с выдачей сертификатов',
        'duration': 'В рамках университетских программ партнёрства',
        'region': '🌍 Global',
        'requirements': 'Почта аккредитованного университета',
        'description': 'Курсы по машинному обучению, бизнесу, программированию и языкам от Google, IBM, Stanford и Yale с получением официальных сертификатов.',
        'how_to': 'Авторизуйтесь на странице студенческой программы Coursera с вашим вузовским адресом.',
        'link': 'https://www.coursera.org/for-university-and-college-students',
        'extra_tags': ['курсы', 'образование', 'сертификаты']
    },
    {
        'id': 'youtube_premium_student',
        'title': 'YouTube Premium + YouTube Music для студентов',
        'category': 'Медиа и Развлечения',
        'main_tag': 'подписки',
        'benefit': 'Скидка около 50% на подписку без рекламы и с фоновым воспроизведением',
        'duration': 'До 4 лет (ежегодная проверка через SheerID)',
        'region': '🇸🇰 Словакия и 🇪🇺 ЕС',
        'requirements': 'Подтверждение статуса через SheerID (справка или ISIC)',
        'description': 'Просмотр обучающих лекций и видео без рекламы, скачивание в офлайн и доступ к трекам YouTube Music по студенческой цене (€4.49 вместо €8.99).',
        'how_to': 'Откройте страницу студенческой подписки YouTube, выберите вуз и подтвердите статус через систему SheerID.',
        'link': 'https://www.youtube.com/premium/student',
        'extra_tags': ['музыка', 'youtube', 'подписки']
    },
    {
        'id': 'spotify_student',
        'title': 'Spotify Premium Student',
        'category': 'Музыка и Подкасты',
        'main_tag': 'подписки',
        'benefit': 'Скидка 50% на премиум-подписку без рекламы в высоком качестве',
        'duration': 'До 4 лет с ежегодным продлением',
        'region': '🇸🇰 Словакия (€3.49/месяц вместо €6.99)',
        'requirements': 'Верификация через SheerID',
        'description': 'Официальный студенческий тариф Spotify. Вся музыка мира, подкасты для изучения языков, прослушивание офлайн без рекламы.',
        'how_to': 'Перейдите на страницу Spotify Student, войдите в аккаунт и пройдите валидацию учебного заведения.',
        'link': 'https://www.spotify.com/student/',
        'extra_tags': ['музыка', 'spotify', 'подписки']
    },
    {
        'id': 'apple_music_tv',
        'title': 'Apple Music + Apple TV+ для студентов',
        'category': 'Музыка и Кино',
        'main_tag': 'подписки',
        'benefit': 'Apple Music со скидкой 50% + бесплатный доступ к онлайн-кинотеатру Apple TV+',
        'duration': 'До 48 месяцев',
        'region': '🇸🇰 Словакия и 🇪🇺 ЕС',
        'requirements': 'Студенческая верификация через UNiDAYS',
        'description': 'Студенческая цена на Apple Music (Spatial Audio, Lossless) плюс бесплатный полный доступ ко всем фильмам и сериалам сервиса Apple TV+.',
        'how_to': 'В приложении «Музыка» или на сайте Apple выберите студенческую подписку и подтвердите статус через UNiDAYS.',
        'link': 'https://www.apple.com/apple-music/',
        'extra_tags': ['кино', 'музыка', 'apple']
    },
    {
        'id': 'asos_student_discount',
        'title': 'Скидка 10% на одежду и обувь в ASOS (доставка в ЕС)',
        'category': 'Одежда и Стиль',
        'main_tag': 'одежда',
        'benefit': 'Постоянная скидка 10% на весь ассортимент',
        'duration': 'Круглый год на весь период учёбы',
        'region': '🇸🇰 Словакия, 🇪🇺 ЕС',
        'requirements': 'Студенческая почта или верификация ASOS',
        'description': 'Брендовые кроссовки (Nike, New Balance, adidas) и базовый гардероб. Студенческий код действует постоянно и суммируется со многими распродажами.',
        'how_to': 'Перейдите на страницу валидации ASOS, укажите страну учёбы и подтвердите статус студента для получения персонального кода.',
        'link': 'https://www.asos.com/student-validation',
        'extra_tags': ['одежда', 'стиль', 'кроссовки']
    },
    {
        'id': 'epic_games_weekly',
        'title': 'Еженедельные бесплатные игры в Epic Games Store',
        'category': 'Игры и Раздачи',
        'main_tag': 'игры',
        'benefit': '100% бесплатно (1–2 лицензионные игры каждую неделю)',
        'duration': 'Обновление каждый четверг в 17:00 (навсегда в библиотеку)',
        'region': '🌍 Global / Онлайн',
        'requirements': 'Бесплатный аккаунт Epic Games Store',
        'description': 'Каждую неделю Epic Games дарит отличные игры: от инди-хитов до крупных AAA-проектов. Добавленная игра остаётся на вашем аккаунте навсегда.',
        'how_to': '1. Зарегистрируйтесь в Epic Games Store.\n2. Перейдите в раздел «Бесплатные игры» и нажмите «Получить».\n3. Игра навсегда привяжется к вашему аккаунту.',
        'link': 'https://store.epicgames.com/free-games',
        'extra_tags': ['игры', 'epicgames', 'раздача']
    },
    {
        'id': 'steam_free_to_play',
        'title': 'Постоянный каталог бесплатных игр в Steam (Free to Play)',
        'category': 'Игры и Развлечения',
        'main_tag': 'игры',
        'benefit': 'Сотни топовых игр без оплаты (Dota 2, CS2, Apex Legends, Destiny 2)',
        'duration': 'Доступно всегда',
        'region': '🌍 Global / Онлайн',
        'requirements': 'Аккаунт Steam',
        'description': 'Официальный раздел бесплатных соревновательных, кооперативных и сюжетных игр в Steam. Отличный способ отвлечься от учёбы вместе с друзьями без затрат.',
        'how_to': 'Откройте раздел Free to Play в клиенте Steam или браузере и добавьте любую игру в библиотеку.',
        'link': 'https://store.steampowered.com/genre/Free%20to%20Play/',
        'extra_tags': ['игры', 'steam', 'онлайн']
    },
    {
        'id': 'isic_extra_hot_deals',
        'title': 'Горящие акции и специальные купоны месяца по ISIC (Словакия)',
        'category': 'Горящие Акции и Скидки',
        'main_tag': 'горящее',
        'benefit': 'Скидки до 50% на фастфуд, электронику, доставку и покупки',
        'duration': 'Временные ежемесячные промокоды',
        'region': '🇸🇰 Словакия (Кошице, Прешов, Братислава)',
        'requirements': 'Карта студента ISIC',
        'description': 'Кроме базовых льгот на поезда, держателям словацкого ISIC доступны ежемесячные горящие купоны (Extra kupóny): скидки в McDonald\'s, KFC, Martinus, Panta Rhei, Alza и спортивных магазинах.',
        'how_to': '1. Авторизуйтесь на сайте isic.sk или в приложении ISIC Slovakia.\n2. Перейдите в раздел «Kupóny» и активируйте спецпредложения месяца.',
        'link': 'https://isic.sk/zlavy-na-slovensku/',
        'extra_tags': ['горящее', 'словакия', 'кошице', 'скидки']
    },
    {
        'id': 'github_perks_hot_credits',
        'title': 'Горящие кредиты и лицензии: DigitalOcean, JetBrains и Namecheap',
        'category': 'Бонусы и Студенческие Кредиты',
        'main_tag': 'горящее',
        'benefit': '$200 на серверы DigitalOcean, бесплатный домен .me и SSL на 1 год',
        'duration': 'На время учёбы',
        'region': '🌍 Global / Онлайн',
        'requirements': 'Студенческий статус (студенческая почта или ISIC)',
        'description': 'Щедрые стартовые бонусы для студентов в рамках GitHub Education: поднимайте личные серверы, VPN и учебные веб-проекты с бесплатным балансом.',
        'how_to': 'Авторизуйтесь через GitHub Education Pack и активируйте промокоды партнёров в разделе Offers.',
        'link': 'https://education.github.com/pack',
        'extra_tags': ['горящее', 'софт', 'it', 'серверы']
    }
]

# Статус «Постоянная льгота» добавляется ТОЛЬКО для базового каталога
for deal in EVERGREEN_DEALS:
    deal["status_line"] = "📌 <b>Статус:</b> Постоянная льгота (бессрочно)"

DYNAMIC_FEEDS = [
    # 1. Раздачи ПК-игр: СТРОГО Steam и Epic Games
    {
        "url": "https://www.gamerpower.com/api/giveaways?platform=pc&sort-by=date",
        "type": "game",
        "category": "Раздача недели (Игры)",
        "badge": "🎮 [Игры: Steam & Epic]",
        "main_tag": "игры",
        "default_benefit": "Бесплатно 100% (Вместо полной цены)",
        "default_duration": "Ограничено по времени (до окончания раздачи)",
        "default_region": "Global (ПК)",
        "how_to_tip": "Перейдите на страницу раздачи платформы и добавьте игру в свою библиотеку навсегда.",
        "max_ttl_seconds": 604800
    },
    {
        "url": "https://www.reddit.com/r/FreeGamesOnSteam/new.rss",
        "type": "game",
        "category": "Раздача недели (Игры)",
        "badge": "🎮 [Steam]",
        "main_tag": "игры",
        "default_benefit": "Бесплатно 100% (Лицензия Steam)",
        "default_duration": "Ограничено по времени",
        "default_region": "Global (Steam)",
        "how_to_tip": "Активируйте ключ или заберите игру через страницу акции в магазине Steam.",
        "max_ttl_seconds": 345600
    },
    {
        "url": "https://www.reddit.com/r/EpicGamesPC/new.rss",
        "type": "game",
        "category": "Раздача недели (Игры)",
        "badge": "🎮 [Epic Games]",
        "main_tag": "игры",
        "default_benefit": "Бесплатная раздача Epic Games",
        "default_duration": "Еженедельная акция EGS",
        "default_region": "Global (Epic Games)",
        "how_to_tip": "Войдите в аккаунт Epic Games и нажмите «Оформить заказ» за 0€.",
        "max_ttl_seconds": 604800
    },
    # 2. Подработка и стажировки для студентов в Словакии / Кошице
    {
        "url": "https://www.profesia.sk/praca/kosice/?format=rss&employment_type=brigada",
        "type": "vacancy",
        "category": "Работа и Доход",
        "badge": "💼 [Бригада в Кошице]",
        "main_tag": "работа",
        "default_benefit": "Почасовая оплата для студентов (Dohoda)",
        "default_duration": "Актуально до закрытия вакансии работодателем",
        "default_region": "🇸🇰 Кошице (Словакия)",
        "how_to_tip": "Отправьте резюме через форму Profesia.sk или свяжитесь с работодателем.",
        "max_ttl_seconds": 604800
    },
    {
        "url": "https://www.brigada.sk/rss.php",
        "type": "vacancy",
        "category": "Работа и Доход",
        "badge": "💼 [Студенческая подработка]",
        "main_tag": "работа",
        "default_benefit": "Гибкий график для студентов вузов",
        "default_duration": "До набора кандидатов",
        "default_region": "🇸🇰 Словакия",
        "how_to_tip": "Откликнитесь на вакансию на сайте Brigada.sk, указав студенческий статус.",
        "max_ttl_seconds": 604800
    },
    # 3. Бесплатные курсы и сертификаты с промокодами
    {
        "url": "https://www.reddit.com/r/udemyfreebies/new.rss",
        "type": "promo",
        "category": "Бесплатные курсы",
        "badge": "🎓 [Курсы с купонами]",
        "main_tag": "курсы",
        "default_benefit": "Бесплатный доступ к курсу (Скидка 100%)",
        "default_duration": "Купон на 1–2 дня или первые 1000 активаций",
        "default_region": "Online (Глобально)",
        "how_to_tip": "Перейдите по ссылке с примененным промокодом и нажмите «Enroll Now» за $0.",
        "max_ttl_seconds": 172800
    },
    # 4. Студенческий гардероб и стиль
    {
        "url": "https://www.reddit.com/r/frugalmalefashion/new.rss",
        "type": "promo",
        "category": "Одежда и Шопинг",
        "badge": "👟 [Одежда и Обувь]",
        "main_tag": "одежда",
        "default_benefit": "Скидки до 60–70% в европейских магазинах",
        "default_duration": "Пока товар есть в наличии (Распродажа)",
        "default_region": "Европа / Доставка в Словакию",
        "how_to_tip": "Используйте промокод на корзине или заказывайте товары из раздела сейла.",
        "max_ttl_seconds": 259200
    },
    # 5. Горящие скидки на технику, софт и сервисы
    {
        "url": "https://www.pepper.it/rss/nuove",
        "type": "promo",
        "category": "Софт и Полезности",
        "badge": "🔥 [Горящее предложение]",
        "main_tag": "горящее",
        "default_benefit": "Крупная скидка на электронику / софт",
        "default_duration": "Ограниченная акция",
        "default_region": "Евросоюз",
        "how_to_tip": "Проверьте условия акции на сайте продавца перед покупкой.",
        "max_ttl_seconds": 259200
    }
]

TOPIC_RULES = [
    ("ИИ", ["ai", "copilot", "chatgpt", "openai", "claude", "gemini", "нейросеть", "llm"]),
    ("dev", ["github", "jetbrains", "azure", "docker", "python", "developer", "код", "git", "api", "ide", "vscode"]),
    ("дизайн", ["figma", "canva", "adobe", "дизайн", "ui/ux", "graphics", "3d", "blender"]),
    ("cad", ["fusion 360", "autocad", "autodesk", "cad", "solidworks", "инженерия"]),
    ("продуктивность", ["notion", "office 365", "excel", "obsidian", "учеба", "конспекты"]),
    ("подписки", ["spotify", "apple music", "youtube premium", "музыка", "стриминг", "подписка"]),
    ("курсы", ["coursera", "udemy", "сертификат", "обучение", "лекции"]),
    ("одежда", ["asos", "nike", "adidas", "кроссовки", "гардероб", "одежда"]),
    ("игры", ["steam", "epic games", "раздача", "игры", "гейминг", "бесплатно игра"]),
    ("словакия", ["словакия", "slovensko", "slovakia", "bratislava", "zssk", "isic"]),
    ("кошице", ["кошице", "košice", "kosice", "dpmk", "tuke", "upjs"]),
    ("путешествия", ["поезд", "flixbus", "regiojet", "ryanair", "wizz", "лоукостер", "билеты", "музей"])
]

def extract_topic_tags(title, text):
    combined = f"{title} {text}".lower()
    matched = []
    for tag_name, keywords in TOPIC_RULES:
        for kw in keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', combined):
                if tag_name not in matched:
                    matched.append(tag_name)
                break
    return matched

def load_json_file(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка чтения {filename}: {e}")
    return None

def save_json_file(filename, data):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def escape_html(text):
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def is_expired_title(title):
    t = title.lower()
    markers = ["[expired]", "(expired)", "ended", "oos", "out of stock", "завершено", "истекло", "неактуально"]
    return any(m in t for m in markers)

def is_allowed_language(text):
    if not text:
        return True, "Empty text"

    non_allowed_scripts = re.compile(
        r'[가-힯ᄀ-ᇿ㄰-㆏'  # Корейский
        r'一-鿿㐀-䶿'                # Китайский / Японский (CJK)
        r'぀-ゟ゠-ヿ'                # Хирагана / Катакана
        r'؀-ۿݐ-ݿ'                # Арабский
        r'֐-׿'                            # Иврит
        r'ऀ-ॿ'                            # Деванагари
        r'฀-๿]'                           # Тайский
    )
    if non_allowed_scripts.search(text):
        return False, "Неразрешённая письменность (Корейский, Китайский, Арабский и др.)"

    lower_t = text.lower()

    disallowed_tags = [
        '[fr]', '(fr)', '[french]', '(french)', '[français]', '(français)',
        '[es]', '(es)', '[spanish]', '(spanish)', '[español]', '(español)',
        '[de]', '(de)', '[german]', '(german)', '[deutsch]', '(deutsch)',
        '[pt]', '(pt)', '[portuguese]', '(portuguese)',
        '[it]', '(it)', '[italian]', '(italian)',
        '[ar]', '(ar)', '[arabic]', '(arabic)',
        '[tr]', '(tr)', '[turkish]', '(turkish)',
        '[pl]', '(pl)', '[polish]', '(polish)'
    ]
    for tag in disallowed_tags:
        if tag in lower_t:
            return False, f"Запрещённый языковой тег {tag}"

    cyrillic_chars = re.findall(r'[а-яА-ЯёЁіІїЇєЄґҐ]', text)
    if len(cyrillic_chars) >= 4:
        return True, "Русский / Украинский язык"

    forbidden_chars = set('çœèêàâîïûùöüßñ¿¡ąęłśźż')
    matched_forbidden = set(c for c in lower_t if c in forbidden_chars)
    if len(matched_forbidden) >= 1:
        return False, f"Недопустимые символы языка: {matched_forbidden}"

    slovak_diacritics = set('ľĺŕčšžťďňôä')
    if any(c in slovak_diacritics for c in lower_t):
        return True, "Словацкий язык"

    tokens = set(re.findall(r'[a-zA-Z]+', lower_t))
    french_words = {
        'le', 'la', 'les', 'des', 'du', 'pour', 'avec', 'dans', 'sur', 'une', 'sont',
        'formation', 'formations', 'apprendre', 'debutant', 'debutants', 'gratuit',
        'gratuite', 'francais', 'francaise', 'cours', 'cette', 'votre', 'notre'
    }
    spanish_words = {
        'el', 'los', 'las', 'del', 'para', 'con', 'por', 'curso', 'cursos',
        'aprender', 'aprende', 'gratis', 'espanol', 'desde', 'principiantes'
    }
    german_words = {
        'der', 'die', 'das', 'den', 'dem', 'des', 'fuer', 'mit', 'und',
        'kostenlos', 'lernen', 'deutsch', 'anfaenger', 'kurs'
    }

    if len(tokens.intersection(french_words)) >= 2:
        return False, "Французский язык"
    if len(tokens.intersection(spanish_words)) >= 2:
        return False, "Испанский язык"
    if len(tokens.intersection(german_words)) >= 2:
        return False, "Немецкий язык"

    return True, "Английский или Словацкий язык"

def extract_direct_link(summary_html, default_link):
    if not summary_html:
        return default_link
    match = re.search(r'<a\s+href="([^"]+)">\[link\]</a>', summary_html, re.IGNORECASE)
    if match:
        return match.group(1)
    urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', summary_html)
    for u in urls:
        if "reddit.com" not in u and "redd.it" not in u:
            return u
    return default_link

def clean_summary_text(summary_html):
    if not summary_html:
        return ""
    # Декодируем HTML-сущности (&#32; превращается в обычный пробел)
    text = html.unescape(summary_html)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&#\d+;|&[a-zA-Z]+;', ' ', text)
    text = re.sub(r'submitted by.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[link\].*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[comments\].*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'https?://\S+', '', text)
    clean = ' '.join(text.split()).strip()
    if len(clean) < 15:
        return ""
    if len(clean) > 280:
        clean = clean[:277].rsplit(' ', 1)[0] + '...'
    return clean

def get_base_domain(url):
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return url

def validate_link(url, fallback_url=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    try:
        resp = requests.head(url, timeout=7, headers=headers, allow_redirects=True)
        if resp.status_code in (405, 501):
            resp = requests.get(url, timeout=7, headers=headers, allow_redirects=True, stream=True)

        if resp.status_code in (404, 410):
            print(f"Ссылка {url} вернула статус {resp.status_code}. Пропуск публикации.")
            return "DROP", None, False
        if resp.status_code in (500, 502, 503, 504):
            print(f"Сервер временно недоступен ({resp.status_code}). Повтор позже.")
            return "RETRY", None, False

        final_url = resp.url
        base_original = get_base_domain(url).lower()
        base_final = get_base_domain(final_url).lower()

        if base_original == base_final and final_url.rstrip("/") == base_final.rstrip("/"):
            if url.rstrip("/") != base_original.rstrip("/"):
                print(f"Редирект на главную страницу сервиса: {url} -> {final_url}. Публикуем с пометкой.")
                return "OK", final_url, True

        return "OK", final_url, False
    except requests.exceptions.Timeout:
        print(f"Таймаут проверки ссылки {url}. Повтор в следующем цикле.")
        return "RETRY", None, False
    except requests.exceptions.RequestException as e:
        print(f"Ошибка проверки ссылки ({e}). Используем резервную ссылку.")
        return "OK", fallback_url or url, False

def fetch_feed_entries(feed_info):
    url = feed_info["url"]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    if "gamerpower.com" in url:
        resp = requests.get(url, timeout=10, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            entries = []
            for item in data[:25]:
                open_giveaway_url = item.get("open_giveaway_url") or item.get("open_giveaway") or item.get("gamerpower_url") or ""
                platforms_str = str(item.get("platforms", "")).lower()
                combined_text = f"{item.get('title', '')} {open_giveaway_url} {platforms_str}".lower()

                # СТРОГО: только Steam и Epic Games
                if not any(plat in combined_text for plat in ("steam", "epic", "epicgames")):
                    continue

                entries.append({
                    "id": str(item.get("id")),
                    "title": item.get("title"),
                    "link": open_giveaway_url,
                    "summary": item.get("description", "")
                })
            return entries
        return []

    req_headers = {"User-Agent": "telegram:discount4studentsbot:v2.0 (by /u/studentdealsbot)"} if "reddit.com" in url else headers
    try:
        resp = requests.get(url, timeout=10, headers=req_headers)
        if resp.status_code == 200:
            feed = feedparser.parse(resp.content)
            entries = []
            for e in feed.entries[:25]:
                entries.append({
                    "id": getattr(e, "id", getattr(e, "link", None)),
                    "title": getattr(e, "title", ""),
                    "link": getattr(e, "link", ""),
                    "summary": getattr(e, "summary", "")
                })
            return entries
    except Exception as err:
        print(f"Ошибка загрузки RSS {url}: {err}")
    return []

def send_telegram_card(deal, is_fallback=False):
    title = escape_html(deal.get("title"))
    category = escape_html(deal.get("category"))
    badge = escape_html(deal.get("badge", f"🎓 [{category}]"))
    benefit = escape_html(deal.get("benefit"))
    duration = escape_html(deal.get("duration"))
    region = escape_html(deal.get("region"))
    reqs = escape_html(deal.get("requirements", "Регистрация / Студенческий статус"))
    desc = escape_html(deal.get("description", ""))
    how_to = escape_html(deal.get("how_to", ""))
    link = deal.get("link")

    main_tag = deal.get("main_tag", "горящее")
    extra_tags = deal.get("extra_tags", [])

    seen_tags = set()
    all_tags = []
    for t in [main_tag] + extra_tags:
        if t and t not in seen_tags:
            seen_tags.add(t)
            all_tags.append(t)

    tags_string = " ".join(f"#{t}@{CHANNEL_USERNAME}" for t in all_tags)

    parts = [
        f"{badge} — <b>{title}</b>",
        "",
        f"💰 <b>Выгода:</b> {benefit}",
        f"⏳ <b>Срок:</b> {duration}",
        f"🌍 <b>Регион:</b> {region}",
        f"📋 <b>Что нужно:</b> {reqs}",
        ""
    ]
    if desc:
        parts.extend([desc, ""])
    if how_to:
        parts.extend(["💡 <b>Как оформить / забрать:</b>", how_to, ""])
    if is_fallback:
        parts.extend(["ℹ️ <i>Прямая страница акции перемещена. Предложение доступно на главной странице или через поиск на сайте сервиса.</i>", ""])

    parts.append(tags_string)
    text = "\n".join(parts)

    button_text = "🔗 Перейти на сайт сервиса" if is_fallback else "🔗 Забрать предложение"
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": button_text, "url": link}
            ]
        ]
    }

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
        "reply_markup": reply_markup
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 429:
            retry_after = response.json().get("parameters", {}).get("retry_after", 10)
            print(f"[Лимит Telegram 429] Ожидание {retry_after} секунд...")
            time.sleep(retry_after + 1)
            response = requests.post(url, json=payload, timeout=15)

        print(f"Отправка '{title[:35]}...': HTTP {response.status_code}")
        time.sleep(2.5)

        if response.status_code == 200:
            res_data = response.json()
            message_id = res_data.get("result", {}).get("message_id")
            return True, message_id
        return False, None
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return False, None

def get_navigator_text():
    return (
        "🎓 <b>Навигатор по студенческим скидкам и льготам</b>\n\n"
        "Здесь собраны постоянные льготы, акции и бесплатный софт для студентов в Словакии (Кошице) и онлайн.\n"
        "Нажмите на интересующий тег, чтобы открыть все посты по теме:\n\n"
        "🇸🇰 <b>Словакия и Кошице:</b>\n"
        f"• Бесплатные поезда и транспорт: #транспорт@{CHANNEL_USERNAME} #словакия@{CHANNEL_USERNAME}\n"
        f"• Студенческие скидки по ISIC: #словакия@{CHANNEL_USERNAME}\n"
        f"• Жизнь, еда и досуг в Кошице: #кошице@{CHANNEL_USERNAME}\n"
        f"• Подработка и стажировки: #работа@{CHANNEL_USERNAME}\n\n"
        "🌍 <b>Путешествия и Транспорт:</b>\n"
        f"• Поездки по Европе (FlixBus, музеи): #путешествия@{CHANNEL_USERNAME} #европа@{CHANNEL_USERNAME}\n"
        f"• Дешёвые авиабилеты из Кошице: #авиа@{CHANNEL_USERNAME}\n\n"
        "💻 <b>ИТ, Программирование и ИИ:</b>\n"
        f"• Нейросети и AI-ассистенты: #ИИ@{CHANNEL_USERNAME}\n"
        f"• Лицензии для разработки (JetBrains, GitHub): #dev@{CHANNEL_USERNAME}\n"
        f"• 3D-моделирование и САПР: #cad@{CHANNEL_USERNAME}\n\n"
        "🎨 <b>Дизайн и Презентации:</b>\n"
        f"• Графика, UI/UX (Figma, Canva Pro): #дизайн@{CHANNEL_USERNAME}\n\n"
        "📝 <b>Учёба и Продуктивность:</b>\n"
        f"• Заметки, софт и организация: #продуктивность@{CHANNEL_USERNAME}\n"
        f"• Бесплатные онлайн-курсы и сертификаты: #курсы@{CHANNEL_USERNAME}\n\n"
        "🎧 <b>Подписки и Развлечения:</b>\n"
        f"• Музыка и видео (Spotify, YouTube, Apple): #подписки@{CHANNEL_USERNAME}\n"
        f"• Раздачи лицензионных игр (Steam & Epic): #игры@{CHANNEL_USERNAME}\n"
        f"• Одежда и студенческий гардероб: #одежда@{CHANNEL_USERNAME}\n\n"
        "🔥 <b>Горящие предложения:</b>\n"
        f"• Временные акции и топ-скидки недели: #горящее@{CHANNEL_USERNAME}\n\n"
        "📌 <i>Сохраните этот пост в закладки для быстрого поиска по каналу!</i>"
    )

def send_pinned_navigator():
    text = get_navigator_text()
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            nav_msg_id = resp.json().get("result", {}).get("message_id")
            print(f"Пост-навигатор успешно опубликован: ID {nav_msg_id}")
            return nav_msg_id
        else:
            print(f"Ошибка публикации навигатора: HTTP {resp.status_code} ({resp.text})")
            return None
    except Exception as e:
        print(f"Ошибка отправки навигатора: {e}")
        return None

def pin_telegram_message(message_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/pinChatMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "message_id": message_id,
        "disable_notification": True
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            print(f"Пост-навигатор {message_id} успешно закреплён в канале.")
        else:
            print(f"Не удалось закрепить навигатор: HTTP {resp.status_code} ({resp.text})")
    except Exception as e:
        print(f"Ошибка закрепления навигатора: {e}")

def check_is_deal_still_active(info):
    now = time.time()
    max_ttl = info.get("max_ttl", now + 604800)
    if now >= max_ttl:
        return False, "Истёк максимальный срок публикации (Safety TTL)"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    target_link = info.get("target_link")
    source_link = info.get("source_link")
    post_type = info.get("type", "promo")

    if target_link:
        try:
            resp = requests.get(target_link, timeout=7, headers=headers, allow_redirects=True, stream=True)
            if resp.status_code in (404, 410):
                return False, f"Страница удалена (HTTP {resp.status_code})"

            content_snippet = resp.text[:80000].lower()

            if post_type == "vacancy":
                slovak_expired = [
                    "ponuka už nie je aktuálna",
                    "pracovná ponuka bola archivovaná",
                    "ponuka bola ukončená",
                    "ľutujeme, ale pracovná ponuka už nie je aktuálna",
                    "pracovná ponuka už bola obsadená"
                ]
                for marker in slovak_expired:
                    if marker in content_snippet:
                        return False, f"Работодатель закрыл вакансию ({marker})"
        except Exception:
            pass

    if source_link and "reddit.com" in source_link:
        try:
            reddit_json_url = source_link.rstrip("/") + ".json"
            r_headers = {
                "User-Agent": "telegram:discount4studentsbot:v2.0 (by /u/studentdealsbot)"
            }
            r_resp = requests.get(reddit_json_url, timeout=7, headers=r_headers)
            if r_resp.status_code == 200:
                data = r_resp.json()
                if isinstance(data, list) and len(data) > 0:
                    post_data = data[0].get("data", {}).get("children", [{}])[0].get("data", {})
                    flair = str(post_data.get("link_flair_text", "")).lower()
                    title = str(post_data.get("title", "")).lower()
                    if any(m in flair or m in title for m in ("expired", "ended", "closed", "oos", "dead")):
                        return False, "Сообщество пометило акцию как завершённую (Expired)"
        except Exception:
            pass

    return True, "Активно"

def cleanup_expired_posts(active_posts):
    remaining_posts = {}

    for post_id, info in active_posts.items():
        is_alive, reason = check_is_deal_still_active(info)
        if not is_alive:
            message_id = info.get("message_id")
            title = escape_html(info.get("title", ""))

            print(f"[ЧИСТКА КАНАЛА] Пост {message_id} ('{title}') больше не актуален ({reason}). Удаление...")

            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "message_id": message_id
            }

            try:
                resp = requests.post(url, json=payload, timeout=10)
                if resp.status_code == 200:
                    print(f"  Пост {message_id} успешно удалён из канала.")
                else:
                    print(f"  Не удалось удалить сообщение {message_id}: HTTP {resp.status_code} ({resp.text})")
                time.sleep(1.0)
            except Exception as e:
                print(f"  Ошибка при удалении {message_id}: {e}")
        else:
            remaining_posts[post_id] = info

    return remaining_posts

def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ОШИБКА: Токен или ID канала не заданы.")
        return

    processed_ids_raw = load_json_file(HISTORY_FILE)
    processed_ids = set(processed_ids_raw if isinstance(processed_ids_raw, list) else [])
    new_processed = set(processed_ids)

    active_posts_raw = load_json_file(ACTIVE_POSTS_FILE)
    active_posts = active_posts_raw if isinstance(active_posts_raw, dict) else {}

    is_initial_fill = len(processed_ids) == 0
    print(f"Запуск бота. Режим первичного наполнения: {is_initial_fill}")

    # Шаг 1: Автоматическая чистка канала от неактуальных постов
    active_posts = cleanup_expired_posts(active_posts)

    # Шаг 2: Каталог постоянных программ (все 24 выверенные программы)
    evergreen_posts_file = "data/evergreen_posts.json"
    deal_to_msg_id = load_json_file(evergreen_posts_file) or {}

    for deal in EVERGREEN_DEALS:
        deal_id = deal["id"]
        if deal_id not in processed_ids:
            status, final_url, is_fallback = validate_link(deal["link"])
            if status == "DROP":
                new_processed.add(deal_id)
                continue
            elif status == "RETRY":
                continue

            deal["link"] = final_url
            print(f"Публикация из каталога: {deal['title']}")
            success, message_id = send_telegram_card(deal, is_fallback=is_fallback)
            if success:
                new_processed.add(deal_id)
                if message_id:
                    deal_to_msg_id[deal_id] = message_id

    # =========================================================================
    # СТРОКИ ПОСЛЕ for deal in EVERGREEN_DEALS:
    # =========================================================================
    save_json_file(evergreen_posts_file, deal_to_msg_id)

    # Шаг 3: Публикация и закрепление текстового навигатора
    nav_file = "data/navigator_info.json"
    nav_info = load_json_file(nav_file) or {}

    if is_initial_fill or not nav_info.get("pinned"):
        print("[Навигатор] Публикация закреплённого поста-навигатора...")
        nav_msg_id = send_pinned_navigator()
        if nav_msg_id:
            pin_telegram_message(nav_msg_id)
            save_json_file(nav_file, {"pinned": True, "message_id": nav_msg_id})

    # Шаг 4: Выгрузка всех доступных новостей из КАЖДОГО источника
    per_feed_limit = 10 if is_initial_fill else 4
    dynamic_published = 0
    now = time.time()

    print(f"[Динамика] Опрос всех источников. Лимит на источник: {per_feed_limit} постов.")

    for feed_info in DYNAMIC_FEEDS:
        feed_cat = feed_info.get("category", "Новости")
        feed_count = 0

        try:
            entries = fetch_feed_entries(feed_info)
            print(f"[{feed_cat}] Получено {len(entries)} записей из ленты.")

            for entry in entries:
                if feed_count >= per_feed_limit:
                    break

                post_id = entry.get("id") or entry.get("link")
                if not post_id or post_id in processed_ids:
                    continue

                title = entry.get("title", "")
                if is_expired_title(title):
                    new_processed.add(post_id)
                    continue

                # Игры: разрешены СТРОГО только Steam и Epic Games
                if feed_info.get("type") == "game":
                    comb_game = f"{title} {entry.get('link', '')}".lower()
                    if not any(p in comb_game for p in ("steam", "epic", "epicgames")):
                        new_processed.add(post_id)
                        continue

                raw_link = entry.get("link", "")
                summary = entry.get("summary", "")

                # Фильтрация по языкам: разрешены только EN, RU, UK, SK
                is_ok_lang, lang_reason = is_allowed_language(f"{title} {summary}")
                if not is_ok_lang:
                    print(f"[Языковой фильтр] Пропущен '{title[:40]}...': {lang_reason}")
                    new_processed.add(post_id)
                    continue

                direct_link = extract_direct_link(summary, raw_link) if "reddit.com" in raw_link else raw_link
                status, final_url, is_fallback = validate_link(direct_link, fallback_url=raw_link)

                if status == "DROP":
                    new_processed.add(post_id)
                    continue
                elif status == "RETRY":
                    continue

                topic_tags = extract_topic_tags(title, summary)
                extra_tags = ["горящее"]
                for t in topic_tags:
                    if t != feed_info["main_tag"] and t not in extra_tags:
                        extra_tags.append(t)

                card = {
                    "id": post_id,
                    "title": title,
                    "category": feed_info["category"],
                    "badge": feed_info["badge"],
                    "main_tag": feed_info["main_tag"],
                    "benefit": feed_info["default_benefit"],
                    "duration": feed_info["default_duration"],
                    "region": feed_info["default_region"],
                    "requirements": "Учётная запись платформы / студенческий",
                    "description": clean_summary_text(summary),
                    "how_to": feed_info["how_to_tip"],
                    "link": final_url,
                    "extra_tags": extra_tags
                }

                success, message_id = send_telegram_card(card, is_fallback=is_fallback)
                if success:
                    new_processed.add(post_id)
                    dynamic_published += 1
                    feed_count += 1

                    max_ttl = now + feed_info.get("max_ttl_seconds", 345600)
                    if message_id:
                        active_posts[post_id] = {
                            "message_id": message_id,
                            "title": title,
                            "category": feed_info["category"],
                            "main_tag": feed_info["main_tag"],
                            "target_link": final_url,
                            "source_link": raw_link,
                            "type": feed_info.get("type", "promo"),
                            "posted_at": now,
                            "max_ttl": max_ttl
                        }
        except Exception as e:
            print(f"Ошибка при обработке {feed_info['url']}: {e}")

    save_json_file(HISTORY_FILE, list(new_processed)[-1500:])
    save_json_file(ACTIVE_POSTS_FILE, active_posts)
    print(f"Сбор завершён. Опубликовано динамических постов: {dynamic_published}. Активных на мониторинге: {len(active_posts)}")

if __name__ == "__main__":
    main()
