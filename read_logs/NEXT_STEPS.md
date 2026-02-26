# NEXT_STEPS

## Что делать дальше (быстрый чек-лист)

1. Проверка прода в Telegram:
- `/health`
- `/start`
- пройти тест до конца
- проверить итог и `.txt`

2. Проверка Railway:
- Deployments/Logs: нет постоянных ошибок
- Variables: `BOT_TOKEN`, `REDIS_URL`, `REDIS_PASSWORD` (если нужен), `RETENTION_HOURS=24`

3. Если бот не отвечает:
- проверить логи Railway
- проверить Redis-ошибки
- исключить конфликт процессов (если запускался локально)

4. Если нужен новый похожий проект:
- использовать шаблон:
  `/Users/uliatihonova/Library/Containers/Mail.Ru.DiskO.as/Data/Disk-O.as.mounts/arven63@mail.ru-mailru/VS Code/Telegram-bots/PROJECT_WORKFLOW.md`
- в новом чате вставить готовый промпт из этого файла.

## Полезные команды локально

```bash
cd "/Users/uliatihonova/Library/Containers/Mail.Ru.DiskO.as/Data/Disk-O.as.mounts/arven63@mail.ru-mailru/VS Code/Telegram-bots/dosha-telegram-bot"
source .venv/bin/activate
pytest -q
```

```bash
# локальный запуск
python bot.py
```

```bash
# остановить локальные процессы бота
pkill -f "bot.py"
```

## Идеи улучшений (опционально)
- Ограничить двойные нажатия кнопок жестче (анти-спам debounce).
- Добавить расширенную админ-команду статистики.
- Добавить экспорт отчета в PDF (кроме txt).
