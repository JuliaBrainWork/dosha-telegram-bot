from dataclasses import dataclass

DOSHAS = ("vata", "pitta", "kapha")
LABELS_SHORT = {"vata": "В", "pitta": "П", "kapha": "К"}
LABELS_LONG = {"vata": "Вата", "pitta": "Питта", "kapha": "Капха"}


@dataclass
class Result:
    mode: str
    raw: dict[str, int]
    normalized: dict[str, int]
    ratio_label: str
    dominant: list[str]


def compute_result(mode: str, answers: dict[str, str]) -> Result:
    raw = {d: 0 for d in DOSHAS}
    for dosha in answers.values():
        if dosha in raw:
            raw[dosha] += 1

    non_zero = [v for v in raw.values() if v > 0]
    min_non_zero = min(non_zero) if non_zero else 1

    normalized: dict[str, int] = {}
    for d in DOSHAS:
        if raw[d] == 0:
            normalized[d] = 0
        else:
            normalized[d] = round(raw[d] / min_non_zero)

    sorted_items = sorted(normalized.items(), key=lambda x: (-x[1], x[0]))
    ratio_label = "".join(f"{LABELS_SHORT[d]}{v}" for d, v in sorted_items)

    max_score = max(normalized.values())
    dominant = [d for d, v in normalized.items() if v == max_score]

    return Result(
        mode=mode,
        raw=raw,
        normalized=normalized,
        ratio_label=ratio_label,
        dominant=dominant,
    )


def dominant_text(dominant: list[str]) -> str:
    if not dominant:
        return "Не определено"
    names = [LABELS_LONG[d] for d in dominant]
    if len(names) == 1:
        return names[0]
    return ", ".join(names)


def mode_title(mode: str) -> str:
    return "Пракрити" if mode == "prakriti" else "Викрити"
