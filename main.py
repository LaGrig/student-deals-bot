import os
import json
import time
import re
from urllib.parse import urlparse
import feedparser
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
HISTORY_FILE = "data/processed_ids.json"
ACTIVE_POSTS_FILE = "data/active_posts.json"

CHANNEL_USERNAME = TELEGRAM_CHAT_ID.replace("@", "") if TELEGRAM_CHAT_ID else "discounts4students"

# 20 выверенных студенческих программ: Кошице, Словакия, Европа и софт
EVERGREEN_DEALS = [
    {
        "id": "sk_trains_free",
        "title": "Бесплатные поезда по Словакии для студентов (ŽSSK)",
        "category": "Транспорт и Путешествия",
        "main_tag": "словакия",
        "benefit": "100% бесплатно во 2-м классе всех поездов ŽSSK",
        "duration": "На весь период дневной формы обучения (до 26 лет)",
        "region": "🇸🇰 Словакия (Кошице, Братислава, Татры)",
        "requirements": "Студенческий билет с чипом ISIC (вузы TUKE, UPJŠ и др.)",
        "description": "Легендарная льгота в Словакии: бесплатный проезд во всех поездах государственной железной дороги по всей стране. Поездки из Кошице в горы Высокие Татры, Братиславу или к границам не стоят ни цента.",
        "how_to": "1. Оформите студенческий ISIC в вашем вузе (TUKE, UPJŠ).\n2. В кассе ŽSSK на вокзале Кошице оформите регистрацию (Preukaz pre študenta).\n3. Оформляйте бесплатные нулевые билеты на сайте zssk.sk или в приложении Ideme vlakom.",
        "link": "https://www.zssk.sk/bezplatna-preprava/studenti/",
        "extra_tags": ["кошице", "поезда", "isic"]
    },
    {
        "id": "kosice_dpmk_transport",
        "title": "Студенческий проездной в Кошице (DPMK) со скидкой 50%",
        "category": "Транспорт и Город",
        "main_tag": "кошице",
        "benefit": "Скидка 50% на все билеты и месячные проездные",
        "duration": "На учебный год (продление по ISIC)",
        "region": "🇸🇰 Кошице (Словакия)",
        "requirements": "Студенческая карта ISIC с активированным транспортным чипом",
        "description": "Городской транспорт Кошице (трамваи и автобусы DPMK) для студентов стоит ровно вполовину дешевле. Выгоднее всего оформить электронный проездной (Mesačník) прямо на карту ISIC.",
        "how_to": "1. Активируйте транспортный чип ISIC в университетском терминале.\n2. В приложении DPMK или в кассах на Bardejovská / Rooseveltova пополните студенческий проездной.",
        "link": "https://www.dpmk.sk/prepravny-poriadok/vybavovanie-studentskych-zliav",
        "extra_tags": ["словакия", "транспорт", "dpmk"]
    },
    {
        "id": "sk_isic_jedalne",
        "title": "Студенческие обеды в Кошице по ISIC за €1.80–€2.50",
        "category": "Лайфхаки и Еда",
        "main_tag": "кошице",
        "benefit": "Горячий комплексный обед за ~€2 вместо €7–€9",
        "duration": "Ежедневно в учебные дни",
        "region": "🇸🇰 Кошице (столовые TUKE и UPJŠ)",
        "requirements": "Карта ISIC дневной формы обучения",
        "description": "Государство в Словакии субсидирует питание студентов. В студенческих столовых (študentské jedálne на Jedlíkova, Němcovej, Medická) по карте ISIC можно полноценно пообедать (первое, второе и напиток) всего за пару евро.",
        "how_to": "Пополните свой счет питания через систему университета (MAIS / AiS2) и прикладывайте ISIC на кассе столовой.",
        "link": "https://jedalen.tuke.sk/",
        "extra_tags": ["словакия", "еда", "isic"]
    },
    {
        "id": "kosice_tabacka_usmev",
        "title": "Студенческий досуг в Кошице: Tabačka Kulturfabrik и Kino Úsmev",
        "category": "Ивенты и Досуг",
        "main_tag": "кошице",
        "benefit": "Скидки до 40% на концерты, фестивали и кино",
        "duration": "Постоянно по студенческому билету",
        "region": "🇸🇰 Кошице (Словакия)",
        "requirements": "Карта ISIC любого вуза",
        "description": "Главные точки притяжения молодёжи Кошице. Культурный центр Tabačka Kulturfabrik (живые концерты, фестивали, воркшопы) и культовый артхаусный кинотеатр Kino Úsmev предлагают специальные студенческие цены.",
        "how_to": "Выбирайте тариф «Zľavnený / Študent» при покупке онлайн на сайтах площадок или показывайте ISIC в кассе.",
        "link": "https://tabacka.sk/",
        "extra_tags": ["словакия", "ивенты", "концерты"]
    },
    {
        "id": "sk_student_brigady",
        "title": "Работа для студентов в Словакии (Dohoda o brigáde): налоговый бонус",
        "category": "Работа и Доход",
        "main_tag": "работа",
        "benefit": "До €200 в месяц БЕЗ вычета налогов",
        "duration": "До 20 часов в неделю (легко совмещать с парами)",
        "region": "🇸🇰 Словакия (Кошице, Прешов и др.)",
        "requirements": "Справка об обучении на дневной форме (до 26 лет)",
        "description": "В Словакии действует специальный студенческий контракт (Dohoda o brigádnickej práci študentov). Подписав форму об отказе от налогообложения (Vyhlásenie), вы получаете чистыми всю сумму заработка до 200€ без удержания социальных взносов.",
        "how_to": "Ищите вакансии со статусом «Brigáda pre študentov» на порталах Profesia.sk и Kariera.sk, в договоре обязательно укажите применение налогового бонуса.",
        "link": "https://www.profesia.sk/praca/kosice/brigady/",
        "extra_tags": ["словакия", "кошице", "стажировки"]
    },
    {
        "id": "flixbus_regiojet_discounts",
        "title": "Скидки 10–15% на FlixBus и поезда RegioJet по ISIC из Кошице",
        "category": "Путешествия по Европе",
        "main_tag": "путешествия",
        "benefit": "Скидки 10-15% на междугородние и международные рейсы",
        "duration": "Круглый год",
        "region": "🇪🇺 Европа (маршруты из Кошице в Чехию, Польшу, Австрию)",
        "requirements": "Карта ISIC",
        "description": "Из Кошице удобно путешествовать в Краков, Будапешт, Прагу и Вену. Автобусы FlixBus и поезда RegioJet дают официальные студенческие скидки по купонам ISIC.",
        "how_to": "1. Авторизуйтесь на словацком портале ISIC (isic.sk) или в приложении.\n2. Сгенерируйте персональный купон FlixBus на 10-15%.\n3. Примените код в корзине при покупке билета на flixbus.sk.",
        "link": "https://isic.sk/zlavy-na-slovensku/",
        "extra_tags": ["европа", "поезда", "flixbus"]
    },
    {
        "id": "europe_isic_benefits",
        "title": "Карта ISIC в Европе: бесплатные музеи, скидки и хостелы",
        "category": "Путешествия по Европе",
        "main_tag": "европа",
        "benefit": "Скидки до 50% или бесплатный вход в главные музеи Европы",
        "duration": "1 календарный год",
        "region": "🇪🇺 ЕС (Вена, Будапешт, Прага, Рим, Париж)",
        "requirements": "Пластиковая или цифровая карта ISIC",
        "description": "Карта студента открывает двери во все государственные музеи и достопримечательности ЕС с огромными льготами (в Вене и Париже многие музеи для студентов ЕС до 26 лет бесплатны).",
        "how_to": "Всегда держите карту ISIC при себе и проверяйте раздел скидок на официальном сайте ISIC перед поездкой.",
        "link": "https://www.isic.org/discounts/",
        "extra_tags": ["путешествия", "isic", "скидки"]
    },
    {
        "id": "lowcost_flights_kosice",
        "title": "Дешёвые перелёты по Европе из Кошице, Будапешта и Кракова",
        "category": "Путешествия по Европе",
        "main_tag": "путешествия",
        "benefit": "Авиабилеты по Европе от €12 до €25",
        "duration": "Регулярные распродажи лоукостеров",
        "region": "🇪🇺 Вылеты из Кошице (KSC), Будапешта (BUD) и Кракова (KRK)",
        "requirements": "Молодежные и стандартные тарифы Ryanair / Wizz Air",
        "description": "Из аэропорта Кошице летают прямые рейсы в Вену, Лондон, Дублин. А за 3 часа на автобусе можно добраться до Будапешта или Кракова, откуда открываются сотни направлений по всей Европе от €10.",
        "how_to": "Используйте агрегаторы Skyscanner и Google Flights в режиме «Везде», выкупайте билеты за 3–5 недель до вылета.",
        "link": "https://www.airportkosice.sk/sk",
        "extra_tags": ["авиа", "лоукостеры", "европа"]
    },
    {
        "id": "fusion_360_edu",
        "title": "Autodesk Fusion 360 (CAD / 3D-моделирование)",
        "category": "3D и Инженерия",
        "main_tag": "cad",
        "benefit": "Бесплатно (обычная цена: ~$545/год)",
        "duration": "1 год с ежегодным продлением на весь период учебы",
        "region": "🌍 Global (актуально для инженеров TUKE и др.)",
        "requirements": "Справка об обучении или фото студенческого билета",
        "description": "Профессиональный пакет для 3D-моделирования, инженерных симуляций механики и подготовки моделей к ЧПУ/3D-печати. Без функциональных ограничений.",
        "how_to": "1. Зайдите на портал Autodesk Education.\n2. Укажите свой вуз и загрузите подтверждение статуса студента (модерация длится от 15 минут).",
        "link": "https://www.autodesk.com/education/edu-software/overview",
        "extra_tags": ["софт", "3d", "инженерия"]
    },
    {
        "id": "jetbrains_all_products",
        "title": "JetBrains All Products Pack (Профессиональные IDE)",
        "category": "Программирование / Софт",
        "main_tag": "dev",
        "benefit": "Бесплатно 100% (обычная цена: $289/год)",
        "duration": "1 год с ежегодным продлением",
        "region": "🌍 Global",
        "requirements": "Студенческая почта вуза или карта ISIC",
        "description": "Лицензии на лучшие среды разработки: IntelliJ IDEA Ultimate, PyCharm Professional, WebStorm, CLion, GoLand, DataGrip и Rider.",
        "how_to": "Откройте страницу JetBrains Free Educational Licenses и подтвердите статус через университетский email или ISIC.",
        "link": "https://www.jetbrains.com/community/education/#students",
        "extra_tags": ["программирование", "софт", "jetbrains"]
    },
    {
        "id": "github_student_pack",
        "title": "GitHub Student Developer Pack (включая Copilot)",
        "category": "ИИ и Разработка",
        "main_tag": "ИИ",
        "benefit": "Бесплатно (пакет ценностью более $200,000)",
        "duration": "На весь период обучения (до 2 лет с продлением)",
        "region": "🌍 Global",
        "requirements": "Студенческая почта или студенческий билет с датой",
        "description": "Крупнейший набор для разработчиков: бесплатный доступ к ИИ-ассистенту GitHub Copilot, бесплатные домены от Namecheap, облачные кредиты DigitalOcean, Canva Pro и более 100 сервисов.",
        "how_to": "Перейдите на GitHub Education, загрузите фото студенческого и разрешите геолокацию в браузере при отправке заявки.",
        "link": "https://education.github.com/pack",
        "extra_tags": ["разработка", "copilot", "софт"]
    },
    {
        "id": "azure_students",
        "title": "Microsoft Azure for Students ($100 на серверы и ИИ)",
        "category": "Облачные сервисы и ИИ",
        "main_tag": "ИИ",
        "benefit": "$100 бесплатных кредитов + бесплатные сервисы",
        "duration": "12 месяцев (возобновляемый)",
        "region": "🌍 Global",
        "requirements": "Студенческая почта вуза",
        "description": "$100 на запуск серверов, баз данных и ИИ-моделей в облаке Microsoft. Главное преимущество: кредитная карта НЕ требуется!",
        "how_to": "Войдите на страницу Azure for Students под своей университетской учетной записью Microsoft.",
        "link": "https://azure.microsoft.com/free/students/",
        "extra_tags": ["облако", "azure", "серверы"]
    },
    {
        "id": "figma_education",
        "title": "Figma Professional для студентов",
        "category": "Дизайн и UI/UX",
        "main_tag": "дизайн",
        "benefit": "Бесплатно (обычная цена: $15/месяц)",
        "duration": "До 2 лет с продлением",
        "region": "🌍 Global",
        "requirements": "Указание учебного заведения и студенческий статус",
        "description": "Полный тариф Figma Professional: неограниченное число проектов, командная работа, общие дизайн-системы и презентации Figma Slides.",
        "how_to": "Зайдите на figma.com/education, нажмите «Apply for free», выберите «Student» и отправьте заявку.",
        "link": "https://www.figma.com/education/",
        "extra_tags": ["figma", "uiux", "дизайн"]
    },
    {
        "id": "canva_pro_student",
        "title": "Canva Pro для студентов",
        "category": "Дизайн и Презентации",
        "main_tag": "дизайн",
        "benefit": "Бесплатно 100% (обычная цена: $120/год)",
        "duration": "На весь период учебы",
        "region": "🌍 Global",
        "requirements": "Студенческий билет или GitHub Student Pack",
        "description": "Премиум-подписка Canva: миллионы платных шаблонов, шрифтов, удаление фона в один клик и встроенный ИИ Magic Studio.",
        "how_to": "Перейдите на страницу Canva for Education и авторизуйтесь через студенческий статус или GitHub Pack.",
        "link": "https://www.canva.com/education/",
        "extra_tags": ["canva", "графика", "презентации"]
    },
    {
        "id": "notion_education",
        "title": "Notion Plus Plan for Education",
        "category": "Продуктивность и Учёба",
        "main_tag": "продуктивность",
        "benefit": "Бесплатно (обычная цена: $10/месяц)",
        "duration": "На весь период владения студенческой почтой",
        "region": "🌍 Global",
        "requirements": "Студенческая почта вуза",
        "description": "Тариф Plus без лимита на загрузку файлов, с бесконечной историей правок конспектов и совместными рабочими пространствами.",
        "how_to": "Смените email в Notion на студенческий → перейдите в «Upgrade» и выберите бесплатный студенческий тариф.",
        "link": "https://www.notion.so/product/notion-for-education",
        "extra_tags": ["notion", "заметки", "учеба"]
    },
    {
        "id": "coursera_student",
        "title": "Coursera for Campus (Студенческий доступ)",
        "category": "Курсы и Обучение",
        "main_tag": "курсы",
        "benefit": "1 бесплатный курс с официальным сертификатом в год",
        "duration": "12 месяцев с возможностью продления",
        "region": "🌍 Global",
        "requirements": "Студенческая почта вашего вуза",
        "description": "Бесплатный доступ к курсам от Google, IBM, Yale и Stanford с получением официального международного сертификата в резюме.",
        "how_to": "Зайдите на Coursera for Campus и подтвердите участие своего университета через почту.",
        "link": "https://www.coursera.org/for-university-and-college-students",
        "extra_tags": ["сертификаты", "курсы", "it"]
    },
    {
        "id": "youtube_premium_student",
        "title": "YouTube Premium + YouTube Music для студентов",
        "category": "Музыка и Видео",
        "main_tag": "подписки",
        "benefit": "Скидка ~50% от стандартной цены",
        "duration": "1 год с ежегодным продлением (до 4 лет учебы)",
        "region": "🇸🇰 Словакия, 🇪🇺 ЕС, 🌍 Global",
        "requirements": "Студенческий билет (верификация через SheerID)",
        "description": "YouTube и YouTube Music без рекламы, фоновое воспроизведение на телефоне при выключенном экране и скачивание треков офлайн.",
        "how_to": "Перейдите на страницу студенческой подписки YouTube и подтвердите статус через форму SheerID.",
        "link": "https://www.youtube.com/premium/student",
        "extra_tags": ["музыка", "youtube", "подписки"]
    },
    {
        "id": "spotify_student",
        "title": "Spotify Premium Student",
        "category": "Музыка и Аудио",
        "main_tag": "подписки",
        "benefit": "Скидка 50% + 1 месяц бесплатно",
        "duration": "До 4 лет (подтверждение раз в 12 месяцев)",
        "region": "🇸🇰 Словакия, 🇪🇺 ЕС, 🌍 Global",
        "requirements": "Студенческий билет (верификация SheerID)",
        "description": "Премиум-доступ к Spotify: миллионы треков и подкастов без рекламы, в максимальном качестве и с прослушиванием офлайн.",
        "how_to": "Откройте страницу Spotify Student и пройдите минутную проверку статуса учащегося через SheerID.",
        "link": "https://www.spotify.com/student/",
        "extra_tags": ["музыка", "spotify", "подписки"]
    },
    {
        "id": "apple_music_tv",
        "title": "Apple Music + Apple TV+ для студентов",
        "category": "Музыка и Кино",
        "main_tag": "подписки",
        "benefit": "Скидка ~50% + бесплатный Apple TV+",
        "duration": "До 48 месяцев (4 года учебы)",
        "region": "🇸🇰 Словакия, 🇪🇺 ЕС, 🌍 Global",
        "requirements": "Верификация через сервис UNiDAYS",
        "description": "Студенческая подписка на Apple Music со скидкой 50%, в которую автоматически входит онлайн-кинотеатр Apple TV+ без доплат.",
        "how_to": "В приложении «Музыка» выберите студенческий тариф и подтвердите статус через UNiDAYS.",
        "link": "https://www.apple.com/apple-music/",
        "extra_tags": ["кино", "музыка", "apple"]
    },
    {
        "id": "asos_student_discount",
        "title": "Скидка 10% на одежду и обувь в ASOS (доставка в ЕС)",
        "category": "Одежда и Стиль",
        "main_tag": "одежда",
        "benefit": "Постоянная скидка 10% на весь ассортимент",
        "duration": "Круглый год на весь период учёбы",
        "region": "🇸🇰 Словакия, 🇪🇺 ЕС",
        "requirements": "Студенческая почта или аккаунт ASOS",
        "description": "Брендовые кроссовки (Nike, New Balance, adidas) и базовый гардероб. Студенческий код действует постоянно и суммируется со многими распродажами.",
        "how_to": "Перейдите на официальную страницу валидации ASOS, укажите страну учёбы и подтвердите статус студента для получения персонального кода.",
        "link": "https://www.asos.com/student-validation",
        "extra_tags": ["одежда", "стиль", "кроссовки"]
    }
]

# Динамические потоки: вакансии (Кошице), курсы, игры, софт, одежда
DYNAMIC_FEEDS = [
    {
        "url": "https://www.profesia.sk/praca/kosice/brigady/?format=rss",
        "type": "vacancy",
        "category": "Работа и Доход",
        "badge": "💼 [Студенческая вакансия: Кошице]",
        "main_tag": "работа",
        "default_benefit": "Оплата от €6 до €10 в час (Dohoda)",
        "default_duration": "Приём заявок открыт (24-72 часа)",
        "default_region": "🇸🇰 Кошице (Словакия)",
        "how_to_tip": "Нажмите на кнопку ниже и отправьте отклик / резюме работодателю.",
        "max_ttl_seconds": 432000,
        "expired_badge": "🔴 [Набор закрыт]",
        "expired_button": "🔒 Набор закрыт ➔ Свежие вакансии"
    },
    {
        "url": "https://www.reddit.com/r/udemyfreebies/hot/.rss",
        "type": "course",
        "category": "Бесплатные курсы",
        "badge": "🔥 [Ограничено по времени]",
        "main_tag": "курсы",
        "default_benefit": "100% скидка (Бесплатно вместо $40–$90)",
        "default_duration": "Временный промокод (в профиле навсегда)",
        "default_region": "🌍 Global / Онлайн",
        "how_to_tip": "Нажмите кнопку ниже ➔ убедитесь, что цена $0 (Free) ➔ нажмите «Enroll now». Привязка карты не нужна!",
        "max_ttl_seconds": 172800,
        "expired_badge": "⌛️ [Промокод исчерпан]",
        "expired_button": "🔒 Промокод истёк ➔ Свежие курсы"
    },
    {
        "url": "https://www.reddit.com/r/FreeGameFindings/hot/.rss",
        "type": "game",
        "category": "Раздача недели (Игры)",
        "badge": "🎮 [100% Бесплатная раздача]",
        "main_tag": "игры",
        "default_benefit": "Бесплатно (навсегда в библиотеку)",
        "default_duration": "Ограниченное время акции",
        "default_region": "🌍 Global / Онлайн",
        "how_to_tip": "Войдите в аккаунт платформы (Steam, Epic Games, GOG) и нажмите «Добавить в библиотеку».",
        "max_ttl_seconds": 604800,
        "expired_badge": "⌛️ [Раздача завершена]",
        "expired_button": "🔒 Раздача закрыта ➔ Свежие игры"
    },
    {
        "url": "https://www.reddit.com/r/eFreebies/hot/.rss",
        "type": "software",
        "category": "Софт и Полезности",
        "badge": "🎁 [Бесплатный софт / сервис]",
        "main_tag": "софт",
        "default_benefit": "Бесплатная лицензия / Доступ",
        "default_duration": "Временная промо-акция",
        "default_region": "🌍 Global / Онлайн",
        "how_to_tip": "Перейдите по ссылке и активируйте промокод или зарегистрируйте бесплатную лицензию.",
        "max_ttl_seconds": 259200,
        "expired_badge": "⌛️ [Акция завершена]",
        "expired_button": "🔒 Срок истёк ➔ Все скидки"
    },
    {
        "url": "https://www.reddit.com/r/frugalmalefashion/hot/.rss",
        "type": "clothing",
        "category": "Одежда и Шопинг",
        "badge": "👟 [Временная скидка / Распродажа]",
        "main_tag": "одежда",
        "default_benefit": "Скидки до 40–60% на брендовые вещи",
        "default_duration": "Ограниченное время распродажи",
        "default_region": "🇪🇺 ЕС / 🌍 Global",
        "how_to_tip": "Перейдите на сайт магазина и используйте скидочный код при оформлении.",
        "max_ttl_seconds": 259200,
        "expired_badge": "⌛️ [Скидка завершена]",
        "expired_button": "🔒 Скидка завершена ➔ Свежие купоны"
    }
]

def load_json_file(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {} if "active" in filename else []
    return {} if "active" in filename else []

def save_json_file(filename, data):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def escape_html(text):
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def is_expired_title(title):
    lower = title.lower()
    expired_markers = ["[expired]", "(expired)", "[ended]", "(ended)", "[closed]", "[oos]", "out of stock"]
    return any(marker in lower for marker in expired_markers)

def extract_direct_link(summary_html, fallback_url):
    if not summary_html:
        return fallback_url
    found_links = re.findall(r'href=[\"\']([^\"\']+)[\"\']', summary_html)
    for link in found_links:
        if "reddit.com" not in link and not link.startswith("/"):
            return link
    return fallback_url

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
            print(f"[WAF/Защита {status}] Ссылка {url} активна для обычных браузеров.")
            return "OK", url, False

        if 500 <= status < 600:
            print(f"[Сервер перегружен {status}] Ссылка {url} временно недоступна. Откладываем.")
            return "RETRY", None, False

        if status in [404, 410]:
            if fallback_url and fallback_url != url:
                print(f"[404 ➔ Резервная ссылка] Ссылка {url} вернула 404. Подменяем на {fallback_url}")
                return "OK", fallback_url, True

            base_url = get_base_domain(url)
            if base_url != url:
                print(f"[404 ➔ Главная] Прямой адрес {url} не найден. Пробуем главную страницу: {base_url}")
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
        # Автоматическая защита от лимитов Telegram (HTTP 429)
        if response.status_code == 429:
            retry_after = response.json().get("parameters", {}).get("retry_after", 10)
            print(f"[Лимит Telegram 429] Ожидание {retry_after} секунд...")
            time.sleep(retry_after + 1)
            response = requests.post(url, json=payload, timeout=15)

        print(f"Отправка '{title[:35]}...': HTTP {response.status_code}")
        time.sleep(2.5)  # Безопасная пауза между отправками
        if response.status_code == 200:
            res_data = response.json()
            message_id = res_data.get("result", {}).get("message_id")
            return True, message_id
        return False, None
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return False, None

def check_is_deal_still_active(info):
    """
    ДЕЙСТВИТЕЛЬНАЯ ЖИВАЯ ПРОВЕРКА АКТУАЛЬНОСТИ:
    1. Проверяет реальную страницу на маркеры закрытия ('nie je aktuálna', 404)
    2. Проверяет Reddit-пост на наличие флейра 'Expired'
    3. Применяет страховочный таймер (max_ttl), если сайт не вернул явных маркеров
    """
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

    # 1. Живая проверка целевой страницы (вакансии Profesia.sk)
    if target_link:
        try:
            resp = requests.get(target_link, timeout=7, headers=headers, allow_redirects=True, stream=True)
            if resp.status_code in [404, 410]:
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

    # 2. Живая проверка первоисточника (Reddit flairs для курсов и игр)
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
                    if any(m in flair or m in title for m in ["expired", "ended", "closed", "oos", "dead"]):
                        return False, "Сообщество пометило акцию как завершённую (Expired)"
        except Exception:
            pass

    return True, "Активно"

def update_expired_posts(active_posts):
    """Обновляет статус устаревших постов в Telegram на основе живой проверки"""
    remaining_posts = {}

    for post_id, info in active_posts.items():
        is_alive, reason = check_is_deal_still_active(info)
        
        if not is_alive:
            message_id = info.get("message_id")
            title = escape_html(info.get("title", ""))
            category = escape_html(info.get("category", ""))
            main_tag = info.get("main_tag", "скидки")
            badge = info.get("expired_badge", "⌛️ [Акция завершена]")
            button_label = info.get("expired_button", "🔒 Завершено ➔ Все посты")

            print(f"[ЖИВАЯ ПРОВЕРКА] Пост {message_id} ('{title}') закрывается: {reason}")

            updated_text = (
                f"{badge} — <b>{title}</b>\n\n"
                f"📂 <b>Категория:</b> {category}\n"
                f"⚠️ <b>Статус:</b> Предложение больше не активно ({reason}).\n\n"
                f"<i>Следите за новыми актуальными предложениями на канале!</i>\n\n"
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

    # ДЕТЕКТОР СТАРТОВОГО НАПОЛНЕНИЯ:
    # Если processed_ids пуст (канал только что очищен), включается режим ПОЛНОГО НАПОЛНЕНИЯ.
    # В этом режиме выгружается ВСЯ база постоянных программ (20 постов) И ВСЕ доступные динамические предложения (до 35 шт).
    is_initial_fill = (len(processed_ids) == 0)
    max_dynamic_allowed = 35 if is_initial_fill else 3

    print(f"Запуск бота. Режим первичного наполнения: {is_initial_fill} (Лимит динамических постов: {max_dynamic_allowed})")

    # 1. ЖИВАЯ ПРОВЕРКА И ОБНОВЛЕНИЕ СТАТУСОВ РАНЕЕ ОПУБЛИКОВАННЫХ ПОСТОВ
    active_posts = update_expired_posts(active_posts)

    # 2. КАТАЛОГ ПОСТОЯННЫХ ПРОГРАММ (все 20 проверенных ссылок выгружаются разом)
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

    # 3. ДИНАМИЧЕСКИЕ ПОТОКИ: ВАКАНСИИ (Кошице), КУРСЫ, ИГРЫ, ОДЕЖДА
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
                    "benefit": feed_info["default_benefit"],
                    "duration": feed_info["default_duration"],
                    "region": feed_info["default_region"],
                    "requirements": "Учётная запись платформы / студенческий",
                    "description": "Свежее предложение, обнаруженное в сообществе.",
                    "how_to": feed_info["how_to_tip"],
                    "link": final_url,
                    "extra_tags": ["горящее"]
                }

                success, message_id = send_telegram_card(card, is_fallback=is_fallback)
                if success:
                    new_processed.add(post_id)
                    dynamic_published += 1

                    # Регистрируем пост для живого мониторинга актуальности
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
                            "expired_button": feed_info.get("expired_button", "🔒 Завершено ➔ Все посты")
                        }

        except Exception as e:
            print(f"Ошибка при обработке {feed_info['url']}: {e}")

    # Сохраняем состояние
    save_json_file(HISTORY_FILE, list(new_processed)[-1500:])
    save_json_file(ACTIVE_POSTS_FILE, active_posts)
    print(f"Сбор завершён. Опубликовано динамических постов: {dynamic_published}. Активных на мониторинге: {len(active_posts)}")

if __name__ == "__main__":
    main()
