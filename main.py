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

# 24 выверенные программы: полный охват категорий
EVERGREEN_DEALS = [
    {
        'benefit': '100% бесплатно во 2-м классе всех поездов ŽSSK',
        'category': 'Транспорт и Путешествия',
        'description': 'Легендарная льгота в Словакии: бесплатный проезд во 2-м классе поездов государственной компании ŽSSK (RegioJet и EuroCity требуют символической доплаты). Оформить можно на любом крупном вокзале.',
        'duration': 'На весь период обучения в вузе',
        'extra_tags': ['кошице', 'поезда', 'isic'],
        'how_to': '1. Возьмите в деканате справку об обучении (Potvrdenie o návšteve školy) или карту ISIC.\n2. В кассе ŽSSK (на вокзале в Кошице) оформите «Preukaz pre žiaka/študenta».\n3. Покупайте «нулевые» билеты через кассу или приложение Ideme vlakom.',
        'id': 'sk_trains_free',
        'link': 'https://www.zssk.sk/en/zero-fare/',
        'main_tag': 'словакия',
        'region': '🇸🇰 Вся Словакия',
        'requirements': 'Студент дневной формы обучения словацкого вуза до 26 лет',
        'title': 'Бесплатные поезда по Словакии для студентов (ŽSSK)'
    },
    {
        'benefit': 'Скидка 50% на разовые билеты и проездные карты',
        'category': 'Транспорт и Город',
        'description': 'Городской транспорт в Кошице (автобусы и трамваи DPMK) для студентов стоит ровно вполовину дешевле. Выгоднее всего оформить электронный проездной (Mesačník) прямо на карту ISIC.',
        'duration': 'На учебный год (продление по ISIC)',
        'extra_tags': ['словакия', 'транспорт', 'dpmk'],
        'how_to': '1. Активируйте транспортный чип ISIC в университетском терминале.\n2. В приложении DPMK или в кассах на Bardejovská / Rooseveltova пополните студенческий проездной.',
        'id': 'kosice_dpmk_transport',
        'link': 'https://www.dpmk.sk/prepravny-poriadok/vybavovanie-studentskych-zliav',
        'main_tag': 'кошице',
        'region': '🇸🇰 Кошице (Словакия)',
        'requirements': 'Студенческая карта ISIC с активированным транспортным чипом',
        'title': 'Студенческий проездной в Кошице (DPMK) со скидкой 50%'
    },
    {
        'benefit': 'Горячий комплексный обед за ~€2 вместо €7–€9',
        'category': 'Лайфхаки и Еда',
        'description': 'Государство в Словакии субсидирует питание студентов. В студенческих столовых (študentské jedálne на Jedlíkova, Němcovej, Medická) по карте ISIC можно полноценно пообедать (первое, второе и напиток) всего за пару евро.',
        'duration': 'Ежедневно в учебные дни',
        'extra_tags': ['словакия', 'еда', 'isic'],
        'how_to': 'Пополните свой счет питания через систему университета (MAIS / AiS2) и прикладывайте ISIC на кассе столовой.',
        'id': 'sk_isic_jedalne',
        'link': 'https://jedalen.tuke.sk/',
        'main_tag': 'кошице',
        'region': '🇸🇰 Кошице (столовые TUKE и UPJŠ)',
        'requirements': 'Карта ISIC дневной формы обучения',
        'title': 'Студенческие обеды в Кошице по ISIC за €1.80–€2.50'
    },
    {
        'benefit': 'Скидка 10% на все напитки по студенческому билету / ISIC',
        'category': 'Вкусное',
        'description': 'Кофейня Starbucks в ТЦ Aupark Košice предоставляет официальную студенческую скидку на весь кофе, сезонные напитки и выпечку при предъявлении студенческого билета.',
        'duration': 'Круглый год',
        'extra_tags': ['вкусное'],
        'how_to': 'Предъявите студенческий билет или карту ISIC бариста на кассе перед оплатой заказа.',
        'id': 'starbucks_student_ke',
        'link': 'https://www.starbucks.sk/',
        'main_tag': 'вкусное',
        'region': '🇸🇰 Кошице (Aupark Košice, Námestie osloboditeľov 1)',
        'requirements': 'Студенческий билет или карта ISIC',
        'title': 'Скидка 10% на кофе и напитки в Starbucks Košice'
    },
    {
        'benefit': 'Студенческое комбо и специальные цены на бургеры и кофе',
        'category': 'Вкусное',
        'description': 'McDonalds на Protifašistických bojovníkov и в ТЦ Optima/Aupark предлагает специальные комбо-цены для студентов (McMenu по льготному тарифу) при сканировании студенческого статуса.',
        'duration': 'Постоянная программа',
        'extra_tags': ['вкусное'],
        'how_to': 'Сканируйте карту студента на кассе или выберите студенческий купон в киоске самообслуживания.',
        'id': 'mcdonalds_student_ke',
        'link': 'https://www.mcdonalds.sk/menu/',
        'main_tag': 'вкусное',
        'region': '🇸🇰 Кошице (Aupark, Optima, Hlavná)',
        'requirements': 'Студенческий билет',
        'title': 'Студенческие комбо и скидки в McDonald\'s Košice'
    },
    {
        'benefit': 'Скидки до 40% на концерты, фестивали и кино',
        'category': 'Ивенты и Досуг',
        'description': 'Главные культурные пространства Кошице — Tabačka Kulturfabrik и кинотеатр Kino Úsmev — дают постоянные скидки на киносеансы, лекции, спектакли и вечеринки для студентов.',
        'duration': 'Круглый год',
        'extra_tags': ['кошице', 'словакия', 'кино'],
        'how_to': 'Предъявляйте ISIC при покупке билетов в кассе или выбирайте тариф «Študent» онлайн.',
        'id': 'kosice_tabacka_usmev',
        'link': 'https://tabacka.sk/',
        'main_tag': 'ивенты',
        'region': '🇸🇰 Кошице (Gorkého 2 / Kasárenské námestie)',
        'requirements': 'Действующий студенческий билет или ISIC',
        'title': 'Студенческий досуг в Кошице: Tabačka Kulturfabrik и Kino Úsmev'
    },
    {
        'benefit': 'Официальная работа без налога на доход до €200/мес',
        'category': 'Работа и Доход',
        'description': 'Специальный тип трудового договора для студентов дневной формы в Словакии. Вы освобождаетесь от уплаты пенсионных и медицинских взносов с суммы заработка до €200 в месяц.',
        'duration': 'До окончания статуса студента (максимум до 26 лет)',
        'extra_tags': ['словакия', 'кошице', 'стажировки'],
        'how_to': '1. Возьмите в университете справку о статусе студента.\n2. При оформлении на работу подпишите «Oznámenie a čestné vyhlásenie k uplatneniu odvodovej odpočítateľnej položky».',
        'id': 'sk_student_brigady',
        'link': 'https://www.employment.gov.sk/sk/praca-zamestnanost/vztah-zamestnanca-zamestnavatela/dohody-o-pracach-vykonavanych-mimo-pracovneho-pomeru/dohoda-o-brigadnickej-praci-studentov.html',
        'main_tag': 'работа',
        'region': '🇸🇰 Вся Словакия',
        'requirements': 'Студент очного отделения до 26 лет',
        'title': 'Работа для студентов в Словакии (Dohoda o brigádnickej práci študentov)'
    },
    {
        'benefit': 'Скидки 10–15% на междугородние и международные рейсы',
        'category': 'Путешествия по Европе',
        'description': 'Путешествия из Кошице в Прагу, Вену, Будапешт, Краков или Братиславу на автобусах и поездах со студенческой скидкой по карте ISIC.',
        'duration': 'Постоянно круглый год',
        'extra_tags': ['европа', 'поезда', 'flixbus'],
        'how_to': 'При поиске билетов на сайте RegioJet выберите тариф «Študent (ISIC)». Для FlixBus и RegioJet оформляйте студенческий билет на официальных сайтах перевозчиков.',
        'id': 'flixbus_regiojet_discounts',
        'link': 'https://www.flixbus.sk/sluzby/studentske-zlavy',
        'main_tag': 'путешествия',
        'region': '🇪🇺 Словакия и Центральная Европа',
        'requirements': 'Карта ISIC',
        'title': 'Скидки 10–15% на FlixBus и поезда RegioJet'
    },
    {
        'benefit': 'Бесплатный вход или скидка 50% в тысячи музеев Европы',
        'category': 'Путешествия по Европе',
        'description': 'Студенты европейских вузов имеют право на бесплатный или льготный вход в главные музеи Европы: Лувр в Париже, Бельведер в Вене, галерею Уффици во Флоренции и многие другие.',
        'duration': 'До достижения 26 лет',
        'extra_tags': ['путешествия', 'isic', 'скидки'],
        'how_to': 'При бронировании онлайн выбирайте категорию «EU Student under 26» или покажите ISIC на кассе.',
        'id': 'europe_isic_benefits',
        'link': 'https://youth.europa.eu/',
        'main_tag': 'европа',
        'region': '🇪🇺 Страны Евросоюза',
        'requirements': 'Студенческий билет / ISIC европейского университета',
        'title': 'Бесплатные музеи и достопримечательности Европы до 26 лет'
    },
    {
        'benefit': 'Авиабилеты по Европе от €10–€20 (Wizz Air, Ryanair)',
        'category': 'Путешествия по Европе',
        'description': 'Из Кошице (KSC), а также соседних Будапешта и Кракова летают лоукостеры по десяткам направлений. Wizz Air предлагает студенческий тариф и клубные скидки WIZZ Discount Club.',
        'duration': 'Круглый год при раннем бронировании',
        'extra_tags': ['путешествия', 'европа', 'билеты'],
        'how_to': 'Используйте агрегаторы (Skyscanner / Google Flights) с вылетом из Košice, Budapest или Kraków.',
        'id': 'lowcost_flights_kosice',
        'link': 'https://www.airportkosice.sk/sk/lety/odlety',
        'main_tag': 'авиа',
        'region': '✈️ Кошице / Будапешт / Краков',
        'requirements': 'Загранпаспорт и студенческий статус',
        'title': 'Дешёвые путешествия из Кошице: лоукостеры по Европе'
    },
    {
        'benefit': 'Бесплатная лицензия на софт стоимостью $545 в год',
        'category': '3D и Инженерия',
        'description': 'Autodesk предоставляет студентам технических специальностей (особенно актуально для TUKE) полный бесплатный доступ к Fusion 360, AutoCAD, Inventor, Maya и 3ds Max.',
        'duration': 'Возобновляемая годовая подписка на всё время учёбы',
        'extra_tags': ['софт', '3d', 'инженерия'],
        'how_to': '1. Зарегистрируйтесь на образовательном портале Autodesk.\n2. Загрузите фото студенческого или справку с портала MAIS.\n3. Доступ активируется в течение 20 минут.',
        'id': 'fusion_360_edu',
        'link': 'https://www.autodesk.com/education/edu-software/overview',
        'main_tag': 'cad',
        'region': '🌍 Global / Онлайн',
        'requirements': 'Студенческий статус в аккредитованном вузе',
        'title': 'Autodesk Fusion 360 & AutoCAD — бесплатно для студентов'
    },
    {
        'benefit': 'Бесплатный All Products Pack (экономия от $250 до $650 в год)',
        'category': 'Программирование / Софт',
        'description': 'Полный профессиональный пакет сред разработки от JetBrains: IntelliJ IDEA Ultimate, PyCharm Pro, WebStorm, CLion, Rider, DataGrip и другие бесплатно для студентов.',
        'duration': '1 год с ежегодным бесплатным продлением',
        'extra_tags': ['программирование', 'софт', 'jetbrains'],
        'how_to': 'Перейдите на страницу студенческой программы JetBrains и зарегистрируйтесь, указав свой университетский email (@tuke.sk, @upjs.sk) или загрузив фото ISIC.',
        'id': 'jetbrains_all_products',
        'link': 'https://www.jetbrains.com/community/education/#students',
        'main_tag': 'dev',
        'region': '🌍 Global / Онлайн',
        'requirements': 'Университетская почта (.edu / .sk) или карта ISIC',
        'title': 'Бесплатные лицензии JetBrains на все IDE (PyCharm, IntelliJ, WebStorm)'
    },
    {
        'benefit': 'Инструменты разработки и сервисы стоимостью свыше $1000',
        'category': 'ИИ и Разработка',
        'description': 'Легендарный набор разработчика: бесплатный GitHub Copilot (ИИ-ассистент), бесплатные домены Namecheap, кредиты на облачные серверы DigitalOcean, доступ к Canva Pro, JetBrains и десяткам сервисов.',
        'duration': 'На весь период обучения в университете',
        'extra_tags': ['разработка', 'copilot', 'софт'],
        'how_to': 'Авторизуйтесь на GitHub, перейдите в раздел Education, добавьте университетский email и прикрепите фото карты ISIC.',
        'id': 'github_student_pack',
        'link': 'https://education.github.com/pack',
        'main_tag': 'ИИ',
        'region': '🌍 Global / Онлайн',
        'requirements': 'Аккаунт GitHub и подтверждение студенческого статуса',
        'title': 'GitHub Student Developer Pack + бесплатный GitHub Copilot'
    },
    {
        'benefit': '$100 на баланс облака и бесплатный доступ к популярным сервисам',
        'category': 'Облачные сервисы и ИИ',
        'description': 'Microsoft дарит студентам $100 на использование серверов, виртуальных машин, баз данных и ИИ-моделей в облаке Azure без необходимости привязывать банковскую карту.',
        'duration': '12 месяцев с возможностью продления',
        'extra_tags': ['облако', 'azure', 'серверы'],
        'how_to': 'Зайдите на портал Azure for Students и подтвердите статус через студенческий email.',
        'id': 'azure_students',
        'link': 'https://azure.microsoft.com/en-us/free/students/',
        'main_tag': 'ИИ',
        'region': '🌍 Global / Онлайн',
        'requirements': 'Студенческая почта вуза',
        'title': 'Microsoft Azure for Students: $100 бесплатных кредитов на серверы и ИИ'
    },
    {
        'benefit': 'Бесплатный профессиональный тариф Figma Enterprise / Education',
        'category': 'Дизайн и UI/UX',
        'description': 'Главный инструмент продуктового дизайна и совместной работы. Студенческий тариф открывает неограниченное число проектов, командных библиотек и истории версий.',
        'duration': '2 года с правом продления',
        'extra_tags': ['figma', 'uiux', 'дизайн'],
        'how_to': 'Зайдите на страницу Figma Education, заполните форму с названием вуза (TUKE, UPJŠ и др.) и прикрепите фото ISIC.',
        'id': 'figma_education',
        'link': 'https://www.figma.com/education/',
        'main_tag': 'дизайн',
        'region': '🌍 Global / Онлайн',
        'requirements': 'Студенческий статус',
        'title': 'Figma Professional — бесплатно для студентов и дизайнеров'
    },
    {
        'benefit': 'Премиум-доступ к шаблонам, графике и ИИ-генераторам Canva',
        'category': 'Дизайн и Презентации',
        'description': 'Создавайте презентации для пар, курсовых и проектов за считанные минуты с полным набором инструментов Canva Pro.',
        'duration': 'На время учёбы',
        'extra_tags': ['canva', 'графика', 'презентации'],
        'how_to': 'Активируйте через GitHub Student Developer Pack или образовательный аккаунт Canva.',
        'id': 'canva_pro_student',
        'link': 'https://www.canva.com/education/',
        'main_tag': 'дизайн',
        'region': '🌍 Global / Онлайн',
        'requirements': 'Подтверждение через GitHub Pack или edu-почту',
        'title': 'Canva Pro: бесплатный графический редактор для студентов'
    },
    {
        'benefit': 'Бесплатный план Plus без лимитов на блоки и файлы',
        'category': 'Продуктивность и Учёба',
        'description': 'Идеальное рабочее пространство для конспектов, расписания, дедлайнов и подготовки к экзаменам. Студенческий тариф снимает ограничение на загрузку больших файлов.',
        'duration': 'Бессрочно при привязке университетской почты',
        'extra_tags': ['notion', 'заметки', 'учеба'],
        'how_to': 'Зарегистрируйте аккаунт Notion на личную почту, затем в настройках аккаунта смените email на студенческий (@tuke.sk / @upjs.sk) и перейдите на вкладку Upgrade -> Get free student plan.',
        'id': 'notion_education',
        'link': 'https://www.notion.so/product/notion-for-education',
        'main_tag': 'продуктивность',
        'region': '🌍 Global / Онлайн',
        'requirements': 'Студенческая почта вуза',
        'title': 'Notion Plus: бесплатный тариф для студентов на организацию учёбы'
    },
    {
        'benefit': 'Бесплатные курсы от Google, IBM, Stanford и сертификаты за $0',
        'category': 'Курсы и Обучение',
        'description': 'Получайте востребованные навыки в ИТ, маркетинге и аналитике бесплатно. На любой платный курс на Coursera можно подать заявку на финансовую помощь (Financial Aid) и учиться бесплатно с выдачей официального сертификата.',
        'duration': 'Постоянно (на каждый курс подаётся отдельная заявка)',
        'extra_tags': ['курсы', 'образование', 'сертификаты'],
        'how_to': 'На странице курса нажмите на ссылку «Financial Aid Available» рядом с кнопкой записи, укажите статус студента и обоснуйте необходимость бесплатного обучения. Одобрение приходит за 16 дней.',
        'id': 'coursera_student',
        'link': 'https://www.coursera.org/',
        'main_tag': 'продуктивность',
        'region': '🌍 Global / Онлайн',
        'requirements': 'Аккаунт Coursera',
        'title': 'Бесплатные курсы и сертификаты на Coursera через Financial Aid'
    },
    {
        'benefit': 'YouTube без рекламы, фоновый режим и YouTube Music со скидкой 45%',
        'category': 'Музыка и Видео',
        'description': 'Официальная студенческая подписка на YouTube Premium в Словакии стоит вдвое дешевле обычной семейной или индивидуальной подписки.',
        'duration': 'До 4 лет (ежегодная верификация через SheerID)',
        'extra_tags': ['музыка', 'youtube', 'подписки'],
        'how_to': 'Перейдите на страницу оформления студенческой подписки YouTube, выберите университет и подтвердите статус через SheerID.',
        'id': 'youtube_premium_student',
        'link': 'https://www.youtube.com/premium/student',
        'main_tag': 'подписки',
        'region': '🇸🇰 Словакия / ЕС',
        'requirements': 'Студент вуза (подтверждение через SheerID)',
        'title': 'YouTube Premium Student со скидкой 45% (включая YouTube Music)'
    },
    {
        'benefit': 'Скидка 50% на премиум-подписку (€3.49 вместо €6.99 в месяц)',
        'category': 'Музыка и Аудио',
        'description': 'Миллионы треков без рекламы, прослушивание офлайн и высокое качество звука по сниженной студенческой цене.',
        'duration': 'До 4 лет с ежегодным продлением',
        'extra_tags': ['музыка', 'spotify', 'подписки'],
        'how_to': 'Оформите подписку на сайте Spotify Student, пройдя быструю проверку через сервис SheerID.',
        'id': 'spotify_student',
        'link': 'https://www.spotify.com/sk/student/',
        'main_tag': 'подписки',
        'region': '🇸🇰 Словакия / ЕС',
        'requirements': 'Студент дневной формы обучения',
        'title': 'Spotify Premium Student со скидкой 50%'
    },
    {
        'benefit': 'Скидка 50% на музыку + бесплатный доступ к сериалам и фильмам Apple TV+',
        'category': 'Музыка и Кино',
        'description': 'Уникальное предложение от Apple: при оформлении студенческой подписки Apple Music вы бесплатно получаете доступ к стримингу Apple TV+ без доплаты.',
        'duration': 'До 48 месяцев',
        'extra_tags': ['кино', 'музыка', 'apple'],
        'how_to': 'В приложении Apple Music или на сайте выберите план «Студенческий» и подтвердите статус через сервис UNiDAYS.',
        'id': 'apple_music_tv',
        'link': 'https://www.apple.com/sk/apple-music/',
        'main_tag': 'подписки',
        'region': '🇸🇰 Словакия / ЕС',
        'requirements': 'Верификация через UNiDAYS',
        'title': 'Apple Music Student со скидкой 50% + бесплатный Apple TV+'
    },
    {
        'benefit': 'Постоянная скидка 10% на все заказы одежды и обуви',
        'category': 'Одежда и Стиль',
        'description': 'Один из крупнейших европейских интернет-магазинов одежды, обуви и аксессуаров ASOS дарит студентам постоянный персональный промокод на 10% скидку, действующий даже на распродажи.',
        'duration': 'До окончания учёбы',
        'extra_tags': ['одежда', 'стиль', 'кроссовки'],
        'how_to': 'Заполните форму подтверждения студента на сайте ASOS, указав год окончания вуза и университетский email, чтобы получить персональный код.',
        'id': 'asos_student_discount',
        'link': 'https://www.asos.com/discover/students/asosteam/discount/',
        'main_tag': 'одежда',
        'region': '🇪🇺 Доставка в Словакию',
        'requirements': 'Студенческий статус',
        'title': 'Постоянная студенческая скидка 10% на ASOS'
    },
    {
        'benefit': 'Каждую неделю 1–2 полноценные платные игры бесплатно навсегда',
        'category': 'Игры и Раздачи',
        'description': 'Цифровой магазин Epic Games Store каждый четверг в 17:00 (по Братиславе) запускает бесплатную раздачу лицензионных игр. Забрав игру один раз, вы сохраняете её навсегда.',
        'duration': 'Обновление каждый четверг, акция длится 7 дней',
        'extra_tags': ['игры', 'epicgames', 'раздача'],
        'how_to': 'Войдите в аккаунт Epic Games Store, перейдите в раздел «Бесплатные игры» и оформите заказ за 0€.',
        'id': 'epic_games_weekly',
        'link': 'https://store.epicgames.com/ru/free-games',
        'main_tag': 'игры',
        'region': '🌍 Global (ПК)',
        'requirements': 'Учетная запись Epic Games',
        'title': 'Еженедельные бесплатные раздачи ПК-игр в Epic Games Store'
    },
    {
        'benefit': 'Сотни топовых лицензионных игр без необходимости платить',
        'category': 'Игры и Развлечения',
        'description': 'База лучших соревновательных и кооперативных игр в Steam, доступных абсолютно бесплатно: Counter-Strike 2, Dota 2, Apex Legends, Destiny 2, PUBG: Battlegrounds и Team Fortress 2.',
        'duration': 'Бессрочно',
        'extra_tags': ['игры', 'steam', 'онлайн'],
        'how_to': 'Установите клиент Steam, откройте страницу нужной игры и нажмите «Играть бесплатно». Игра навсегда закрепится в вашей библиотеке.',
        'id': 'steam_free_to_play',
        'link': 'https://store.steampowered.com/genre/Free%20to%20Play/',
        'main_tag': 'игры',
        'region': '🌍 Global (Steam)',
        'requirements': 'Аккаунт Steam',
        'title': 'Постоянный каталог бесплатных игр в Steam (Free to Play)'
    },
    {
        'benefit': 'Скидки до 30% на технику, электронику и бесплатная доставка',
        'category': 'Горящие Акции и Скидки',
        'description': 'Карта ISIC в Словакии дает сотни скидок: от покупки билетов в кино до скидок на электронику в Nay / Datart, фастфуд (McDonalds, Subway) и книжные магазины Martinus.',
        'duration': 'В течение срока действия карты',
        'extra_tags': ['горящее', 'словакия', 'кошице', 'скидки'],
        'how_to': '1. Войдите в личный кабинет на alza.sk в раздел alza.sk/student.\n2. Подтвердите статус студента (по номеру карты ISIC или справке из деканата).\n3. Получайте автоматические клубные скидки в корзине.',
        'id': 'isic_extra_hot_deals',
        'link': 'https://www.alza.sk/student',
        'main_tag': 'горящее',
        'region': '🇸🇰 Словакия',
        'requirements': 'Действующая карта ISIC',
        'title': 'Студенческий клуб Alza: скидки до 30% на технику и электронику'
    },
    {
        'benefit': '$200 кредитов DigitalOcean, бесплатные домены .me и SSL-сертификаты',
        'category': 'Бонусы и Студенческие Кредиты',
        'description': 'Дополнительные эксклюзивные предложения для студентов: запуск собственных проектов, пет-проектов и ботов на бесплатном облачном сервере в течение целого года.',
        'duration': '1 год с момента активации',
        'extra_tags': ['горящее', 'софт', 'it', 'серверы'],
        'how_to': 'Активируйте купон из GitHub Student Developer Pack на сайте DigitalOcean или Namecheap.',
        'id': 'github_perks_hot_credits',
        'link': 'https://education.github.com/pack',
        'main_tag': 'горящее',
        'region': '🌍 Global / Онлайн',
        'requirements': 'Студенческий статус (студенческая почта или ISIC)',
        'title': 'Горящие кредиты и лицензии: DigitalOcean, JetBrains и Namecheap'
    }
]

DYNAMIC_FEEDS = [
    # 1. Официальный API еженедельных бесплатных раздач Epic Games Store (СТРОГО 100% бесплатно)
    {
        "url": "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=ru&country=SK&allowCountries=SK",
        "format": "epic_api",
        "type": "game",
        "category": "Игры",
        "badge": "🎮 [Epic Games]",
        "main_tag": "игры",
        "default_benefit": "Бесплатно 100% (Лицензия EGS)",
        "default_duration": "Еженедельная раздача Epic Games",
        "default_region": "Global (Epic Games)",
        "how_to_tip": "Войдите в аккаунт Epic Games и нажмите «Оформить заказ» за 0€.",
        "max_ttl_seconds": 604800
    },
    # 2. Раздачи ПК-игр с GamerPower (СТРОГО Steam / Epic, отсекаем обычный Free-to-play)
    {
        "url": "https://www.gamerpower.com/api/giveaways?platform=pc&type=game&sort-by=date",
        "format": "gamerpower_json",
        "type": "game",
        "category": "Игры",
        "badge": "🎮 [Раздача Steam & Epic]",
        "main_tag": "игры",
        "default_benefit": "Бесплатно 100% (Вместо полной цены)",
        "default_duration": "Ограниченное время раздачи",
        "default_region": "Global (ПК)",
        "how_to_tip": "Перейдите на страницу раздачи и добавьте игру в свою библиотеку.",
        "max_ttl_seconds": 604800
    },
    # 3. Временные 100% скидки на платные игры Steam (отсекаем F2P и посты без прямой ссылки)
    {
        "url": "https://www.reddit.com/r/FreeGamesOnSteam/new.rss",
        "format": "steam_reddit",
        "type": "game",
        "category": "Игры",
        "badge": "🎮 [Steam]",
        "main_tag": "игры",
        "default_benefit": "Бесплатно 100% (Лицензия Steam)",
        "default_duration": "Ограничено по времени",
        "default_region": "Global (Steam)",
        "how_to_tip": "Активируйте ключ или заберите игру через страницу акции в магазине Steam.",
        "max_ttl_seconds": 345600
    },
    # 4. Подработка и стажировки для студентов в Кошице
    {
        "url": "https://www.profesia.sk/praca/kosice/?format=rss&employment_type=brigada",
        "format": "rss",
        "type": "vacancy",
        "category": "Работа",
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
        "format": "rss",
        "type": "vacancy",
        "category": "Работа",
        "badge": "💼 [Студенческая подработка]",
        "main_tag": "работа",
        "default_benefit": "Гибкий график для студентов вузов",
        "default_duration": "До набора кандидатов",
        "default_region": "🇸🇰 Словакия",
        "how_to_tip": "Откликнитесь на вакансию на сайте Brigada.sk, указав студенческий статус.",
        "max_ttl_seconds": 604800
    },
    # 5. Бесплатные курсы и сертификаты с промокодами
    {
        "url": "https://www.reddit.com/r/udemyfreebies/new.rss",
        "format": "rss",
        "type": "promo",
        "category": "Курсы",
        "badge": "🎓 [Курсы с купонами]",
        "main_tag": "курсы",
        "default_benefit": "Бесплатный доступ к курсу (Скидка 100%)",
        "default_duration": "Купон на 1–2 дня или первые 1000 активаций",
        "default_region": "Online (Глобально)",
        "how_to_tip": "Перейдите по ссылке с примененным промокодом и нажмите «Enroll Now» за $0.",
        "max_ttl_seconds": 172800
    },
    # 6. Студенческий гардероб и стиль
    {
        "url": "https://www.reddit.com/r/frugalmalefashion/new.rss",
        "format": "rss",
        "type": "promo",
        "category": "Скидки",
        "badge": "👟 [Одежда и Обувь]",
        "main_tag": "скидки",
        "default_benefit": "Скидки до 60–70% в европейских магазинах",
        "default_duration": "Пока товар есть в наличии (Распродажа)",
        "default_region": "Европа / Доставка в Словакию",
        "how_to_tip": "Используйте промокод на корзине или заказывайте товары из раздела сейла.",
        "max_ttl_seconds": 259200
    },
    # 7. Горящие скидки на технику, софт и сервисы
    {
        "url": "https://www.pepper.it/rss/nuove",
        "format": "rss",
        "type": "promo",
        "category": "Скидки",
        "badge": "🛍 [Скидки на технику/софт]",
        "main_tag": "скидки",
        "default_benefit": "Крупная скидка на электронику / софт",
        "default_duration": "Ограниченная акция",
        "default_region": "Евросоюз",
        "how_to_tip": "Проверьте условия акции на сайте продавца перед покупкой.",
        "max_ttl_seconds": 259200
    },
    # 8. Живая афиша и молодежные события в Кошице (GoOut Košice)
    {
        "url": "https://goout.net/sk/kosice/akcie/lezfhdmkk/",
        "format": "goout_html",
        "type": "event",
        "category": "Ивенты",
        "badge": "🎭 [Ивенты: Кошице]",
        "main_tag": "ивенты",
        "default_benefit": "Студенческие билеты / Вход свободный",
        "default_duration": "Афиша недели в Кошице",
        "default_region": "🇸🇰 Кошице (Tabačka, Kulturpark, Úsmev)",
        "how_to_tip": "Ознакомьтесь с программой и приобретайте билеты по студенческому тарифу на входе или онлайн.",
        "max_ttl_seconds": 604800
    },
    # 9. Городские анонсы и фестивали Кошице (SlovakInfo)
    {
        "url": "https://slovakinfo.sk/afisha-koshicze/",
        "format": "slovakinfo_afisha",
        "type": "event",
        "category": "Ивенты",
        "badge": "📍 [Кошице: Афиша]",
        "main_tag": "ивенты",
        "default_benefit": "Бесплатные фестивали, ярмарки и выставки",
        "default_duration": "Еженедельный дайджест",
        "default_region": "🇸🇰 Кошице",
        "how_to_tip": "Смотрите полную программу недели и время начала на официальной странице анонса.",
        "max_ttl_seconds": 604800
    },
    # 10. Горящие скидки на еду и пиццу в Кошице до 15€ (Zľavomat Košice)
    {
        "url": "https://www.zlavomat.sk/kosice/restauracie-a-bary?filtre[okolie]=24008|20|0|0&filtre[pocet-osob]=1&list=1&radenia=najlacnejsie",
        "format": "zlavomat_html",
        "type": "promo",
        "category": "Вкусное",
        "badge": "🍕 [Вкусное: Кошице]",
        "main_tag": "вкусное",
        "default_benefit": "Обед или пицца со скидкой (до 15€)",
        "default_duration": "Ограниченное количество купонов",
        "default_region": "🇸🇰 Кошице",
        "how_to_tip": "Приобретите купон со скидкой онлайн и покажите его при заказе в заведении.",
        "max_ttl_seconds": 604800
    }
]

TOPIC_RULES = [
    ("софт", ["github", "jetbrains", "azure", "docker", "python", "developer", "код", "git", "api", "ide", "vscode", "ai", "copilot", "chatgpt", "openai", "claude", "gemini", "нейросеть", "llm", "figma", "canva", "adobe", "дизайн", "ui/ux", "graphics", "3d", "blender", "fusion 360", "autocad", "autodesk", "cad", "solidworks", "инженерия", "notion", "office 365", "excel", "obsidian", "учеба", "конспекты"]),
    ("игры", ["steam", "epic games", "раздача", "игры", "гейминг", "бесплатно игра"]),
    ("курсы", ["coursera", "udemy", "сертификат", "обучение", "лекции"]),
    ("скидки", ["spotify", "apple music", "youtube premium", "музыка", "стриминг", "подписка", "asos", "nike", "adidas", "кроссовки", "гардероб", "одежда"]),
    ("кошице", ["кошице", "košice", "kosice", "dpmk", "tuke", "upjs", "словакия", "slovensko", "slovakia", "bratislava", "zssk", "isic", "столовая", "jedalen"]),
    ("ивенты", ["tabacka", "usmev", "кино", "театр", "музей", "выставка", "фестиваль", "концерт"]),
    ("работа", ["вакансия", "brigada", "бригада", "работа", "dohoda", "стажировка"]),
    ("туризм", ["поезд", "flixbus", "regiojet", "ryanair", "wizz", "лоукостер", "билеты", "туризм", "путешествия"])
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
        r'一-鿿㐀-䶿'                # CJK (Китайский / Японский)
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
    """
    Извлекает прямую целевую ссылку на внешний ресурс (Udemy, Steam, магазин),
    минуя ссылки на Reddit и сторонние сервисы.
    """
    if not summary_html:
        return default_link

    # 1. Ищем стандартную внешнюю ссылку Reddit
    match = re.search(r'<a\s+href="([^"]+)">\[link\]</a>', summary_html, re.IGNORECASE)
    if match:
        target = match.group(1)
        if "reddit.com" not in target and "redd.it" not in target:
            return target

    # 2. Ищем целевые ссылки внутри текста
    urls = re.findall(r'https?://[^\s<>"\'\)]+', summary_html)
    for u in urls:
        if any(dom in u for dom in ("udemy.com", "coursera.org", "store.steampowered.com/app/", "epicgames.com")):
            return u
        if "reddit.com" not in u and "redd.it" not in u and "discord" not in u:
            return u

    # 3. Пробуем получить из JSON поста
    if "reddit.com" in default_link:
        try:
            json_url = default_link.rstrip("/") + ".json"
            r = requests.get(json_url, timeout=5, headers={"User-Agent": "telegram:discount4studentsbot:v2.0 (by /u/studentdealsbot)"})
            if r.status_code == 200:
                data = r.json()
                post_data = data[0]["data"]["children"][0]["data"]
                post_url = post_data.get("url", "")
                if post_url and "reddit.com" not in post_url and "redd.it" not in post_url:
                    return post_url
                selftext = post_data.get("selftext", "")
                for u in re.findall(r'https?://[^\s<>"\'\)]+', selftext):
                    if any(dom in u for dom in ("udemy.com", "coursera.org", "store.steampowered.com/app/", "epicgames.com")):
                        return u
                    if "reddit.com" not in u and "redd.it" not in u and "discord" not in u:
                        return u
        except Exception:
            pass

    return default_link

def clean_summary_text(summary_html):
    if not summary_html:
        return ""
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


def check_steam_game_is_free(steam_url):
    """
    Проверяет через официальный API Steam, действительно ли платная игра сейчас раздаётся со скидкой 100%.
    Отсекает обычные Free to Play игры, DLC, вопросы, темы обсуждений и завершённые акции.
    """
    match = re.search(r'/app/(\d+)', steam_url)
    if not match:
        return False  # Ссылка не на конкретную игру в Steam — отбрасываем

    app_id = match.group(1)
    api_url = f"https://store.steampowered.com/api/appdetails?appids={app_id}&filters=price_overview,basic"
    try:
        r = requests.get(api_url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            data = r.json().get(app_id, {})
            if not data.get("success"):
                return False
            d_data = data.get("data", {})

            # 1. Если игра Free to Play (is_free == True) — СТРОГО ОТБРАСЫВАЕМ!
            if d_data.get("is_free"):
                print(f"[Steam API] Отклонено: {app_id} является постоянным Free-to-play.")
                return False

            # 2. Проверяем наличие временной 100% скидки
            price_info = d_data.get("price_overview", {})
            if price_info:
                discount = price_info.get("discount_percent", 0)
                final_price = price_info.get("final", 1)
                if discount == 100 or final_price == 0:
                    return True
                else:
                    print(f"[Steam API] Отклонено: {app_id} платная, скидка {discount}%, цена > 0.")
                    return False
            return False
    except Exception as e:
        print(f"Ошибка проверки Steam API ({app_id}): {e}")
    return False

def fetch_feed_entries(feed_info):
    url = feed_info["url"]
    feed_format = feed_info.get("format", "rss")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    # 1. Epic API
    if feed_format == "epic_api":
        try:
            resp = requests.get(url, timeout=10, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                elements = data.get("data", {}).get("Catalog", {}).get("searchStore", {}).get("elements", [])
                entries = []
                for el in elements:
                    title = el.get("title")
                    promos = el.get("promotions") or {}
                    active_offers = promos.get("promotionalOffers", [])

                    is_free_now = False
                    end_date = ""
                    if active_offers:
                        offers_list = active_offers[0].get("promotionalOffers", [])
                        for off in offers_list:
                            discount = off.get("discountSetting", {}).get("discountPercentage")
                            if discount == 0:
                                is_free_now = True
                                end_date = off.get("endDate", "")[:10]
                                break

                    price_info = el.get("price", {}).get("totalPrice", {})
                    if is_free_now and price_info.get("discountPrice") == 0:
                        slug = el.get("productSlug") or el.get("urlSlug")
                        orig = price_info.get("originalPrice", 0) / 100
                        worth_str = f"€{orig:.2f}" if orig > 0 else "Бесплатно"
                        link = f"https://store.epicgames.com/p/{slug}" if slug else "https://store.epicgames.com/free-games"
                        desc = el.get("description", "")
                        entries.append({
                            "id": f"egs_{el.get('id')}",
                            "title": title,
                            "summary": desc,
                            "link": link,
                            "benefit": f"Бесплатно 100% (вместо {worth_str})",
                            "duration": f"До {end_date}" if end_date else "Ограничено по времени"
                        })
                return entries
        except Exception as e:
            print(f"Ошибка загрузки Epic Games API: {e}")
        return []

    # 2. GoOut
    if feed_format == "goout_html":
        try:
            resp = requests.get(url, timeout=10, headers=headers)
            if resp.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.content, "html.parser")
                entries = []
                cards = soup.find_all("div", class_=re.compile(r"item|event|card", re.I))
                if not cards:
                    cards = soup.find_all("a", href=re.compile(r"/sk/.*-kosice/|/sk/akcie/"))

                seen_event_titles = set()
                for card in cards[:30]:
                    title_elem = card.find(["h2", "h3", "h4", "strong", "span"])
                    title = title_elem.get_text(strip=True) if title_elem else card.get_text(strip=True)
                    if not title or len(title) < 5 or len(title) > 90:
                        continue
                    if title in seen_event_titles:
                        continue

                    link = card.get("href") if card.name == "a" else None
                    if not link:
                        a_tag = card.find("a")
                        link = a_tag.get("href") if a_tag else None

                    if not link or "javascript" in link:
                        continue
                    if not link.startswith("http"):
                        link = "https://goout.net" + link

                    if any(skip in link for skip in ("/vstupenky/", "/registracia/", "/prihlasenie/")):
                        continue

                    seen_event_titles.add(title)
                    entries.append({
                        "id": f"goout_{re.sub(r'[^a-zA-Z0-9]', '', title)[:25]}",
                        "title": title,
                        "link": link,
                        "summary": "Событие в Кошице на площадках Tabačka, Kulturpark или Kino Úsmev. Билеты и расписание на GoOut.",
                        "benefit": "Студенческие билеты / Вход свободный"
                    })
                return entries[:10]
        except Exception as e:
            print(f"Ошибка парсинга GoOut: {e}")
        return []

    # 3. Zlavomat
    if feed_format == "zlavomat_html":
        try:
            resp = requests.get(url, timeout=10, headers=headers)
            if resp.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.content, "html.parser")
                entries = []
                cards = soup.find_all("div", class_=re.compile(r"deal|card|item", re.I)) or soup.find_all("a", href=re.compile(r"/akcia/\d+"))

                for card in cards[:30]:
                    a_tag = card if card.name == "a" else card.find("a", href=re.compile(r"/akcia/\d+"))
                    if not a_tag:
                        continue
                    link = a_tag.get("href", "")
                    if not link.startswith("http"):
                        link = "https://www.zlavomat.sk" + link

                    title_el = card.find(["h2", "h3", "h4", "strong", "span"])
                    title = title_el.get_text(strip=True) if title_el else a_tag.get_text(strip=True)
                    if not title or len(title) < 6:
                        continue

                    text_all = card.get_text(" ", strip=True)
                    price_match = re.search(r'(\d+[\.,]\d+)\s*€|€\s*(\d+[\.,]\d+)', text_all)
                    price_val = 0.0
                    if price_match:
                        price_str = (price_match.group(1) or price_match.group(2)).replace(",", ".")
                        try:
                            price_val = float(price_str)
                        except ValueError:
                            pass

                    if price_val > 15.0:
                        continue

                    benefit_str = f"От €{price_val:.2f} по акции" if price_val > 0 else "Скидка на меню до 40–50%"

                    entries.append({
                        "id": f"zlavomat_{re.sub(r'[^a-zA-Z0-9]', '', link)[-15:]}",
                        "title": title[:80],
                        "link": link,
                        "summary": "Выгодное предложение в ресторанах и кафе Кошице. Блюда и комбо по специальной цене.",
                        "benefit": benefit_str
                    })
                return entries[:4]
        except Exception as e:
            print(f"Ошибка парсинга Zlavomat: {e}")
        return []

    # 4. SlovakInfo
    if feed_format == "slovakinfo_afisha":
        try:
            resp = requests.get(url, timeout=10, headers=headers)
            if resp.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.content, "html.parser")
                entries = []
                articles = soup.find_all("article") or soup.find_all("div", class_=re.compile(r"post|entry", re.I))

                for art in articles[:10]:
                    title_el = art.find(["h2", "h3", "h4", "a"])
                    if not title_el:
                        continue
                    title = title_el.get_text(strip=True)
                    if not title or ("афиша" not in title.lower() and "кошице" not in title.lower()):
                        continue

                    a_tag = art.find("a") if art.name != "a" else art
                    link = a_tag.get("href") if a_tag else url

                    summary_el = art.find(["p", "div", "span"], class_=re.compile(r"desc|summary|excerpt", re.I))
                    summary = summary_el.get_text(strip=True) if summary_el else "Главные городские события, фестивали и выставки в Кошице."

                    entries.append({
                        "id": f"slovakinfo_{re.sub(r'[^a-zA-Z0-9]', '', title)[:25]}",
                        "title": title,
                        "link": link,
                        "summary": summary[:250],
                        "benefit": "Дайджест бесплатных и молодежных событий недели"
                    })
                return entries[:4]
        except Exception as e:
            print(f"Ошибка парсинга SlovakInfo: {e}")
        return []

    # 5. GamerPower
    if feed_format == "gamerpower_json":
        try:
            resp = requests.get(url, timeout=10, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                entries = []
                for item in data[:25]:
                    title = item.get("title", "")
                    platforms = str(item.get("platforms", "")).lower()
                    giveaway_url = str(item.get("open_giveaway_url") or item.get("open_giveaway") or item.get("gamerpower_url") or "")
                    worth = str(item.get("worth", "")).strip()

                    comb_check = f"{title} {platforms} {giveaway_url}".lower()
                    if not any(plat in comb_check for plat in ("steam", "epic", "epicgames")):
                        continue

                    if worth in ("$0.00", "0€", "N/A", "") or any(m in title.lower() for m in ("free to play", "f2p", "[f2p]")):
                        continue

                    entries.append({
                        "id": str(item.get("id")),
                        "title": title,
                        "link": giveaway_url,
                        "summary": item.get("description", ""),
                        "benefit": f"Бесплатно 100% (вместо {worth})" if worth else "Бесплатно 100%"
                    })
                return entries
        except Exception as e:
            print(f"Ошибка GamerPower: {e}")
        return []

    # 6. RSS
    req_headers = {"User-Agent": "telegram:discount4studentsbot:v2.0 (by /u/studentdealsbot)"} if "reddit.com" in url else headers
    try:
        resp = requests.get(url, timeout=10, headers=req_headers)
        if resp.status_code == 200:
            feed = feedparser.parse(resp.content)
            entries = []
            for e in feed.entries[:25]:
                title = getattr(e, "title", "")

                if "?" in title or any(w in title.lower() for w in (
                    "working for you", "anyone else", "problem", "question",
                    "is down", "how to", "discussion", "megathread", "discord", "weekly thread"
                )):
                    continue

                if feed_format == "steam_reddit":
                    t_low = title.lower()
                    if any(m in t_low for m in ("discussion", "thread", "megathread", "discord", "weekly", "f2p", "free to play", "[f2p]")):
                        continue

                raw_link = getattr(e, "link", "")
                summary = getattr(e, "summary", "")

                direct = extract_direct_link(summary, raw_link) if "reddit.com" in raw_link else raw_link

                if feed_format == "steam_reddit":
                    if "store.steampowered.com/app/" not in direct:
                        continue
                    if not check_steam_game_is_free(direct):
                        continue

                if "udemyfreebies" in url.lower():
                    if not any(dom in direct for dom in ("udemy.com", "coursera.org", "edx.org")):
                        continue

                entries.append({
                    "id": getattr(e, "id", getattr(e, "link", None)),
                    "title": title,
                    "link": direct,
                    "summary": summary
                })
            return entries
    except Exception as err:
        print(f"Ошибка загрузки RSS {url}: {err}")
    return []

CATEGORY_CONFIG = {
    "вкусное": {"icon": "🍕", "name": "Вкусное"},
    "поездки": {"icon": "🚆", "name": "Поездки"},
    "туризм": {"icon": "🏕", "name": "Туризм"},
    "ивенты": {"icon": "🎭", "name": "Ивенты"},
    "кошице": {"icon": "📍", "name": "Кошице"},
    "работа": {"icon": "💼", "name": "Работа"},
    "софт": {"icon": "💻", "name": "IT & Софт"},
    "курсы": {"icon": "🎓", "name": "Курсы"},
    "игры": {"icon": "🎮", "name": "Игры"},
    "подписки": {"icon": "🛍", "name": "Подписки"}
}

# Строгая привязка всех постоянных программ (никаких ссылок на ISIC!)
DEAL_PRIMARY_CATEGORY = {
    "starbucks_student_ke": ("вкусное", "🍕 [Вкусное: Starbucks]"),
    "mcdonalds_student_ke": ("вкусное", "🍕 [Вкусное: McDonald's]"),
    "sk_trains_free": ("поездки", "🚆 [Поездки: Поезда ŽSSK]"),
    "kosice_dpmk_transport": ("поездки", "🚆 [Поездки: Транспорт DPMK]"),
    "sk_isic_jedalne": ("вкусное", "🍕 [Вкусное: СтудСтоловые]"),
    "kosice_tabacka_usmev": ("ивенты", "🎭 [Ивенты: Tabačka & Кино]"),
    "k13_kosice_culture": ("ивенты", "🎭 [Ивенты: Kulturpark & Опен-эйр]"),
    "sk_student_brigady": ("работа", "💼 [Работа: Кошице]"),
    "flixbus_regiojet_discounts": ("поездки", "🚆 [Поездки: Автобусы & Поезда]"),
    "europe_isic_benefits": ("туризм", "🏕 [Туризм: Музеи Европы]"),
    "lowcost_flights_kosice": ("поездки", "🚆 [Поездки: Лоукостеры]"),
    "fusion_360_edu": ("софт", "💻 [IT & Софт: 3D CAD]"),
    "jetbrains_all_products": ("софт", "💻 [IT & Софт: Dev]"),
    "github_student_pack": ("софт", "💻 [IT & Софт: GitHub Pack]"),
    "azure_students": ("софт", "💻 [IT & Софт: Azure Cloud]"),
    "figma_education": ("софт", "💻 [IT & Софт: Дизайн]"),
    "canva_pro_student": ("софт", "💻 [IT & Софт: Дизайн]"),
    "notion_education": ("софт", "💻 [IT & Софт: Учёба]"),
    "coursera_student": ("курсы", "🎓 [Курсы: Coursera]"),
    "youtube_premium_student": ("подписки", "🛍 [Подписки: Видео]"),
    "spotify_student": ("подписки", "🛍 [Подписки: Музыка]"),
    "apple_music_tv": ("подписки", "🛍 [Подписки: Стриминг]"),
    "asos_student_discount": ("подписки", "🛍 [Подписки: Одежда]"),
    "epic_games_weekly": ("игры", "🎮 [Игры: Epic Games]"),
    "steam_free_to_play": ("игры", "🎮 [Игры: Steam Каталог]"),
    "isic_extra_hot_deals": ("подписки", "🛍 [Подписки: Alza Student]"),
    "github_perks_hot_credits": ("софт", "💻 [IT & Софт: IT Кредиты]")
}

TAG_MAP = {
    "вкусное": "вкусное",
    "столовая": "вкусное",
    "еда": "вкусное",
    "поездки": "поездки",
    "транспорт": "поездки",
    "поезда": "поездки",
    "туризм": "туризм",
    "путешествия": "туризм",
    "авиа": "поездки",
    "ивенты": "ивенты",
    "культура": "ивенты",
    "кошице": "кошице",
    "работа": "работа",
    "стажировки": "работа",
    "софт": "софт",
    "dev": "софт",
    "cad": "софт",
    "дизайн": "софт",
    "продуктивность": "софт",
    "ии": "софт",
    "курсы": "курсы",
    "игры": "игры",
    "подписки": "подписки",
    "скидки": "подписки",
    "одежда": "подписки",
    "горящее": "подписки"
}

def get_deal_meta(deal):
    deal_id = deal.get("id")
    if deal_id in DEAL_PRIMARY_CATEGORY:
        canonical_cat, official_badge = DEAL_PRIMARY_CATEGORY[deal_id]
        return canonical_cat, official_badge

    raw_tag = str(deal.get("main_tag", "подписки")).lower()
    canonical_cat = TAG_MAP.get(raw_tag, "подписки")
    cfg = CATEGORY_CONFIG.get(canonical_cat, {"icon": "🔥", "name": "Скидка"})
    official_badge = deal.get("badge") or f"{cfg['icon']} [{cfg['name']}]"
    return canonical_cat, official_badge

def send_telegram_card(deal, is_fallback=False):
    title = escape_html(deal.get("title"))
    canonical_cat, badge = get_deal_meta(deal)

    benefit = escape_html(deal.get("benefit"))
    duration = escape_html(deal.get("duration"))
    region = escape_html(deal.get("region"))
    reqs = escape_html(deal.get("requirements", "Регистрация / Студенческий статус"))
    desc = escape_html(deal.get("description", ""))
    how_to = escape_html(deal.get("how_to", ""))
    link = deal.get("link")

    tags_string = f"#{canonical_cat}@{CHANNEL_USERNAME}"

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
        "🎓 <b>Интерактивный каталог студенческих льгот и скидок</b>\n\n"
        "Мы собрали актуальные льготы в Кошице, бесплатные лицензии на софт, раздачи игр в Steam/Epic Games и полезные курсы.\n\n"
        "⚡️ <i>Нажмите на хештег темы для быстрого поиска по каналу:</i>\n"
        f"• 🍕 #вкусное@{CHANNEL_USERNAME} — студенческие столовые TUKE/UPJŠ, обеды за €2, скидки на еду\n"
        f"• 🚆 #поездки@{CHANNEL_USERNAME} — бесплатные поезда ŽSSK, DPMK 50%, FlixBus, лоукостеры\n"
        f"• 🏕 #туризм@{CHANNEL_USERNAME} — Словацкий Рай, Татры, Спишский Град, музеи Европы\n"
        f"• 🎭 #ивенты@{CHANNEL_USERNAME} — Tabačka, Kulturpark, городские фестивали, опен-эйры\n"
        f"• 📍 #кошице@{CHANNEL_USERNAME} — студенческий кампус, общежития и жизнь в городе\n"
        f"• 💼 #работа@{CHANNEL_USERNAME} — студенческие бригады в Кошице, контракт Dohoda\n"
        f"• 💻 #софт@{CHANNEL_USERNAME} — лицензии JetBrains, GitHub Pack, Figma, ИИ\n"
        f"• 🎓 #курсы@{CHANNEL_USERNAME} — онлайн-курсы Coursera и промокоды Udemy\n"
        f"• 🎮 #игры@{CHANNEL_USERNAME} — 100% бесплатные раздачи Steam и Epic Games\n"
        f"• 🛍 #подписки@{CHANNEL_USERNAME} — скидки на Spotify, Apple, ASOS, Alza Student\n\n"
        "📱 <b>Или откройте удобный поиск прямо в Telegram:</b>\n"
        "Нажмите на кнопку ниже, чтобы запустить Mini App с фильтрами по категориям! 👇"
    )

def send_pinned_navigator():
    text = get_navigator_text()
    reply_markup = {
        "inline_keyboard": [
            [
                {
                    "text": "📱 Открыть каталог скидок",
                    "url": "https://t.me/discount4studentsbot/deals"
                }
            ]
        ]
    }
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "reply_markup": reply_markup
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

def export_deals_for_webapp(deal_to_msg_id, active_posts):
    items = []
    for d in EVERGREEN_DEALS:
        canonical_cat, official_badge = get_deal_meta(d)
        items.append({
            "id": d.get("id"),
            "title": d.get("title"),
            "category": canonical_cat,
            "badge": official_badge,
            "benefit": d.get("benefit"),
            "duration": d.get("duration"),
            "region": d.get("region"),
            "requirements": d.get("requirements"),
            "description": d.get("description"),
            "how_to": d.get("how_to"),
            "link": d.get("link"),
            "main_tag": canonical_cat,
            "extra_tags": [canonical_cat],
            "message_id": deal_to_msg_id.get(d.get("id")),
            "is_evergreen": True
        })

    for post_id, info in active_posts.items():
        canonical_cat, official_badge = get_deal_meta(info)
        items.append({
            "id": post_id,
            "title": info.get("title"),
            "category": canonical_cat,
            "badge": official_badge,
            "benefit": info.get("benefit", "Актуальная скидка / раздача"),
            "duration": info.get("duration", "Временное предложение"),
            "region": "Онлайн / Кошице",
            "requirements": "Учётная запись платформы",
            "description": "",
            "how_to": "Перейдите по ссылке предложения.",
            "link": info.get("target_link") or info.get("source_link"),
            "main_tag": canonical_cat,
            "extra_tags": [canonical_cat],
            "message_id": info.get("message_id"),
            "is_evergreen": False
        })

    os.makedirs("docs", exist_ok=True)
    with open("docs/deals.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"[WebApp] Экспортировано {len(items)} предложений в docs/deals.json")

def normalize_title(title):
    return re.sub(r'[^a-zA-Z0-9а-яА-Я]', '', str(title).lower())[:25]

def normalize_link(link):
    return str(link).split('?')[0].rstrip('/').lower()

def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ОШИБКА: Токен или ID канала не заданы.")
        return

    processed_ids_raw = load_json_file(HISTORY_FILE)
    processed_ids = set(processed_ids_raw if isinstance(processed_ids_raw, list) else [])
    new_processed = set(processed_ids)

    active_posts_raw = load_json_file(ACTIVE_POSTS_FILE)
    active_posts = active_posts_raw if isinstance(active_posts_raw, dict) else {}

    # Набор для сквозной дедупликации по названию и прямой ссылке
    seen_titles = set(normalize_title(p.get("title", "")) for p in active_posts.values() if p.get("title"))
    seen_links = set(normalize_link(p.get("target_link", "")) for p in active_posts.values() if p.get("target_link"))

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

    # Шаг 3: Сохранение номеров постов и публикация закреплённого навигатора с кнопкой
    save_json_file(evergreen_posts_file, deal_to_msg_id)

    nav_file = "data/navigator_info.json"
    nav_info = load_json_file(nav_file) or {}

    if is_initial_fill or not nav_info.get("pinned"):
        print("[Навигатор] Публикация закреплённого поста-навигатора с кнопкой...")
        nav_msg_id = send_pinned_navigator()
        if nav_msg_id:
            pin_telegram_message(nav_msg_id)
            save_json_file(nav_file, {"pinned": True, "message_id": nav_msg_id})

    # Шаг 4: Выгрузка новостей из КАЖДОГО источника с отдельным лимитом
    per_feed_limit = 10 if is_initial_fill else 4
    dynamic_published = 0
    now = time.time()

    print(f"[Динамика] Опрос источников. Лимит на источник: {per_feed_limit} постов.")

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

                # Двойной заслон от вопросов и мусора
                if "?" in title or any(w in title.lower() for w in (
                    "working for you", "anyone else", "problem", "question", 
                    "is down", "how to", "discussion", "megathread", "discord"
                )):
                    new_processed.add(post_id)
                    continue

                # Кросс-дедупликация: исключаем повторные публикации одной игры из разных источников
                norm_t = normalize_title(title)
                if norm_t in seen_titles:
                    print(f"[Дедупликация] Пропуск повтора по названию: '{title}'")
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

                # Не постим ссылки на Reddit
                if "reddit.com" in direct_link or "redd.it" in direct_link:
                    new_processed.add(post_id)
                    continue

                # Курсы обязаны вести на Udemy / Coursera
                if feed_info.get("category") == "Курсы" and not any(dom in direct_link for dom in ("udemy.com", "coursera.org", "edx.org")):
                    new_processed.add(post_id)
                    continue

                status, final_url, is_fallback = validate_link(direct_link, fallback_url=raw_link)

                if status == "DROP":
                    new_processed.add(post_id)
                    continue
                elif status == "RETRY":
                    continue

                norm_link = normalize_link(final_url)
                if norm_link in seen_links:
                    print(f"[Дедупликация] Пропуск повтора по ссылке: '{final_url}'")
                    new_processed.add(post_id)
                    continue

                topic_tags = extract_topic_tags(title, summary)
                extra_tags = []
                for t in topic_tags:
                    if t != feed_info["main_tag"] and t not in extra_tags:
                        extra_tags.append(t)

                card = {
                    "id": post_id,
                    "title": title,
                    "category": feed_info["category"],
                    "badge": feed_info["badge"],
                    "main_tag": feed_info["main_tag"],
                    "benefit": entry.get("benefit") or feed_info["default_benefit"],
                    "duration": entry.get("duration") or feed_info["default_duration"],
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
                    seen_titles.add(norm_t)
                    seen_links.add(norm_link)
                    dynamic_published += 1
                    feed_count += 1

                    max_ttl = now + feed_info.get("max_ttl_seconds", 345600)
                    if message_id:
                        active_posts[post_id] = {
                            "message_id": message_id,
                            "title": title,
                            "category": feed_info["category"],
                            "main_tag": feed_info["main_tag"],
                            "benefit": card["benefit"],
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
    export_deals_for_webapp(deal_to_msg_id, active_posts)
    print(f"Сбор завершён. Опубликовано динамических постов: {dynamic_published}. Активных на мониторинге: {len(active_posts)}")

if __name__ == "__main__":
    main()
