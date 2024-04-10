## CURRENCY REST

### Сервис для получения данных с бирж и коингеко


Сервис функционально содержит 2 части: API и Celery tasks:

### Фоновые задачи:
Все задачи находятся в директории src/tasks
Расписание задач в src/worker, и управляется celery beat

Основные задачи 
1. get_exchange_markets.py, запускается при старте приложения. Каждые 5 минут запрашивает все тикеры с бирж.
2. get_coingecko_markets.py, каждые 5 минут запрашивает монеты с коингеко, которые не получаем с бирж

Периодические задачи:
1. update_quote_rates.py запришивает с financialmodelingrep курсы фиатных валют, стейблов, и основных котируемых
2. update_coingecko_mapper.py запрашивает 2 раза в сутки с коингеко данные для маппинга тикеров и коингеко id для каждой биржи
3. update_coingecko_coin_ids.py получает список актаульных монет с коингеко.
4. calculate_total_markets.py по всем тикерам полученным с бирж вычисляет рыночную цену и объем торгов для каждой монеты
5. strapi_sync.py синхронизирует данные по биржам (logo,trust rate) со страпи

Также force_mapper.py для быстрого (но, не точного) маппинга тикеров и конгеко айди монет, (вызываем только при первом запуске)

### API:

Основные API находятся в main.py 
1. для получения последних данных по ценам и объемам для каждой монеты
2. для получения исторических данных для данной монеты

Остальные API находятся в src/api/endpoints, для получения данных по биржам, тикерам, и проч.


Основная логика работы с биржами описана в классе Market. src/deps/markets
Бэйзлайн для работы с какждой биржой выглядит так:
1. Загружаем все доступные торговые пары биржи (load_markets)
2. Запрашиваем последнюю цену и объем торгов за 24 часа для каждой торговой пары
3. Приводим полученные тикеры к единому виду, конвертируем цену и объем в доллары
4. Сохраняем каждый тикер в базу

Все пользовательские биржи находятся в src/exchanges
Для добавления биржи нужно 
1. добавить имлементацию класса биржи в src/exchanges
2. дабавить импорт класса в init.py
3. добавить имя биржи в список actual_exchanges в src/lib/quotes
4. добавить в базу данных инфу о бирже (coingecko_id биржи для получения маппера) #todo добавить поле в класс и сделать автоматичское добавление 

запуск приложения
```
docker compose up --build -d
```

При первой инициализции необходимо наполнить маппер биржи:тикер на коингеко id в базе данных,
```
docker compose exec celery_worker celery -A src.worker call src.worker.old_update_mapper_task
```
а также конвертер валют (подождать 5 минут, пока задача выполнится сама)

.env file
```
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_HOST=db
POSTGRES_PORT=5432

DB_URL=
CELERY_BROKER=
CELERY_BACKEND=
REDIS_URL=
REDIS_HOST=redis
REDIS_PORT=6389
FMG_API_KEY=
STRAPI_URL=https://devapp.hodler.sh/strapi
STRAPI_TOKEN=
COINGECKO_TOKEN=
IS_DEV=1
```


