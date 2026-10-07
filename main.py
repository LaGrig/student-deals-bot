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

# 1. Постоянные программы, локальные ивенты, одежда и работа
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
        "description": "Уникальная льгота для студентов словацких вузов: бесплатный проезд на всех поездах государственной железной дороги по всей Словакии (поездки из Кошице в горы Высокие Татры, Братиславу и к границам).",
        "how_to": "1. Получите студенческий ISIC в вашем университете (например, TUKE или UPJŠ).\n2. На вокзале Кошице (Železničná stanica Košice) в кассе оформите Preukaz pre študenta.\n3. Оформляйте бесплатные нулевые билеты на сайте zssk.sk или в приложении Ideme vlakom.",
        "link": "https://www.zssk.sk/bezplatna-preprava/",
        "extra_tags": ["кошице", "словакия", "поезда", "isic"]
    },
    {
        "id": "kosice_tabacka_usmev",
        "title": "Студенческий досуг в Кошице: Tabačka Kulturfabrik и Kino Úsmev",
        "category": "Ивенты и Досуг",
        "main_tag": "кошице",
        "benefit": "Скидки до 40% на концерты, фестивали и кино",
        "duration": "Постоянно при предъявлении ISIC",
        "region": "🇸🇰 Кошице (Словакия)",
        "requirements": "Карта ISIC любого вуза",
        "description": "Главные точки притяжения молодёжи и студентов в Кошице. Культурный центр Tabačka Kulturfabrik (живые концерты, выставки, фестивали) и культовый артхаусный кинотеатр Kino Úsmev предлагают специальные студенческие цены.",
        "how_to": "Выбирайте билет «Zľavnený / Študent» при покупке онлайн на сайтах площадок или показывайте ISIC в кассе.",
        "link": "https://tabacka.sk/",
        "extra_tags": ["кошице", "словакия", "ивенты", "концерты"]
    },
    {
        "id": "odessa_theaters_culture",
        "title": "Скидка 50% на театры, оперу и филармонию в Одессе",
        "category": "Ивенты и Досуг",
        "main_tag": "одесса",
        "benefit": "Скидка 50% от стоимости билета",
        "duration": "Постоянно в течение театрального сезона",
        "region": "🇺🇦 Одесса (Украина)",
        "requirements": "Студенческий билет украинского вуза",
        "description": "Одесский национальный академический театр оперы и балета, Одесская областная филармония и Украинский театр предоставляют скидку 50% для студентов. Отличный способ культурно провести вечер компанией за минимальные деньги.",
        "how_to": "Приобретайте билеты в кассах театров, показав студенческий билет, либо выбирайте студенческий тариф при онлайн-бронировании.",
        "link": "https://operahouse.od.ua/",
        "extra_tags": ["одесса", "украина", "ивенты", "культура"]
    },
    {
        "id": "asos_student_discount",
        "title": "Скидка 10% на брендовую одежду и обувь в ASOS",
        "category": "Одежда и Стиль",
        "main_tag": "одежда",
        "benefit": "Постоянная скидка 10% на весь ассортимент",
        "duration": "Круглый год на весь период учёбы",
        "region": "🌍 Global (доставка в Украину, Словакию и ЕС)",
        "requirements": "Студенческая почта (.edu) или верификация через UNiDAYS",
        "description": "Один из крупнейших мультибрендовых магазинов молодёжной одежды, кроссовок (Nike, New Balance, adidas) и аксессуаров. Студенческий код действует постоянно и суммируется со многими сезонными скидками.",
        "how_to": "1. Перейдите на страницу ASOS Student.\n2. Введите университетскую почту или подтвердите статус через UNiDAYS.\n3. Персональный промокод придёт на email.",
        "link": "https://www.asos.com/discover/students/asosteam/",
        "extra_tags": ["одежда", "стиль", "кроссовки", "скидки"]
    },
    {
        "id": "student_remote_jobs",
        "title": "Удалённая работа и стажировки: проверенные варианты для студентов",
        "category": "Работа и Стажировки",
        "main_tag": "работа",
        "benefit": "Оплата от $400 до $1200 / гибкие смены под пары",
        "duration": "Постоянные наборы",
        "region": "🌍 Global / Remote (Украина, Словакия, ЕС)",
        "requirements": "Базовый английский или грамотный язык, 4–5 часов в день",
        "description": "С чего начать зарабатывать студенту: 1) Оплачиваемые IT-стажировки (Genesis, SoftServe), 2) Чат-саппорт на гибких сменах, 3) Тестирование приложений (uTest, Testlio), где компании платят за проверку мобильных программ в свободное время.",
        "how_to": "1. Зарегистрируйтесь на uTest и пройдите бесплатную Академию тестировщика.\n2. Начните получать приглашения на платные тест-циклы мобильных игр и сайтов.",
        "link": "https://www.utest.com/",
        "extra_tags": ["работа", "стажировки", "удаленка", "фриланс"]
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
        "description": "Премиум-подписка Canva: миллионы платных шаблонов, премиум-шрифты, удаление фона в один клик, экспорт в высоком качестве и генеративный ИИ Magic Studio.",
        "how_to": "1. Перейдите на страницу Canva for Education.\n2. Войдите через аккаунт студента или свяжите с GitHub Student Developer Pack.",
        "link": "https://www.canva.com/education/",
        "extra_tags": ["canva", "графика", "дизайн"]
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
        "description": "Бесплатный доступ к тысячам курсов от Google, IBM, Yale и Stanford с получением официального подтверждённого сертификата для резюме и LinkedIn.",
        "how_to": "1. Зайдите на страницу Coursera for Campus.\n2. Введите университетскую почту для подтверждения участия вашего вуза.",
        "link": "https://www.coursera.org/for-university-and-college-students",
        "extra_tags": ["coursera", "сертификаты", "курсы"]
    }
]

# 2. Динамические потоки горячих акций и раздач
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
    },
    {
        "url": "https://www.reddit.com/r/eFreebies/new/.rss",
        "category": "🎁 Софт и Полезности",
        "badge": "🎁 [Бесплатный софт / сервис]",
        "main_tag": "софт",
        "default_benefit": "Бесплатная лицензия / Доступ",
        "default_duration": "Временная промо-акция",
        "default_region": "🌍 Global / Онлайн",
        "how_to_tip": "Перейдите по ссылке и активируйте промокод или зарегистрируйте бесплатную лицензию."
    },
    {
        "url": "https://www.reddit.com/r/studentdeals/new/.rss",
        "category": "🎓 Студенческие акции",
        "badge": "🎓 [Студенческая скидка]",
        "main_tag": "акции",
        "default_benefit": "Специальная сниженная цена для студентов",
        "default_duration": "Период действия акции",
        "default_region": "🌍 Global / 🇺🇸 US",
        "how_to_tip": "Используйте студенческую почту или промокод при оформлении заказа."
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
    """Извлекает прямую целевую ссылку из описания (вместо ссылки на обсуждение)"""
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
        text += f"💡 <b>Как забрать / оформить:</b>\n{how_to}\n\n"
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
        time.sleep(1.5)
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

    # 1. Публикуем до 2 предложений из каталога за один запуск
    published_from_catalog = 0
    for deal in EVERGREEN_DEALS:
        deal_id = deal["id"]
        if deal_id not in processed_ids:
            print(f"Публикация из каталога: {deal['title']}")
            if send_telegram_card(deal):
                new_processed.add(deal_id)
                published_from_catalog += 1
                if published_from_catalog >= 2:
                    break

    # 2. Проверяем до 10 свежих записей в каждой динамической ленте
    for feed_info in DYNAMIC_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"], agent="Mozilla/5.0")
            for entry in feed.entries[:10]:
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
