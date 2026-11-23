# Backend — Мир Гольфа

Backend — отдельный Python-сервис. Текущий GitHub Pages frontend остаётся статическим: создание backend само по себе не подключает его к сайту. Для этого потребуется развернуть API на сервере и настроить frontend на его URL.

## Установка и запуск

Python 3.11+:

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: `/health`, `/api/v1/tournaments`, `/api/v1/tournaments/{id}`, `/api/v1/sources`, `/api/v1/sources/{id}`. Swagger: `/docs`.

Турниры загружаются из `data/tournaments.json`. Сейчас массив пуст: неподтверждённые демонстрационные события не публикуются как факты. Статус `scheduled/live/finished` вычисляется по датам в часовом поясе Europe/Moscow.

## Мониторинг источников

```bash
python -m app.collectors.monitor
python -m app.scheduler
```

Монитор только сохраняет снимки и помещает изменения в очередь ручной проверки. Он не извлекает автоматически победителей и счёт. Перед эксплуатацией проверьте правила сайтов, robots.txt и допустимость автоматического доступа.

Переменные окружения:
- `GOLF_CIS_CORS_ORIGINS` — список разрешённых origins через запятую.
- `GOLF_CIS_SOURCES` — путь к JSON реестру.
- `GOLF_CIS_MONITOR_DB` — путь к SQLite.
- `GOLF_CIS_TIMEOUT` — таймаут запроса в секундах.
- `GOLF_CIS_MAX_BYTES` — максимальный размер ответа (по умолчанию 2 MiB).
- `GOLF_CIS_REQUEST_DELAY` — пауза между разными URL.

SQLite использует WAL. Повторяющиеся URL запрашиваются один раз за запуск, результат привязывается ко всем соответствующим source IDs. При redirect проверяется robots.txt каждого целевого хоста. При ошибке проверки robots сбор прекращается.

## Тесты

```bash
pytest -q
```

Это базовая реализация change detection, не production-платформа: перед публичным запуском нужны наблюдаемость, резервное копирование, ручная модерация и проверка каждого источника.
