import os
import json
import feedparser
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
HISTORY_FILE = "data/processed_ids.json"

# Получаем чистое имя канала без @ для создания внутриканальных ссылок
CHANNEL_USERNAME = TELEGRAM_CHAT_ID.replace("@", "") if TELEGRAM_CHAT_ID else "discounts4students"

# 1. Золотой фонд студенческих программ и лицензий
EVERGREEN_DEALS = [
    {
        "id": "fusion_360_edu",
        "title": "Autodesk Fusion 360",
        "category": "3D / CAD / Инженерия",
        "main_tag": "cad",
        "benefit": "Бесплатно (обычная цена: ~$545/год)",
        "duration": "1 год с ежегодным продлением на весь период учебы",
        "region": "🌍 Global (Украина, ЕС, США и др.)",
        "requirements": "Студенческий билет или справка из учебного заведения",
        "description": "Полнофункциональный профессиональный пакет для 3D-моделирования, инженерного проектирования, симуляций механики и подготовки моделей к ЧПУ/3D-печати без ограничений.",
        "how_to": "1. Зайдите на портал Autodesk Education.\n2. Укажите свой университет/колледж.\n3. Загрузите фото студенческого билета (почта .edu не обязательна, модерация длится от 15 минут).",
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
        "description": "Крупнейший набор для разработчиков: бесплатный доступ к ИИ-ассистенту GitHub Copilot, бесплатные домены (.me) от Namecheap, облачные кредиты DigitalOcean, Canva Pro, премиум в Datadog и еще более 100 сервисов.",
        "how_to": "1. Перейдите на GitHub Education.\n2. Привяжите студенческую почту или загрузите фото документа.\n3. Включите геолокацию в браузере при отправке заявки (важное требование GitHub).",
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
        "description": "Профессиональные лицензии на все флагманские среды разработки: IntelliJ IDEA Ultimate, PyCharm Professional, WebStorm, CLion, GoLand, DataGrip и Rider.",
        "how_to": "1. Откройте страницу JetBrains Free Educational Licenses.\n2. Заполните заявку через университетскую почту или карту ISIC (верификация мгновенная).",
        "link": "https://www.jetbrains.com/community/education/#students",
        "extra_tags": ["программирование", "софт", "global"]
    },
    {
        "id": "figma_education",
        "title": "Figma Professional",
        "category": "Дизайн и UI/UX",
        "main_tag": "дизайн",
        "benefit": "Бесплатно (обычная цена: $15/месяц за место)",
        "duration": "До 2 лет с возможностью повторной верификации",
        "region": "🌍 Global",
        "requirements": "Указание учебного заведения и студенческий",
        "description": "Полный доступ к тарифу Figma Professional: неограниченное число проектов, общие библиотеки стилей и компонентов, командная работа и Figma Slides.",
        "how_to": "1. Зайдите в аккаунт Figma.\n2. Перейдите на figma.com/education и нажмите «Apply for free». Выберите «Student» и укажите специальность.",
        "link": "https://www.figma.com/education/",
        "extra_tags": ["figma", "uiux", "global"]
    },
    {
        "id": "notion_education",
        "title": "Notion Plus Plan for Education",
        "category": "Продуктивность и Заметки",
        "main_tag": "продуктивность",
        "benefit": "Бесплатно (обычная цена: $10/месяц)",
        "duration": "На весь период владения студенческой почтой",
        "region": "🌍 Global",
        "requirements": "Студенческая почта любого аккредитованного вуза",
        "description": "Тариф Plus без лимита на загрузку файлов, с неограниченной историей версий страниц и командными пространствами для учебы и конспектов.",
        "how_to": "1. Смените основной email в Notion на студенческий.\n2. Зайдите в «Settings & members» → «Upgrade» → активируйте бесплатный план для студентов.",
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
        "description": "$100 на запуск виртуальных машин, баз данных и моделей искусственного интеллекта в облаке Microsoft. НЕ требуется ввод банковской карты!",
        "how_to": "1. Перейдите на страницу Azure for Students.\n2. Войдите под своей учебной учетной записью Microsoft.\n3. Кредиты активируются мгновенно.",
        "link": "https://azure.microsoft.com/free/students/",
        "extra_tags": ["облако", "azure", "global"]
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
        "description": "Студенческая подписка на Apple Music со скидкой 50%, в которую автоматически бесплатно входит доступ к онлайн-кинотеатру Apple TV+.",
        "how_to": "1. Откройте приложение «Музыка» на iPhone/Mac или в браузере.\n2. Выберите тариф «Студенческая подписка».\n3. Подтвердите статус студента через встроенную форму UNiDAYS.",
        "link": "https://www.apple.com/apple-music/",
        "extra_tags": ["музыка", "кино", "украина"]
    },
    {
        "id": "isic_card",
        "title": "Международный студенческий билет ISIC",
        "category": "Путешествия и Скидки",
        "main_tag": "isic",
        "benefit": "Скидки до 50% на билеты, хостелы, музеи и сервисы",
        "duration": "1 календарный год",
        "region": "🌍 Global (более 130 стран, включая Украину и ЕС)",
        "requirements": "Студенческий билет дневной формы обучения",
        "description": "Международное удостоверение студента: дает скидки на автобусы FlixBus (10-15%), бронирование Booking/Hostelworld, музеи Европы и авиабилеты.",
        "how_to": "Оформляется онлайн через сайт ISIC вашей страны или в профкомах вузов.",
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
        "description": "Скидка 50% на проезд во всех внутренних поездах Украины (плацкартные вагоны, общие вагоны, 2-3 класс скоростных Интерсити).",
        "how_to": "При покупке билета в приложении «Укрзалізниця» выберите тип пассажира «Студент» и введите номер студенческого билета.",
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
    
    # Формируем внутриканальные теги: #tag@discounts4students
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

    # Интерактивные кнопки под постом
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
        print(f"Отправка поста '{title}': HTTP {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка при отправке в Telegram: {e}")
        return False

def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ОШИБКА: Не заданы TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID.")
        return

    print(f"Запуск скрипта. Канал: {TELEGRAM_CHAT_ID}")
    processed_ids = load_processed_ids()
    new_processed = set(processed_ids)

    # 1. Публикуем 1-2 карточки из фундаментального каталога
    published_from_catalog = 0
    for deal in EVERGREEN_DEALS:
        deal_id = deal["id"]
        if deal_id not in processed_ids:
            print(f"Публикуем из каталога: {deal['title']}")
            if send_telegram_card(deal):
                new_processed.add(deal_id)
                published_from_catalog += 1
                if published_from_catalog >= 2:
                    break

    # 2. Проверяем свежие акции
    for feed_info in DYNAMIC_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"], agent="Mozilla/5.0")
            for entry in feed.entries[:2]:
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
            print(f"Ошибка при чтении RSS {feed_info['url']}: {e}")

    save_processed_ids(new_processed)
    print("Работа скрипта успешно завершена.")

if __name__ == "__main__":
    main()
