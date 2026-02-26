from core.scoring import compute_result


def test_pdf_example_ratio() -> None:
    answers = {}
    for i in range(19):
        answers[f"qv{i}"] = "vata"
    for i in range(4):
        answers[f"qp{i}"] = "pitta"
    for i in range(9):
        answers[f"qk{i}"] = "kapha"

    result = compute_result("prakriti", answers)

    assert result.raw == {"vata": 19, "pitta": 4, "kapha": 9}
    assert result.normalized == {"vata": 5, "pitta": 1, "kapha": 2}
    assert result.ratio_label == "В5К2П1"


def test_zero_handling() -> None:
    answers = {
        "q1": "vata",
        "q2": "vata",
        "q3": "kapha",
    }
    result = compute_result("vikriti", answers)

    assert result.raw == {"vata": 2, "pitta": 0, "kapha": 1}
    assert result.normalized == {"vata": 2, "pitta": 0, "kapha": 1}
