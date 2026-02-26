from html import escape
from io import BytesIO
from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from core.export_txt import build_result_txt
from core.scoring import compute_result, dominant_text, mode_title
from data.loader import load_questions
from storage.redis_repo import RedisRepo

DOSHA_LABELS = {
    "vata": "Вата",
    "pitta": "Питта",
    "kapha": "Капха",
}

MODE_HINT = {
    "prakriti": "🧒 Как было стабильно много лет, ориентир: 0-12 лет.",
    "vikriti": "📅 Как вы чувствуете себя в последние 1-2 месяца.",
}


all_questions = load_questions()
questions_by_mode = {
    "prakriti": [q for q in all_questions if q["mode"] == "prakriti"],
    "vikriti": [q for q in all_questions if q["mode"] == "vikriti"],
}
APP_STARTED_AT = datetime.now(timezone.utc)


def _format_uptime() -> str:
    delta = datetime.now(timezone.utc) - APP_STARTED_AT
    total = int(delta.total_seconds())
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def question_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🟡 Вата", callback_data="ans:vata"),
                InlineKeyboardButton(text="🔴 Питта", callback_data="ans:pitta"),
                InlineKeyboardButton(text="🔵 Капха", callback_data="ans:kapha"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="nav:back"),
                InlineKeyboardButton(text="🔄 Сброс", callback_data="nav:reset"),
            ],
        ]
    )


def format_question_text(mode: str, index: int, total: int, question: dict, current: str | None) -> str:
    selected = f"\n\n✅ Текущий выбор: <b>{DOSHA_LABELS[current]}</b>" if current else ""
    step = "Шаг 1/2" if mode == "prakriti" else "Шаг 2/2"
    return (
        "<b>Тест: Определение дош (Пракрити-Викрити)</b>\n\n"
        f"<b>{step} — {mode_title(mode)}</b>\n"
        f"{escape(MODE_HINT[mode])}\n\n"
        f"<b>Вопрос {index + 1} из {total}:</b> {escape(question['title'])}\n\n"
        f"<b>🟡 Вата:</b> {escape(question['options']['vata'])}\n\n"
        f"<b>🔴 Питта:</b> {escape(question['options']['pitta'])}\n\n"
        f"<b>🔵 Капха:</b> {escape(question['options']['kapha'])}\n\n"
        f"{selected}"
    )


def combined_summary(prakriti_dominant: list[str], vikriti_dominant: list[str]) -> str:
    p = dominant_text(prakriti_dominant)
    v = dominant_text(vikriti_dominant)

    if set(prakriti_dominant) == set(vikriti_dominant):
        status = "Текущая картина в целом близка к базовой конституции."
    else:
        status = "Есть смещение текущего состояния относительно базовой конституции."

    tips = [
        "Соблюдайте регулярный режим сна и питания.",
        "Снижайте стресс и перегрузки в течение дня.",
        "Отслеживайте изменения самочувствия в динамике каждые 1-2 месяца.",
    ]

    return (
        f"Пракрити: {p}. Викрити: {v}.\n"
        f"{status}\n"
        f"Рекомендации: {' '.join(tips)}"
    )


async def _show_question(target: Message | CallbackQuery, text: str, *, edit: bool) -> None:
    if isinstance(target, Message):
        await target.answer(text, reply_markup=question_keyboard(), parse_mode="HTML")
        return

    if edit and target.message:
        try:
            await target.message.edit_text(text, reply_markup=question_keyboard(), parse_mode="HTML")
            return
        except TelegramBadRequest as exc:
            # Common case when user double-clicks and text has not changed yet.
            if "message is not modified" in str(exc).lower():
                return
            pass

    if target.message:
        await target.message.answer(text, reply_markup=question_keyboard(), parse_mode="HTML")


async def send_current_question(target: Message | CallbackQuery, repo: RedisRepo, user_id: int, *, edit: bool) -> None:
    session = await repo.get_session(user_id)
    if not session:
        text = "Сессия не найдена. Нажмите /start, чтобы начать тест."
        if isinstance(target, Message):
            await target.answer(text)
        else:
            await target.answer("Сессия не найдена", show_alert=True)
            if target.message:
                await target.message.answer(text)
        return

    mode = session["current_mode"]
    questions = questions_by_mode[mode]
    index = session["current_index"]

    index = max(0, min(index, len(questions) - 1))
    question = questions[index]
    current = session["answers"][mode].get(question["id"])

    text = format_question_text(mode, index, len(questions), question, current)
    await _show_question(target, text, edit=edit)



def build_router(repo: RedisRepo) -> Router:
    router = Router()

    @router.message(Command("health"))
    async def cmd_health(message: Message) -> None:
        redis_ok = True
        redis_error = ""
        try:
            await repo.redis.ping()
        except Exception as exc:  # noqa: BLE001
            redis_ok = False
            redis_error = str(exc)

        status = (
            "<b>🔎 Состояние бота</b>\n\n"
            f"• Uptime: <b>{_format_uptime()}</b>\n"
            f"• Redis: <b>{'OK' if redis_ok else 'ERROR'}</b>\n"
            f"• TTL хранения: <b>{repo.retention_hours} ч</b>\n"
            "• Режим: <b>Long Polling</b>\n"
        )
        if not redis_ok:
            status += f"\n• Ошибка Redis: <code>{escape(redis_error[:250])}</code>\n"

        await message.answer(status, parse_mode="HTML")

    @router.message(CommandStart())
    async def cmd_start(message: Message) -> None:
        await repo.delete_session(message.from_user.id)
        await repo.create_new_session(message.from_user.id)

        intro = (
            "<b>Тест: Определение дош (Пракрити-Викрити)</b>\n\n"
            "Вы пройдете <b>2 шага подряд</b>:\n"
            "1) <b>Пракрити</b> (базовое состояние, ориентир 0-12 лет)\n"
            "2) <b>Викрити</b> (текущее состояние за последние 1-2 месяца)\n\n"
            "В конце получите <b>общий вывод</b> и <b>.txt файл</b>.\n\n"
            "🕒 Результаты теста и файл хранятся в системе <b>24 часа</b>, "
            "после чего удаляются автоматически.\n"
            "☁️ Если бот работает на бесплатном хостинге, первый ответ после простоя может прийти с задержкой 20-60 секунд."
        )
        await message.answer(intro, parse_mode="HTML")
        await send_current_question(message, repo, message.from_user.id, edit=False)

    @router.callback_query(F.data.startswith("ans:"))
    async def on_answer(callback: CallbackQuery) -> None:
        dosha = callback.data.split(":", 1)[1]
        if dosha not in {"vata", "pitta", "kapha"}:
            await callback.answer("Некорректный выбор", show_alert=True)
            return

        session = await repo.get_session(callback.from_user.id)
        if not session:
            await callback.answer("Сначала нажмите /start", show_alert=True)
            return

        mode = session["current_mode"]
        questions = questions_by_mode[mode]
        idx = session["current_index"]
        question = questions[idx]

        session["answers"][mode][question["id"]] = dosha

        if idx >= len(questions) - 1:
            if mode == "prakriti":
                session["current_mode"] = "vikriti"
                session["current_index"] = 0
                await repo.save_session(callback.from_user.id, session)

                await callback.answer("Шаг 1 завершен")
                if callback.message:
                    await callback.message.answer(
                        "<b>✅ Шаг 1/2 завершен: Пракрити.</b>\n"
                        "Переходим к <b>шагу 2/2: Викрити</b>.",
                        parse_mode="HTML",
                    )
                # Show first question of step 2 as a new message below transition notice.
                await send_current_question(callback, repo, callback.from_user.id, edit=False)
                return

            await repo.save_session(callback.from_user.id, session)
            await callback.answer("Тест завершен")

            prakriti_answers = session["answers"]["prakriti"]
            vikriti_answers = session["answers"]["vikriti"]

            prakriti_result_obj = compute_result("prakriti", prakriti_answers)
            vikriti_result_obj = compute_result("vikriti", vikriti_answers)

            prakriti_result = {
                "raw": prakriti_result_obj.raw,
                "normalized": prakriti_result_obj.normalized,
                "ratio_label": prakriti_result_obj.ratio_label,
                "dominant": prakriti_result_obj.dominant,
            }
            vikriti_result = {
                "raw": vikriti_result_obj.raw,
                "normalized": vikriti_result_obj.normalized,
                "ratio_label": vikriti_result_obj.ratio_label,
                "dominant": vikriti_result_obj.dominant,
            }

            summary_text = combined_summary(prakriti_result_obj.dominant, vikriti_result_obj.dominant)

            summary = (
                "<b>✅ Тест завершен</b>\n\n"
                "<b>Шаг 1/2 — Пракрити</b>\n"
                "<b>1) Общие показатели:</b>\n"
                f"• В={prakriti_result_obj.raw['vata']} П={prakriti_result_obj.raw['pitta']} К={prakriti_result_obj.raw['kapha']}\n"
                "<b>2) Расчет по формуле:</b>\n"
                f"• Формула: {prakriti_result_obj.ratio_label}\n"
                f"• Нормализовано: В={prakriti_result_obj.normalized['vata']} П={prakriti_result_obj.normalized['pitta']} К={prakriti_result_obj.normalized['kapha']}\n"
                "<b>3) Доминирующая доша:</b>\n"
                f"• {dominant_text(prakriti_result_obj.dominant)}\n\n"
                "<b>Шаг 2/2 — Викрити</b>\n"
                "<b>1) Общие показатели:</b>\n"
                f"• В={vikriti_result_obj.raw['vata']} П={vikriti_result_obj.raw['pitta']} К={vikriti_result_obj.raw['kapha']}\n"
                "<b>2) Расчет по формуле:</b>\n"
                f"• Формула: {vikriti_result_obj.ratio_label}\n"
                f"• Нормализовано: В={vikriti_result_obj.normalized['vata']} П={vikriti_result_obj.normalized['pitta']} К={vikriti_result_obj.normalized['kapha']}\n"
                "<b>3) Доминирующая доша:</b>\n"
                f"• {dominant_text(vikriti_result_obj.dominant)}\n\n"
                f"<b>📌 Общий вывод:</b>\n{escape(summary_text)}\n\n"
                "ℹ️ Это <b>общие рекомендации</b>. Для интерпретации результатов и персональных рекомендаций покажите тест специалисту аюрведы.\n"
                "🕒 Результаты теста и файл хранятся в системе <b>24 часа</b>, после чего удаляются автоматически.\n"
                "⚠️ Важно: это инструмент самооценки, а не медицинский диагноз."
            )
            if callback.message:
                await callback.message.answer(summary, parse_mode="HTML")

            txt = build_result_txt(
                user_id=callback.from_user.id,
                prakriti_questions=questions_by_mode["prakriti"],
                vikriti_questions=questions_by_mode["vikriti"],
                prakriti_answers=prakriti_answers,
                vikriti_answers=vikriti_answers,
                prakriti_result=prakriti_result,
                vikriti_result=vikriti_result,
                combined_summary=summary_text,
            )
            filename = f"result_full_{callback.from_user.id}.txt"
            bio = BytesIO(txt.encode("utf-8"))
            doc = BufferedInputFile(file=bio.getvalue(), filename=filename)
            if callback.message:
                await callback.message.answer_document(doc, caption="📄 Общий файл с результатами Пракрити и Викрити")
                await callback.message.answer("Чтобы пройти заново, нажмите /start", parse_mode="HTML")
            return

        session["current_index"] = idx + 1
        await repo.save_session(callback.from_user.id, session)
        await callback.answer("✅ Ответ принят. Переходим к следующему вопросу.")
        # New message gives clearer visual cue that next question appeared.
        if callback.message:
            try:
                await callback.message.delete()
            except TelegramBadRequest:
                pass
        await send_current_question(callback, repo, callback.from_user.id, edit=False)

    @router.callback_query(F.data == "nav:back")
    async def on_back(callback: CallbackQuery) -> None:
        session = await repo.get_session(callback.from_user.id)
        if not session:
            await callback.answer("Сессия не найдена", show_alert=True)
            return

        mode = session["current_mode"]
        idx = session["current_index"]

        if idx > 0:
            session["current_index"] = idx - 1
        elif mode == "vikriti":
            session["current_mode"] = "prakriti"
            session["current_index"] = len(questions_by_mode["prakriti"]) - 1
        else:
            await callback.answer("Это первый вопрос")
            await send_current_question(callback, repo, callback.from_user.id, edit=True)
            return

        await repo.save_session(callback.from_user.id, session)
        await callback.answer()
        await send_current_question(callback, repo, callback.from_user.id, edit=True)

    @router.callback_query(F.data == "nav:reset")
    async def on_reset(callback: CallbackQuery) -> None:
        await repo.delete_session(callback.from_user.id)
        await repo.create_new_session(callback.from_user.id)
        await callback.answer("Тест сброшен")
        if callback.message:
            await callback.message.answer(
                "🔄 Тест сброшен. Начинаем заново.\n"
                "Если хотите запустить тест вручную, команда: /start"
            )
        await send_current_question(callback, repo, callback.from_user.id, edit=True)

    @router.message()
    async def on_fallback(message: Message) -> None:
        await message.answer("Используйте /start, чтобы начать или перезапустить тест.")

    return router
