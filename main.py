import os
import json
import time
import re
import feedparser
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
HISTORY_FILE = "data/processed_ids.json"

CHANNEL_USERNAME = TELEGRAM_CHAT_ID.replace("@", "") if TELEGRAM_CHAT_ID else "discounts4students"

# Золотой фонд студенческих программ: Кошице, Словакия, Европа и глобальный софт
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
        "link": "https://www.zssk.sk/bezplatna-preprava/",
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
        "link": "https://www.dpmk.sk/prepravne-podmienky-a-tarifa",
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
        "description": "Из Кошице удобно путешествовать в Краков, Будапешт, Прагу и Вену. Автобусы FlixBus и желтые поезда RegioJet дают официальные студенческие скидки по промокодам ISIC.",
        "how_to": "1. Зайдите в приложение ISIC и сгенерируйте персональный купон FlixBus на 10-15%.\n2. В RegioJet выберите тариф «Študent do 26 rokov» при покупке билета.",
        "link": "https://www.flixbus.sk/isic",
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
        "link": "https://www.isic.org/",
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
        "benefit": "Постоянная скидка 10% на все заказы",
        "duration": "Круглый год на весь период учёбы",
        "region": "🇸🇰 Словакия, 🇪🇺 ЕС",
        "requirements": "Студенческая почта или верификация через UNiDAYS",
        "description": "Брендовые кроссовки (Nike, New Balance, adidas) и базовый гардероб. Студенческий код действует постоянно и суммируется со многими распродажами.",
        "how_to": "Перейдите на страницу ASOS Student, введите учебную почту и получите личный промокод на скидку.",
        "link": "https://www.asos.com/discover/students/asosteam/",
        "extra_tags": ["одежда", "стиль", "кроссовки"]
    }
]

# Динамические потоки горячих акций (игры, курсы)
DYNAMIC_FEEDS = [
    {
        "url": "https://www.reddit.com/r/udemyfreebies/new/.rss",
        "category": "🔥 Бесплатные курсы",
        "badge": "🔥 [Ограничено по времени: 24–48ч]",
        "main_tag": "курсы",
        "default_benefit": "100% скидка (Бесплатно вместо $40–$90)",
        "default_duration": "24–48 часов по промокоду (в профиле навсегда)",
        "default_region": "🌍 Global / Онлайн",
        "how_to_tip": "Нажмите кнопку «Забрать предложение» ➔ убедитесь, что цена $0 ➔ нажмите «Записаться». Привязка карты не нужна!"
    },
    {
        "url": "https://www.reddit.com/r/FreeGameFindings/new/.rss",
        "category": "🎮 Раздача недели (Игры)",
        "badge": "🎮 [100% Бесплатная раздача]",
        "main_tag": "игры",
        "default_benefit": "Бесплатно (навсегда в библиотеку)",
        "default_duration": "Ограниченное время (обычно до четверга)",
        "default_region": "🌍 Global / Онлайн",
        "how_to_tip": "Войдите в аккаунт платформы (Steam, Epic Games, GOG) и нажмите «Забрать / Добавить в библиотеку»."
    }
]

def load_processed_ids():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def save_processed_ids(ids):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    recent_ids = list(ids)[-1000:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(recent_ids, f, indent=2, ensure_ascii=False)

def escape_html(text):
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def extract_direct_link(summary_html, fallback_url):
    if not summary_html:
        return fallback_url
    found_links = re.findall(r'href=[\"\']([^\"\']+)[\"\']', summary_html)
    for link in found_links:
        if "reddit.com" not in link and not link.startswith("/"):
            return link
    return fallback_url

def send_telegram_card(deal):
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
    text += f"{tags_string}"

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🔗 Забрать предложение", "url": link}
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
        print(f"Отправка '{title[:35]}...': HTTP {response.status_code}")
        time.sleep(1.5)  # Лимит Telegram
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return False

def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ОШИБКА: Токен или ID канала не заданы.")
        return

    processed_ids = load_processed_ids()
    new_processed = set(processed_ids)

    # 1. При первом старте (когда память пустая) отправятся все 20 постов
    for deal in EVERGREEN_DEALS:
        deal_id = deal["id"]
        if deal_id not in processed_ids:
            print(f"Публикация из каталога: {deal['title']}")
            if send_telegram_card(deal):
                new_processed.add(deal_id)

    # 2. Ненавязчивый мониторинг свежих раздач (до 2 постов за запуск)
    for feed_info in DYNAMIC_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"], agent="Mozilla/5.0")
            for entry in feed.entries[:2]:
                post_id = entry.get("id") or entry.get("link")
                if not post_id or post_id in processed_ids:
                    continue

                target_link = extract_direct_link(entry.get("summary", ""), entry.link)

                card = {
                    "id": post_id,
                    "title": entry.title,
                    "category": feed_info["category"],
                    "badge": feed_info["badge"],
                    "main_tag": feed_info["main_tag"],
                    "benefit": feed_info["default_benefit"],
                    "duration": feed_info["default_duration"],
                    "region": feed_info["default_region"],
                    "requirements": "Учётная запись платформы / купон",
                    "description": "Свежее предложение, обнаруженное в сообществе.",
                    "how_to": feed_info["how_to_tip"],
                    "link": target_link,
                    "extra_tags": ["горящее", "акция"]
                }

                if send_telegram_card(card):
                    new_processed.add(post_id)
        except Exception as e:
            print(f"Ошибка при обработке {feed_info['url']}: {e}")

    save_processed_ids(new_processed)
    print("Сбор и публикация успешно завершены.")

if __name__ == "__main__":
    main()
