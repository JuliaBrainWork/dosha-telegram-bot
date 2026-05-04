# Telegram-бот: тест Пракрити/Викрити

Бот задает вопросы, считает соотношение дош и отправляет:
- итог в сообщении,
- `.txt` файл с ответами и расчетом.

## Что реализовано
- `Python + aiogram`
- `Long polling`
- Хранение сессии в Redis с TTL (`24 часа` по умолчанию)
- Режимы:
  - `Пракрити`: как было стабильно много лет (ориентир 0-12 лет)
  - `Викрити`: последние 1-2 месяца
- Повторный `/start` всегда сбрасывает предыдущую сессию

## Структура
- `bot.py` - запуск
- `config.py` - env конфиг
- `handlers/bot_handlers.py` - команды и сценарий диалога
- `data/questions.json` - 16 + 35 вопросов
- `core/scoring.py` - расчет результатов
- `core/export_txt.py` - генерация `.txt`
- `storage/redis_repo.py` - Redis-репозиторий с TTL
- `tests/test_scoring.py` - тесты формулы расчета

## Локальный запуск
1. Установи Python 3.11-3.13 (рекомендуется) или используй Python 3.14 с флагом совместимости
2. Создай виртуальное окружение:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
3. Установи зависимости:
```bash
pip install -r requirements.txt
```

Если у тебя Python 3.14 и появляется ошибка `pydantic-core`, ставь так:
```bash
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 pip install -r requirements.txt
```
4. Создай `.env` из примера и заполни:
```bash
cp .env.example .env
```
- `BOT_TOKEN` - токен из BotFather
- `REDIS_URL` - URL Redis (например, Upstash)
- `REDIS_PASSWORD` - пароль Redis (если есть)
- `RETENTION_HOURS=24`

5. Запуск:
```bash
python bot.py
```

Если проект лежит в облачной папке и `.venv` не создается из-за ошибки `lib64`,
можно запускать проверки через `uv`:
```bash
uv run --with-requirements requirements.txt python -m pytest -q
uv run --with-requirements requirements.txt python scripts/check_status.py
```

## Проверка дубликатов процесса
Если видишь ошибку `TelegramConflictError`, проверь, не запущено ли несколько копий бота:
```bash
ps ax -o pid=,command= | grep bot.py | grep -v grep
```

Остановить все копии:
```bash
pkill -f "bot.py"
```

И запустить заново один экземпляр:
```bash
source .venv/bin/activate
python bot.py
```

## Тесты
```bash
pytest -q
```

## Диагностика
Команда в Telegram:
```text
/health
```
Показывает uptime, статус Redis и текущий TTL хранения.

Локальная диагностика без вывода секретов:
```bash
python scripts/check_status.py
```

Скрипт показывает, запущен ли локальный процесс, заданы ли env-переменные,
а при наличии `BOT_TOKEN` проверяет `getMe` и `getWebhookInfo` Telegram Bot API.

## Бесплатный деплой на Vercel через webhook
Для бесплатного запуска без always-on worker можно использовать Vercel Hobby.
В этом режиме Telegram отправляет обновления на HTTPS webhook, а не через long polling.

Переменные Vercel:
- `BOT_TOKEN`
- `REDIS_URL`
- `REDIS_PASSWORD` (если нужен)
- `RETENTION_HOURS=24`
- `WEBHOOK_SECRET` - длинная случайная строка

После деплоя:
```bash
VERCEL_URL="https://your-project.vercel.app" python scripts/set_webhook.py
```

Проверка:
```bash
curl https://your-project.vercel.app/health
```

## Бесплатный деплой на Render (для новичка)
1. Зарегистрируйся на `render.com`:
- Нажми `Get Started`.
- Самый простой вход: через GitHub.

2. Подготовь GitHub-репозиторий:
- Загрузи туда этот проект (включая `render.yaml`).

3. Создай сервис на Render:
- В Dashboard нажми `New +` -> `Blueprint`.
- Выбери свой GitHub-репозиторий.
- Render прочитает `render.yaml` и создаст `Worker` сервис.

4. Заполни переменные окружения в Render:
- `BOT_TOKEN`
- `REDIS_URL`
- `REDIS_PASSWORD` (если нужен, иначе оставь пустым)
- `RETENTION_HOURS=24`

5. Нажми Deploy:
- Первый деплой обычно занимает несколько минут.
- После статуса `Live` бот начнет работать без твоего ноутбука.

6. Проверка:
- Открой бота в Telegram.
- Отправь `/health` и `/start`.
- Убедись, что ответы приходят.

## Важно
- Это инструмент самооценки, не медицинский диагноз.
- На бесплатном Render возможен "сон" сервиса: первый ответ после простоя может занимать 20-60 секунд.
