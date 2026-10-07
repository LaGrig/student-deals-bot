import os
import json
import time
import feedparser
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
HISTORY_FILE = "data/processed_ids.json"

CHANNEL_USERNAME = TELEGRAM_CHAT_ID.replace("@", "") if TELEGRAM_CHAT_ID else "discounts4students"

# Полная база студенческих программ по всем категориям
EVERGREEN_DEALS = [
    {
        "id": "youtube_premium_student",
        "title": "YouTube Premium + YouTube Music для студентов",
        "category": "Музыка и Видео",
        "main_tag": "подписки",
        "benefit": "Скидка ~50% (в Украине всего ~59 грн/мес)",
        "duration": "1 год с ежегодным продлением (до 4 лет учебы)",
        "region": "🇺🇦 Украина, 🇪🇺 ЕС, 🇺🇸 США и др.",
        "requirements": "Студенческий билет или справка (верификация через SheerID)",
        "description": "YouTube и YouTube Music без рекламы, фоновое воспроизведение при заблокированном экране и скачивание любых треков и роликов офлайн.",
        "how_to": "1. Перейдите по ссылке на страницу студенческой подписки.\n2. Нажмите «Попробовать бесплатно / Оформить».\n3. Введите данные вуза и прикрепите фото студенческого в форме SheerID (проверка занимает от 15 минут).",
        "link": "https://www.youtube.com/premium/student",
        "extra_tags": ["музыка", "youtube", "украина"]
    },
    {
        "id": "spotify_student",
        "title": "Spotify Premium Student",
        "category": "Музыка и Аудио",
        "main_tag": "подписки",
        "benefit": "Скидка 50% + 1 месяц бесплатно",
        "duration": "До 4 лет (подтверждение раз в 12 месяцев)",
        "region": "🇺🇦 Украина, 🇪🇺 ЕС, 🇺🇸 США",
        "requirements": "Студенческий билет (верификация SheerID)",
        "description": "Премиум-доступ к Spotify: прослушивание музыки без ограничений и рекламы в максимальном качестве, скачивание альбомов на телефон.",
        "how_to": "1. Откройте страницу Spotify Student.\n2. Авторизуйтесь и пройдите быструю проверку статуса учащегося через SheerID.",
        "link": "https://www.spotify.com/student/",
        "extra_tags": ["музыка", "spotify", "украина"]
    },
    {
        "id": "apple_music_tv",
        "title": "Apple Music + Apple TV+ для студентов",
        "category": "Музыка и Кино",
        "main_tag": "подписки",
        "benefit": "Скидка ~50% + бесплатный Apple TV+",
        "duration": "До 48 месяцев (4 года учебы)",
        "region": "🇺🇦 Украина, 🇪🇺 ЕС, 🇺🇸 США",
        "requirements": "Верификация через сервис UNiDAYS",
        "description": "Студенческая подписка на Apple Music со скидкой 50%, в которую автоматически бесплатно входит доступ к фильмам и сериалам Apple TV+.",
        "how_to": "1. Откройте приложение «Музыка» на телефоне или сайте Apple.\n2. Выберите тариф «Студенческая подписка».\n3. Подтвердите статус через встроенную форму UNiDAYS.",
        "link": "https://www.apple.com/apple-music/",
        "extra_tags": ["музыка", "кино", "apple"]
    },
    {
        "id": "fusion_360_edu",
        "title": "Autodesk Fusion 360",
        "category": "3D / CAD / Инженерия",
        "main_tag": "cad",
        "benefit": "Бесплатно (обычная цена: ~$545/год)",
        "duration": "1 год с ежегодным продлением на весь период учебы",
        "region": "🌍 Global (Украина, ЕС, США и др.)",
        "requirements": "Студенческий билет или справка из учебного заведения",
        "description": "Профессиональный пакет для 3D-моделирования, инженерных расчетов, симуляций и подготовки к ЧПУ/3D-печати без ограничений.",
        "how_to": "1. Зайдите на портал Autodesk Education.\n2. Укажите свой университет и прикрепите фото студенческого (почта .edu не обязательна).",
        "link": "https://www.autodesk.com/education/edu-software/overview",
        "extra_tags": ["инженерия", "3d", "global"]
    },
    {
        "id": "github_student_pack",
        "title": "GitHub Student Developer Pack (включая Copilot)",
        "category": "ИИ и Разработка",
        "main_tag": "ИИ",
        "benefit": "Бесплатно (пакет ценностью более $200,000)",
        "duration": "На весь период обучения (до 2 лет с продлением)",
        "region": "🌍 Global",
        "requirements": "Студенческая почта (.edu) или студенческий билет с датой",
        "description": "Бесплатный доступ к ИИ-ассистенту GitHub Copilot, бесплатные домены от Namecheap, облачные кредиты DigitalOcean, Canva Pro и более 100 сервисов.",
        "how_to": "1. Перейдите на GitHub Education.\n2. Загрузите фото студенческого и обязательно разрешите геолокацию в браузере при отправке.",
        "link": "https://education.github.com/pack",
        "extra_tags": ["разработка", "copilot", "global"]
    },
    {
        "id": "jetbrains_all_products",
        "title": "JetBrains All Products Pack",
        "category": "Программирование / IDE",
        "main_tag": "dev",
        "benefit": "Бесплатно 100% (обычная цена: $289/год)",
        "duration": "1 год с ежегодным продлением",
        "region": "🌍 Global",
        "requirements": "Студенческая почта, ISIC или студенческий билет",
        "description": "Лицензии на все топовые среды разработки: IntelliJ IDEA Ultimate, PyCharm Professional, WebStorm, CLion, GoLand, DataGrip и Rider.",
        "how_to": "1. Откройте страницу JetBrains Free Educational Licenses.\n2. Подайте заявку через университетскую почту или студенческий билет.",
        "link": "https://www.jetbrains.com/community/education/#students",
        "extra_tags": ["программирование", "софт", "global"]
    },
    {
        "id": "figma_education",
        "title": "Figma Professional",
        "category": "Дизайн и UI/UX",
        "main_tag": "дизайн",
        "benefit": "Бесплатно (обычная цена: $15/месяц)",
        "duration": "До 2 лет с продлением",
        "region": "🌍 Global",
        "requirements": "Указание учебного заведения и студенческий билет",
        "description": "Полный тариф Figma Professional: неограниченное число файлов, командная работа, общие дизайн-системы и Figma Slides.",
        "how_to": "1. Зайдите на figma.com/education и нажмите «Apply for free».\n2. Выберите статус «Student» и отправьте форму.",
        "link": "https://www.figma.com/education/",
        "extra_tags": ["figma", "uiux", "global"]
    },
    {
        "id": "notion_education",
        "title": "Notion Plus Plan for Education",
        "category": "Продуктивность и Учёба",
        "main_tag": "продуктивность",
        "benefit": "Бесплатно (обычная цена: $10/месяц)",
        "duration": "На весь период владения студенческой почтой",
        "region": "🌍 Global",
        "requirements": "Студенческая почта любого аккредитованного вуза",
        "description": "Тариф Plus без лимита на размер загружаемых файлов, с бесконечной историей правок и совместными рабочими пространствами.",
        "how_to": "Укажите студенческий email в настройках Notion → перейдите в «Upgrade» и выберите бесплатный студенческий тариф.",
        "link": "https://www.notion.so/product/notion-for-education",
        "extra_tags": ["notion", "заметки", "global"]
    },
    {
        "id": "azure_students",
        "title": "Microsoft Azure for Students",
        "category": "Облачные сервисы и ИИ",
        "main_tag": "ИИ",
        "benefit": "$100 бесплатных кредитов + бесплатные сервисы",
        "duration": "12 месяцев (возобновляемый)",
        "region": "🌍 Global",
        "requirements": "Студенческая почта вуза",
        "description": "$100 на запуск серверов, баз данных и ИИ-моделей в облаке Microsoft. Главное преимущество: банковская карта НЕ нужна!",
        "how_to": "Войдите на страницу Azure for Students под своей учебной учетной записью Microsoft.",
        "link": "https://azure.microsoft.com/free/students/",
        "extra_tags": ["облако", "azure", "global"]
    },
    {
        "id": "isic_card",
        "title": "Международный студенческий билет ISIC",
        "category": "Путешествия и Скидки",
        "main_tag": "isic",
        "benefit": "Скидки до 50% на билеты, хостелы, музеи и сервисы",
        "duration": "1 календарный год",
        "region": "🌍 Global (более 130 стран)",
        "requirements": "Студенческий билет дневной формы обучения",
        "description": "Международное удостоверение студента: скидки на автобусы FlixBus (10-15%), бронирование отелей Booking/Hostelworld, музеи Европы и авиабилеты.",
        "how_to": "Оформляется онлайн через сайт ISIC или в студенческих профкомах.",
        "link": "https://www.isic.org/",
        "extra_tags": ["путешествия", "билеты", "транспорт"]
    },
    {
        "id": "uz_student_discount",
        "title": "Скидка 50% на поезда Укрзалізниці",
        "category": "Транспорт и Билеты",
        "main_tag": "транспорт",
        "benefit": "Скидка 50% от стоимости билета",
        "duration": "На весь период действия студенческого билета",
        "region": "🇺🇦 Украина",
        "requirements": "Студенческий билет, внесенный в базу ЕГЭБО (Дія)",
        "description": "Скидка 50% на проезд во всех внутренних поездах Украины (плацкарт, общие вагоны, 2-3 класс скоростных поездов Интерсити).",
        "how_to": "В приложении «Укрзалізниця» выберите пассажира «Студент» и введите номер студенческого билета.",
        "link": "https://booking.uz.gov.ua/",
        "extra_tags": ["билеты", "поезда", "украина"]
    }
]

DYNAMIC_FEEDS = [
    {
        "url": "https://www.reddit.com/r/studentdeals/new/.rss",
        "category": "Свежие акции",
        "main_tag": "акции",
        "default_region": "🌍 Global / 🇺🇸 US"
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

def send_telegram_card(deal):
    title = escape_html(deal.get("title"))
    category = escape_html(deal.get("category"))
    benefit = escape_html(deal.get("benefit"))
    duration = escape_html(deal.get("duration"))
    region = escape_html(deal.get("region"))
    reqs = escape_html(deal.get("requirements"))
    desc = escape_html(deal.get("description"))
    how_to = escape_html(deal.get("how_to"))
    link = deal.get("link")
    
    main_tag = deal.get("main_tag", "скидки")
    extra_tags = deal.get("extra_tags", [])
    
    tags_list = [f"#{main_tag}@{CHANNEL_USERNAME}"]
    for t in extra_tags:
        tags_list.append(f"#{t}@{CHANNEL_USERNAME}")
    tags_string = " ".join(tags_list)

    text = (
        f"🎓 <b>[{category}]</b> — <b>{title}</b>\n\n"
        f"💰 <b>Выгода:</b> {benefit}\n"
        f"⏳ <b>Срок:</b> {duration}\n"
        f"🌍 <b>Регион:</b> {region}\n"
        f"📋 <b>Что нужно:</b> {reqs}\n\n"
        f"{desc}\n\n"
        f"💡 <b>Как получить:</b>\n{how_to}\n\n"
        f"{tags_string}"
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🔗 Оформить предложение", "url": link}
            ],
            [
                {
                    "text": f"📂 Все посты: {category}",
                    "url": f"https://t.me/{CHANNEL_USERNAME}?q=%23{main_tag}"
                }
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
        print(f"Отправка '{title}': HTTP {response.status_code}")
        # Пауза 1.5 секунды между сообщениями для соблюдения лимитов Telegram
        time.sleep(1.5)
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка при отправке: {e}")
        return False

def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ОШИБКА: Не заданы TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID.")
        return

    print(f"Запуск скрипта. Целевой канал: {TELEGRAM_CHAT_ID}")
    processed_ids = load_processed_ids()
    new_processed = set(processed_ids)

    # Публикуем ВСЕ оставшиеся предложения из каталога без ограничений
    for deal in EVERGREEN_DEALS:
        deal_id = deal["id"]
        if deal_id not in processed_ids:
            print(f"Публикация: {deal['title']}")
            if send_telegram_card(deal):
                new_processed.add(deal_id)

    # Проверяем свежие внешние акции
    for feed_info in DYNAMIC_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"], agent="Mozilla/5.0")
            for entry in feed.entries[:3]:
                post_id = entry.get("id") or entry.get("link")
                if not post_id or post_id in processed_ids:
                    continue

                card = {
                    "id": post_id,
                    "title": entry.title,
                    "category": feed_info["category"],
                    "main_tag": feed_info["main_tag"],
                    "benefit": "Временная скидка / промокод",
                    "duration": "Ограниченное время акции",
                    "region": feed_info["default_region"],
                    "requirements": "Студенческий статус / промокод",
                    "description": entry.get("summary", "Подробности акции доступны по ссылке."),
                    "how_to": "Нажмите на кнопку ниже для перехода к условиям акции.",
                    "link": entry.link,
                    "extra_tags": ["промо"]
                }

                if send_telegram_card(card):
                    new_processed.add(post_id)
        except Exception as e:
            print(f"Ошибка RSS: {e}")

    save_processed_ids(new_processed)
    print("Готово! Все доступные предложения опубликованы.")

if __name__ == "__main__":
    main()
