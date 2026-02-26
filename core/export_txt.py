from datetime import datetime, timezone

from core.scoring import LABELS_LONG, dominant_text, mode_title


def _append_mode_answers(lines: list[str], mode: str, questions: list[dict], answers: dict[str, str]) -> None:
    lines.append(f"==================== {mode_title(mode)} ====================")
    lines.append(f"🧭 Период: {'0-12 лет (базовое состояние)' if mode == 'prakriti' else 'последние 1-2 месяца (текущее состояние)'}")
    lines.append("")

    for idx, question in enumerate(questions, start=1):
        qid = question["id"]
        selected = answers.get(qid)
        selected_text = "Нет ответа"
        selected_dosha = "-"
        if selected in {"vata", "pitta", "kapha"}:
            selected_text = question["options"][selected]
            selected_dosha = LABELS_LONG[selected]

        lines.append(f"{idx}. {question['title']}")
        lines.append(f"   ✅ Выбор: {selected_dosha}")
        lines.append(f"   📝 Описание: {selected_text}")
        lines.append("")


def build_result_txt(
    user_id: int,
    prakriti_questions: list[dict],
    vikriti_questions: list[dict],
    prakriti_answers: dict[str, str],
    vikriti_answers: dict[str, str],
    prakriti_result: dict,
    vikriti_result: dict,
    combined_summary: str,
) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "🌿 ТЕСТ: ОПРЕДЕЛЕНИЕ ДОШ (ПРАКРИТИ-ВИКРИТИ)",
        "=" * 58,
        "",
        f"📅 Дата: {ts}",
        f"👤 Пользователь Telegram ID: {user_id}",
        "",
        "ОТВЕТЫ:",
        "-" * 58,
        "",
    ]

    _append_mode_answers(lines, "prakriti", prakriti_questions, prakriti_answers)
    _append_mode_answers(lines, "vikriti", vikriti_questions, vikriti_answers)

    lines.extend(
        [
            "-" * 58,
            "ИТОГ ПО ПРАКРИТИ:",
            f"• Общие показатели: В={prakriti_result['raw']['vata']} П={prakriti_result['raw']['pitta']} К={prakriti_result['raw']['kapha']}",
            f"• По формуле: {prakriti_result['ratio_label']}",
            f"• Нормализовано: В={prakriti_result['normalized']['vata']} П={prakriti_result['normalized']['pitta']} К={prakriti_result['normalized']['kapha']}",
            f"• Доминирующая доша: {dominant_text(prakriti_result['dominant'])}",
            "",
            "ИТОГ ПО ВИКРИТИ:",
            f"• Общие показатели: В={vikriti_result['raw']['vata']} П={vikriti_result['raw']['pitta']} К={vikriti_result['raw']['kapha']}",
            f"• По формуле: {vikriti_result['ratio_label']}",
            f"• Нормализовано: В={vikriti_result['normalized']['vata']} П={vikriti_result['normalized']['pitta']} К={vikriti_result['normalized']['kapha']}",
            f"• Доминирующая доша: {dominant_text(vikriti_result['dominant'])}",
            "",
            "📌 ОБЩИЙ ВЫВОД:",
            combined_summary,
            "",
            "🕒 Результаты теста и файл хранятся в системе 24 часа, после чего удаляются автоматически.",
            "",
            "ℹ️ Это общие рекомендации. Для персональной интерпретации покажите результат специалисту аюрведы.",
            "⚠️ Важно: это инструмент самооценки, а не медицинский диагноз.",
        ]
    )

    return "\n".join(lines)
