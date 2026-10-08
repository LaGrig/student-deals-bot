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

# 20 выверенных программ: Кошице, Словакия, Европа и глобальный софт
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
        'description': 'Министерство образования Словакии субсидирует горячее питание для студентов. В университетских столовых Кошице (Jedáleň TUKE на Němcovej/Boženy Němcovej и столовые UPJŠ) полноценный сытный комплексный обед стоит от €2 до €3.50.',
        'how_to': '1. Пополните баланс питания через портал jedalen.tuke.sk или в кассе столовой.\n2. Приложите карту ISIC на раздаче.',
        'link': 'https://jedalen.tuke.sk/',
        'extra_tags': ['словакия', 'tuke', 'обеды']
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
        'description': 'Главные точки культурной жизни Кошице. Культурный центр Tabačka Kulturfabrik и легендарный арт-кинотеатр Kino Úsmev предлагают специальные студенческие тарифы на европейское кино, лекции, спектакли и концерты.',
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
        'extra_tags': ['словакия', 'кошице', 'доход']
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
        'description': 'Дешёвые путешествия по Европе прямо из Кошице. Автобусы FlixBus и поезда RegioJet соединяют Кошице с Прагой, Братиславой, Будапештом, Краковом и Веной. По карте ISIC действует постоянный дисконт.',
        'how_to': '1. Авторизуйтесь на словацком портале isic.sk в разделе льгот.\n2. Сгенерируйте промокод на поездку FlixBus или привяжите ISIC в профиле RegioJet.',
        'link': 'https://isic.sk/zlavy-na-slovensku/',
        'extra_tags': ['европа', 'flixbus', 'билеты']
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
        'description': 'Ваш студенческий билет ISIC словацкого вуза — это ключ к огромным скидкам по всей Европе. Лувр, музеи Вены, галереи Флоренции и достопримечательности Кракова часто делают вход для студентов бесплатным или за полцены.',
        'how_to': 'Перед поездкой проверяйте список скидок в конкретном городе через международную базу скидок ISIC.',
        'link': 'https://www.isic.org/discounts/',
        'extra_tags': ['путешествия', 'isic', 'музеи']
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
        'description': 'Из аэропорта Кошице летают прямые рейсы Wizz Air и Ryanair. Кроме того, прямой автобус из Кошице доставляет прямо в аэропорт Будапешта (2.5 часа) и Кракова, откуда открывается маршрутная сеть сотен рейсов по €10–€25.',
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
        'description': 'Профессиональный облачный пакет для 3D-проектирования, моделирования деталей, симуляции нагрузок и подготовки к ЧПУ-обработке. Стандарт де-факто для инженеров и машиностроителей.',
        'how_to': '1. Перейдите на образовательный портал Autodesk.\n2. Зарегистрируйтесь с почтой вуза (@tuke.sk и др.) или прикрепите фото ISIC.\n3. Скачайте и активируйте лицензию.',
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
        'description': 'Полный пакет топовых сред разработки от JetBrains для программистов и студентов IT-специальностей. Никаких урезанных Community-версий — полный профессиональный инструментарий.',
        'how_to': '1. Откройте страницу JetBrains for Students.\n2. Подайте заявку, указав университетскую почту.\n3. Получите активацию в профиле JetBrains Account.',
        'link': 'https://www.jetbrains.com/community/education/#students',
        'extra_tags': ['софт', 'программирование', 'it']
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
        'description': 'Главный набор студента-разработчика: интеллектуальный ИИ-ассистент GitHub Copilot, бесплатные домены Namecheap, хостинг, серверы DigitalOcean и десятки премиум-инструментов.',
        'how_to': '1. Войдите в GitHub и перейдите в GitHub Education.\n2. Добавьте студенческую почту и загрузите фото расписания или карты ISIC.\n3. Получите одобрение и доступ к пакету преимуществ.',
        'link': 'https://education.github.com/pack',
        'extra_tags': ['dev', 'софт', 'copilot']
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
        'description': 'Облачная инфраструктура для учебных проектов, развертывания веб-сайтов, баз данных и запуска моделей машинного обучения без риска списания личных денег.',
        'how_to': '1. Перейдите на страницу Azure for Students.\n2. Нажмите «Start free» и пройдите верификацию через студенческий email.\n3. Создавайте виртуальные машины и тестируйте ИИ.',
        'link': 'https://azure.microsoft.com/free/students/',
        'extra_tags': ['софт', 'серверы', 'облако']
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
        'description': 'Главный мировой инструмент для UX/UI-дизайна, совместного прототипирования мобильных приложений, веб-сайтов и интерактивных досок FigJam для командной работы.',
        'how_to': '1. Войдите в аккаунт Figma и перейдите на страницу Education.\n2. Заполните короткую форму с указанием вуза и загрузите студенческий.\n3. Команда получит статус Professional бесплатно.',
        'link': 'https://www.figma.com/education/',
        'extra_tags': ['софт', 'графика', 'ux']
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
        'description': 'Идеальный сервис для оформления рефератов, презентаций курсовых, постеров студенческих мероприятий и постов для соцсетей без навыков профессионального дизайна.',
        'how_to': 'Перейдите на страницу Canva for Education и зарегистрируйтесь по университетскому адресу.',
        'link': 'https://www.canva.com/education/',
        'extra_tags': ['софт', 'презентации', 'шаблоны']
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
        'how_to': '1. Создайте аккаунт Notion на личную или учебную почту.\n2. В настройках Settings & Members ➔ My Account смените email на студенческий.\n3. В разделе Upgrade выберите тариф «Get free Education plan».',
        'link': 'https://www.notion.so/product/notion-for-education',
        'extra_tags': ['софт', 'учёба', 'конспекты']
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
        'description': 'Курсы по машинному обучению, бизнесу, программированию и языкам от Google, IBM, Stanford и Yale с получением официальных верифицированных сертификатов для резюме.',
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
        'description': 'Просмотр обучающих лекций и видео без рекламы, скачивание в офлайн и доступ к огромной библиотеке треков YouTube Music по студенческой цене (около €4.49 вместо €8.99 в Словакии).',
        'how_to': 'Откройте страницу студенческой подписки YouTube, выберите вуз и подтвердите статус через систему SheerID.',
        'link': 'https://www.youtube.com/premium/student',
        'extra_tags': ['музыка', 'видео', 'подписка']
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
        'description': 'Официальный студенческий тариф Spotify. Вся музыка мира, подкасты для изучения языков, прослушивание офлайн без ограничений и навязчивых рекламных вставок.',
        'how_to': 'Перейдите на страницу Spotify Student, войдите в аккаунт и пройдите валидацию учебного заведения.',
        'link': 'https://www.spotify.com/student/',
        'extra_tags': ['музыка', 'подписка', 'isic']
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
        'description': 'Двойная выгода от Apple: студенческая цена на Apple Music (Spatial Audio, Lossless) плюс бесплатный полный доступ ко всем фильмам и сериалам сервиса Apple TV+.',
        'how_to': 'В приложении «Музыка» или на сайте Apple выберите студенческую подписку и подтвердите статус через UNiDAYS.',
        'link': 'https://www.apple.com/apple-music/',
        'extra_tags': ['музыка', 'кино', 'apple']
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
        'how_to': 'Перейдите на официальную страницу валидации ASOS, укажите страну учёбы и подтвердите статус студента для получения персонального кода.',
        'link': 'https://www.asos.com/student-validation',
        'extra_tags': ['одежда', 'стиль', 'кроссовки']
    }
]

# Добавляем для всех постоянных предложений явный статус
for deal in EVERGREEN_DEALS:
    deal["status_line"] = "📌 <b>Статус:</b> Постоянная льгота (бессрочно)"

# 5 динамических RSS-источников с явными статусами актуальности и правилами закрытия
DYNAMIC_FEEDS = [
    {
        "url": "https://www.profesia.sk/praca/kosice/brigady/?format=rss",
        "type": "vacancy",
        "category": "Работа и Доход",
        "badge": "💼 [Студенческая вакансия: Кошице]",
        "main_tag": "работа",
        "default_status": "🟢 <b>Статус:</b> Набор открыт (актуально)",
        "default_benefit": "Оплата от €6 до €10 в час (Dohoda)",
        "default_duration": "Приём заявок открыт (24-72 часа)",
        "default_region": "🇸🇰 Кошице (Словакия)",
        "how_to_tip": "Нажмите на кнопку ниже и отправьте отклик / резюме работодателю.",
        "max_ttl_seconds": 432000,
        "expired_badge": "🔴 [Набор закрыт]",
        "expired_status": "🔴 <b>Статус:</b> Набор закрыт работодателем",
        "expired_button": "🔒 Набор закрыт ➔ Свежие вакансии"
    },
    {
        "url": "https://www.reddit.com/r/udemyfreebies/hot/.rss",
        "type": "course",
        "category": "Бесплатные курсы",
        "badge": "🔥 [Ограничено по времени]",
        "main_tag": "курсы",
        "default_status": "🟢 <b>Статус:</b> Бесплатный купон активен",
        "default_benefit": "100% скидка (Бесплатно вместо $40–$90)",
        "default_duration": "Временный промокод (в профиле навсегда)",
        "default_region": "🌍 Global / Онлайн",
        "how_to_tip": "Нажмите кнопку ниже ➔ убедитесь, что цена $0 (Free) ➔ нажмите «Enroll now». Привязка карты не нужна!",
        "max_ttl_seconds": 172800,
        "expired_badge": "⌛️ [Промокод исчерпан]",
        "expired_status": "⌛️ <b>Статус:</b> Промокод или бесплатный купон истёк",
        "expired_button": "🔒 Промокод истёк ➔ Свежие курсы"
    },
    {
        "url": "https://www.reddit.com/r/FreeGameFindings/hot/.rss",
        "type": "game",
        "category": "Раздача недели (Игры)",
        "badge": "🎮 [100% Бесплатная раздача]",
        "main_tag": "игры",
        "default_status": "🟢 <b>Статус:</b> Раздача активна",
        "default_benefit": "Бесплатно (навсегда в библиотеку)",
        "default_duration": "Ограниченное время акции",
        "default_region": "🌍 Global / Онлайн",
        "how_to_tip": "Войдите в аккаунт платформы (Steam, Epic Games, GOG) и нажмите «Добавить в библиотеку».",
        "max_ttl_seconds": 604800,
        "expired_badge": "⌛️ [Раздача завершена]",
        "expired_status": "⌛️ <b>Статус:</b> Раздача завершена",
        "expired_button": "🔒 Раздача закрыта ➔ Свежие игры"
    },
    {
        "url": "https://www.reddit.com/r/eFreebies/hot/.rss",
        "type": "software",
        "category": "Софт и Полезности",
        "badge": "🎁 [Бесплатный софт / сервис]",
        "main_tag": "софт",
        "default_status": "🟢 <b>Статус:</b> Акция действует",
        "default_benefit": "Бесплатная лицензия / Доступ",
        "default_duration": "Временная промо-акция",
        "default_region": "🌍 Global / Онлайн",
        "how_to_tip": "Перейдите по ссылке и активируйте промокод или зарегистрируйте бесплатную лицензию.",
        "max_ttl_seconds": 259200,
        "expired_badge": "⌛️ [Акция завершена]",
        "expired_status": "⌛️ <b>Статус:</b> Срок действия акции истёк",
        "expired_button": "🔒 Срок истёк ➔ Все скидки"
    },
    {
        "url": "https://www.reddit.com/r/frugalmalefashion/hot/.rss",
        "type": "clothing",
        "category": "Одежда и Шопинг",
        "badge": "👟 [Временная скидка / Распродажа]",
        "main_tag": "одежда",
        "default_status": "🟢 <b>Статус:</b> Скидка действует",
        "default_benefit": "Скидки до 40–60% на брендовые вещи",
        "default_duration": "Ограниченное время распродажи",
        "default_region": "🇪🇺 ЕС / 🌍 Global",
        "how_to_tip": "Перейдите на сайт магазина и используйте скидочный код при оформлении.",
        "max_ttl_seconds": 259200,
        "expired_badge": "⌛️ [Скидка завершена]",
        "expired_status": "⌛️ <b>Статус:</b> Распродажа / промокод завершены",
        "expired_button": "🔒 Скидка завершена ➔ Свежие купоны"
    }
]

def load_json_file(filepath):
    try:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Ошибка чтения {filepath}: {e}")
    return None

def save_json_file(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def escape_html(text):
    if not text:
        return ""
    return html.escape(str(text))

def is_expired_title(title):
    if not title:
        return False
    lower_t = title.lower()
    markers = ["[expired]", "(expired)", "expired", "[ended]", "ended", "oos", "out of stock", "dead deal"]
    return any(m in lower_t for m in markers)

def extract_direct_link(summary, default_link):
    clean_default = default_link.split("?")[0].rstrip("/")
    urls = re.findall(r'https?://[^\s<>"]+[a-zA-Z0-9/]', summary)
    for u in urls:
        clean_u = u.split("?")[0].rstrip("/")
        if "reddit.com" not in u and clean_u != clean_default and "preview.redd.it" not in u:
            return u
    return default_link

def get_base_domain(url):
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/"
    except Exception:
        return url

def validate_link(url, fallback_url=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        resp = requests.get(url, timeout=7, headers=headers, allow_redirects=True, stream=True)
        status = resp.status_code

        if 200 <= status < 400:
            return "OK", url, False

        if status in [401, 403]:
            return "OK", url, False

        if 500 <= status < 600:
            print(f"[Сервер перегружен {status}] Ссылка {url} временно недоступна. Откладываем.")
            return "RETRY", None, False

        if status in [404, 410]:
            if fallback_url and fallback_url != url:
                print(f"[404 Замена] Ссылка {url} вернула 404. Подменяем на {fallback_url}")
                return "OK", fallback_url, True

            base_url = get_base_domain(url)
            if base_url != url:
                print(f"[404 ➔ Главная] Ссылка {url} не найдена. Пробуем главную страницу: {base_url}")
                try:
                    base_resp = requests.get(base_url, timeout=7, headers=headers, allow_redirects=True, stream=True)
                    if base_resp.status_code < 400 or base_resp.status_code in [401, 403]:
                        return "OK", base_url, True
                except Exception:
                    pass

            print(f"[404 Отмена] Ссылка {url} и её домен недоступны. Пост отменён.")
            return "DROP", None, False

        return "OK", url, False

    except requests.exceptions.Timeout:
        print(f"[Таймаут] Сайт {url} не ответил вовремя. Откладываем на следующий цикл.")
        return "RETRY", None, False
    except Exception as e:
        print(f"[Предупреждение] Ошибка проверки {url}: {e}. Оставляем без изменений.")
        return "OK", url, False

def send_telegram_card(deal, is_fallback=False):
    title = escape_html(deal.get("title"))
    category = escape_html(deal.get("category"))
    badge = escape_html(deal.get("badge", f"🎓 [{category}]"))
    status_line = deal.get("status_line", "🟢 <b>Статус:</b> Актуально")
    benefit = escape_html(deal.get("benefit"))
    duration = escape_html(deal.get("duration"))
    region = escape_html(deal.get("region"))
    reqs = escape_html(deal.get("requirements", "Регистрация / Студенческий статус"))
    desc = escape_html(deal.get("description", ""))
    how_to = escape_html(deal.get("how_to", ""))
    link = deal.get("link")

    main_tag = deal.get("main_tag", "скидки")
    extra_tags = deal.get("extra_tags", [])

    tags_list = [f"#{main_tag}@{CHANNEL_USERNAME}"]
    for t in extra_tags:
        tags_list.append(f"#{t}@{CHANNEL_USERNAME}")
    tags_string = " ".join(tags_list)

    text = (
        f"{badge} — <b>{title}</b>\n\n"
        f"{status_line}\n"
        f"💰 <b>Выгода:</b> {benefit}\n"
        f"⏳ <b>Срок:</b> {duration}\n"
        f"🌍 <b>Регион:</b> {region}\n"
        f"📋 <b>Что нужно:</b> {reqs}\n\n"
    )
    if desc:
        text += f"{desc}\n\n"
    if how_to:
        text += f"💡 <b>Как оформить / забрать:</b>\n{how_to}\n\n"
    if is_fallback:
        text += "ℹ️ <i>Прямая страница акции перемещена. Предложение доступно на главной странице или через поиск на сайте сервиса.</i>\n\n"
    text += f"{tags_string}"

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

    # 1. Живая проверка целевого сайта
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

    # 2. Живая проверка Reddit (если первоисточник — Reddit)
    if source_link and "reddit.com" in source_link:
        try:
            reddit_json_url = source_link.rstrip("/") + ".json"
            r_resp = requests.get(reddit_json_url, timeout=7, headers=headers)
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

def update_expired_posts(active_posts):
    remaining_posts = {}

    for post_id, info in active_posts.items():
        is_alive, reason = check_is_deal_still_active(info)
        if not is_alive:
            message_id = info.get("message_id")
            title = escape_html(info.get("title", ""))
            category = escape_html(info.get("category", ""))
            main_tag = info.get("main_tag", "скидки")
            
            expired_badge = info.get("expired_badge", "⌛️ [Акция завершена]")
            expired_status = info.get("expired_status", "⌛️ <b>Статус:</b> Предложение больше не активно")
            button_label = info.get("expired_button", "🔒 Завершено ➔ Все посты")

            print(f"[ЖИВАЯ ПРОВЕРКА] Пост {message_id} ('{title}') закрывается: {reason}")

            updated_text = (
                f"{expired_badge} — <b><s>{title}</s></b>\n\n"
                f"{expired_status} ({reason}).\n\n"
                f"📂 <b>Категория:</b> {category}\n"
                f"ℹ️ <i>Следите за новыми предложениями в канале по тегу ниже или в закрепленном сообщении!</i>\n\n"
                f"#{main_tag}@{CHANNEL_USERNAME}"
            )

            reply_markup = {
                "inline_keyboard": [
                    [
                        {"text": button_label, "url": f"https://t.me/{CHANNEL_USERNAME}?q=%23{main_tag}"}
                    ]
                ]
            }

            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/editMessageText"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "message_id": message_id,
                "text": updated_text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
                "reply_markup": reply_markup
            }

            try:
                requests.post(url, json=payload, timeout=10)
                time.sleep(1.0)
            except Exception as e:
                print(f"Ошибка обновления сообщения {message_id}: {e}")
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
    max_dynamic_allowed = 35 if is_initial_fill else 3

    print(f"Запуск бота. Режим первичного наполнения: {is_initial_fill} (Лимит динамических постов: {max_dynamic_allowed})")

    # Шаг 1: Проверяем актуальность ранее опубликованных динамических постов
    active_posts = update_expired_posts(active_posts)

    # Шаг 2: Каталог постоянных программ (все 20 выверенных программ)
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

    # Шаг 3: Мониторинг динамических источников (вакансии, курсы, игры, софт, одежда)
    dynamic_published = 0
    now = time.time()

    for feed_info in DYNAMIC_FEEDS:
        if dynamic_published >= max_dynamic_allowed:
            break

        try:
            feed = feedparser.parse(feed_info["url"], agent="Mozilla/5.0")
            for entry in feed.entries:
                if dynamic_published >= max_dynamic_allowed:
                    break

                post_id = entry.get("id") or entry.get("link")
                if not post_id or post_id in processed_ids:
                    continue

                if is_expired_title(entry.title):
                    new_processed.add(post_id)
                    continue

                direct_link = extract_direct_link(entry.get("summary", ""), entry.link)
                status, final_url, is_fallback = validate_link(direct_link, fallback_url=entry.link)

                if status == "DROP":
                    new_processed.add(post_id)
                    continue
                elif status == "RETRY":
                    continue

                card = {
                    "id": post_id,
                    "title": entry.title,
                    "category": feed_info["category"],
                    "badge": feed_info["badge"],
                    "main_tag": feed_info["main_tag"],
                    "status_line": feed_info["default_status"],
                    "benefit": feed_info["default_benefit"],
                    "duration": feed_info["default_duration"],
                    "region": feed_info["default_region"],
                    "requirements": "Учётная запись платформы / студенческий",
                    "description": "Свежее предложение, проверенное ботом.",
                    "how_to": feed_info["how_to_tip"],
                    "link": final_url,
                    "extra_tags": ["горящее"]
                }

                success, message_id = send_telegram_card(card, is_fallback=is_fallback)
                if success:
                    new_processed.add(post_id)
                    dynamic_published += 1

                    max_ttl = now + feed_info.get("max_ttl_seconds", 345600)
                    if message_id:
                        active_posts[post_id] = {
                            "message_id": message_id,
                            "title": entry.title,
                            "category": feed_info["category"],
                            "main_tag": feed_info["main_tag"],
                            "target_link": final_url,
                            "source_link": entry.link,
                            "type": feed_info.get("type", "promo"),
                            "posted_at": now,
                            "max_ttl": max_ttl,
                            "expired_badge": feed_info.get("expired_badge", "⌛️ [Акция завершена]"),
                            "expired_status": feed_info.get("expired_status", "⌛️ <b>Статус:</b> Предложение больше не активно"),
                            "expired_button": feed_info.get("expired_button", "🔒 Завершено ➔ Все посты")
                        }
        except Exception as e:
            print(f"Ошибка при обработке {feed_info['url']}: {e}")

    save_json_file(HISTORY_FILE, list(new_processed)[-1500:])
    save_json_file(ACTIVE_POSTS_FILE, active_posts)
    print(f"Сбор завершён. Опубликовано динамических постов: {dynamic_published}. Активных на мониторинге: {len(active_posts)}")

if __name__ == "__main__":
    main()
