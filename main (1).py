from datetime import date
from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
from typing import Optional

app = FastAPI(
    title="Мир Гольфа API",
    description="Стартовое API календаря и результатов турниров по гольфу",
    version="0.1.0",
)

class Tournament(BaseModel):
    id: str
    name: str
    sport: str
    start_date: date
    end_date: date
    country: str
    location: str
    level: str
    status: str
    source_url: HttpUrl
    winner: Optional[str] = None
    score: Optional[str] = None
    verified_at: Optional[str] = None

DEMO = [
    Tournament(
        id="ru-mini-2026",
        name="Кубок России по мини-гольфу",
        sport="Мини-гольф",
        start_date=date(2026, 11, 2),
        end_date=date(2026, 11, 9),
        country="Россия",
        location="Санкт-Петербург, СШОР «Невские звёзды»",
        level="Всероссийский",
        status="scheduled",
        source_url="https://rusgolf.ru/ru/contests/tournament-calendar",
    ),
    Tournament(
        id="kr-krai-2026",
        name="Чемпионат Краснодарского края по гольфу",
        sport="Гольф",
        start_date=date(2026, 11, 5),
        end_date=date(2026, 11, 8),
        country="Россия",
        location="Краснодарский край, «Геленджик гольф резорт»",
        level="Региональный",
        status="scheduled",
        source_url="https://rusgolf.ru/ru/contests/tournament-calendar",
    ),
]

@app.get("/health")
def health():
    return {"status": "ok", "mode": "demo", "collectors_enabled": False}

@app.get("/tournaments", response_model=list[Tournament])
def list_tournaments(country: Optional[str] = None, sport: Optional[str] = None):
    rows = DEMO
    if country:
        rows = [x for x in rows if x.country.casefold() == country.casefold()]
    if sport:
        rows = [x for x in rows if x.sport.casefold() == sport.casefold()]
    return rows

SOURCE_REGISTRY = [
    {
        "id": "rusgolf-calendar", "name": "Ассоциация гольфа России — календарь турниров",
        "url": "https://rusgolf.ru/ru/contests/tournament-calendar", "country": "Россия",
        "type": "official_calendar", "trust_level": 5, "purpose": "Даты, места, уровень, организаторы",
        "collection_method": "html_review_required", "enabled": True,
        "status": "configured_not_crawled", "notes": "Главный источник календаря. Проверять изменения и статус турнира."
    },
    {
        "id": "rusgolf-documents", "name": "Ассоциация гольфа России — документы и положения",
        "url": "https://rusgolf.ru/ru/contests/sorevnovaniya-2026", "country": "Россия",
        "type": "official_documents", "trust_level": 5, "purpose": "Регламенты, требования, официальные положения",
        "collection_method": "document_links_review_required", "enabled": True,
        "status": "configured_not_crawled", "notes": "Извлекать ссылки на документы и даты редакций; не заменять ими календарь."
    },
    {
        "id": "belarus-golf", "name": "Белорусская ассоциация гольфа — календарь",
        "url": "https://ingolf.by/turniryi/kalendarnyij-plan-na-2026", "country": "Беларусь",
        "type": "official_calendar", "trust_level": 5, "purpose": "Календарь, дисциплина, место, категории участников",
        "collection_method": "html_review_required", "enabled": True,
        "status": "configured_not_crawled", "notes": "Календарь может уточняться организаторами."
    },
    {
        "id": "kazakhstan-golf", "name": "Казахстанская федерация гольфа",
        "url": "https://fedgolf.kz/ru", "country": "Казахстан",
        "type": "federation_site", "trust_level": 4, "purpose": "Новости федерации, турниры и регистрационные ссылки",
        "collection_method": "html_review_required", "enabled": True,
        "status": "configured_manual_review", "notes": "На доступных страницах встречались старые сезоны; даты текущего сезона подтверждать отдельно."
    },
    {
        "id": "uzbekistan-golf", "name": "UZGolf — турниры и результаты",
        "url": "https://uzgolf.uz/en/events-en/", "country": "Узбекистан",
        "type": "tournaments_results", "trust_level": 3, "purpose": "Турниры, архивы и ссылки на результаты",
        "collection_method": "html_review_required", "enabled": True,
        "status": "configured_manual_review", "notes": "Архив содержит прошлые сезоны; использовать для обнаружения, а не как подтверждение актуального календаря."
    },
    {
        "id": "moscow-golf-federation", "name": "Федерация гольфа в г. Москве",
        "url": "https://mos-golf.ru/", "country": "Россия — Москва",
        "type": "regional_federation", "trust_level": 5, "purpose": "Чемпионат Москвы, Первенство Москвы, Московский тур и юниорские этапы",
        "collection_method": "html_review_required", "enabled": True,
        "status": "configured_not_crawled", "notes": "Региональный источник; сверять даты с календарём АГР и Москомспорта."
    },
    {
        "id": "moscow-mossport-golf", "name": "Москомспорт — календарь гольфа",
        "url": "https://golf.mossport.ru/", "country": "Россия — Москва",
        "type": "municipal_calendar", "trust_level": 5, "purpose": "Городские турниры, положения, расписания и протоколы",
        "collection_method": "html_review_required", "enabled": True,
        "status": "configured_not_crawled", "notes": "Официальная городская спортивная площадка; проверять документы и протоколы по каждому событию."
    },
    {
        "id": "st-petersburg-golf-events", "name": "Гольф.ру — календарь любительских турниров",
        "url": "https://golf.ru/when_play/lubitelskie/", "country": "Россия — Санкт-Петербург",
        "type": "tournament_calendar", "trust_level": 3, "purpose": "Обнаружение клубных и любительских турниров, включая события Санкт-Петербурга и Ленинградской области",
        "collection_method": "html_review_required", "enabled": True,
        "status": "configured_manual_review", "notes": "Неофициальный агрегатор: даты, победителей и счёт подтверждать у организатора или в протоколе."
    },
    {
        "id": "moscow-oblast-golf-federation", "name": "Федерация гольфа Московской области — календарь",
        "url": "https://mofrg.ru/competitions/calendar/", "country": "Россия — Московская область",
        "type": "regional_calendar", "trust_level": 5, "purpose": "Первенство и чемпионат Московской области, календарь и спортивные документы",
        "collection_method": "html_review_required", "enabled": True,
        "status": "configured_not_crawled", "notes": "Сверять регламент, даты и результаты с официальными публикациями федерации и АГР."
    },
    {
        "id": "krasnodar-golf-events", "name": "АГР — турниры Краснодарского края",
        "url": "https://rusgolf.ru/ru/contests/tournament-calendar", "country": "Россия — Краснодарский край",
        "type": "regional_calendar", "trust_level": 5, "purpose": "Турниры в Геленджик Гольф Резорт, чемпионат края и соревнования Южного федерального округа",
        "collection_method": "html_review_required", "enabled": True,
        "status": "configured_not_crawled", "notes": "Источник официальный, но региональные даты могут меняться; проверить организатора и актуальный регламент."
    },
    {
        "id": "krasnoyarsk-golf-federation", "name": "Красноярская федерация гольфа",
        "url": "https://krasgolf.ru/", "country": "Россия — Красноярский край",
        "type": "regional_federation", "trust_level": 5, "purpose": "Календарь краевых соревнований, новости, детский и студенческий гольф",
        "collection_method": "html_review_required", "enabled": True,
        "status": "configured_not_crawled", "notes": "На сайте опубликован календарь сезона; при сборе сохранять год календаря и дату проверки."
    },
    {
        "id": "astana-golf", "name": "Казахстанская федерация гольфа — турниры в Астане",
        "url": "https://fedgolf.kz/ru", "country": "Казахстан — Астана",
        "type": "regional_tournament_source", "trust_level": 4, "purpose": "Кубок Астаны, Astana Championship Tour и другие турниры клуба Astana",
        "collection_method": "html_review_required", "enabled": True,
        "status": "configured_manual_review", "notes": "На сайте встречаются архивные сезоны; не считать старые даты актуальными без подтверждения организатора."
    },
    {
        "id": "livescoring-results", "name": "Livescoring.ru — история турниров и результаты",
        "url": "https://livescoring.ru/history/", "country": "Россия и СНГ",
        "type": "results_aggregator", "trust_level": 3, "purpose": "Поиск страниц результатов и онлайн-счёта для турниров, включая Москву, Подмосковье и Краснодарский край",
        "collection_method": "html_review_required", "enabled": True,
        "status": "configured_manual_review", "notes": "Агрегатор результатов; победителей и итоговый счёт подтверждать официальным протоколом, если он доступен."
    },
    {
        "id": "wagr", "name": "World Amateur Golf Ranking (WAGR)",
        "url": "https://www.wagr.com/", "country": "Международный",
        "type": "official_ranking", "trust_level": 4, "purpose": "Любительский рейтинг и контекст результатов игроков",
        "collection_method": "terms_and_access_review_required", "enabled": True,
        "status": "configured_manual_review", "notes": "Дополнительный источник рейтинга; не использовать вместо официального протокола турнира."
    },
]

@app.get("/sources")
def list_sources(country: Optional[str] = None, enabled_only: bool = True):
    rows = SOURCE_REGISTRY
    if enabled_only:
        rows = [source for source in rows if source["enabled"]]
    if country:
        rows = [source for source in rows if source["country"].casefold() == country.casefold()]
    return rows

@app.get("/sources/{source_id}")
def get_source(source_id: str):
    from fastapi import HTTPException
    for source in SOURCE_REGISTRY:
        if source["id"] == source_id:
            return source
    raise HTTPException(status_code=404, detail="Источник не найден")
