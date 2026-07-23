from services.classifier import classify_sentence
from services.semantic_analyzer import analyze_semantics


def _result(subject: str, verb: str, lemma: str, obj: str = "No detectado") -> dict:
    return {
        "available": True,
        "tokens": [{"token": verb, "lemma": lemma}],
        "propositions": [
            {
                "number": 1,
                "sentence_number": 1,
                "text": f"{subject} {verb}",
                "subject": subject,
                "verb": verb,
                "verb_lemma": lemma,
                "object": obj,
            }
        ],
    }


def test_ground_vehicle_flying_is_flagged_as_literal_anomaly():
    text = "El carro del vecino vuela."
    result = _result("El carro del vecino", "vuela", "volar")
    semantic = analyze_semantics(text, classify_sentence(text), result, result)

    proposition = semantic["propositions"][0]
    assert semantic["overall"]["status"] == "warning"
    assert proposition["subject_head"].casefold() == "carro"
    assert proposition["subject_category"] == "ground_vehicle"
    assert proposition["verb_lemma"] == "volar"
    assert "aeronave" in proposition["explanation"]


def test_aircraft_flying_is_semantically_compatible():
    text = "El avión vuela."
    result = _result("El avión", "vuela", "volar")
    semantic = analyze_semantics(text, classify_sentence(text), result, result)

    assert semantic["overall"]["status"] == "coherent"
    assert semantic["propositions"][0]["subject_category"] == "aircraft"


def test_inanimate_subject_studying_is_flagged():
    text = "La piedra estudia."
    result = _result("La piedra", "estudia", "estudiar")
    semantic = analyze_semantics(text, classify_sentence(text), result, result)

    assert semantic["overall"]["status"] == "warning"
    assert "persona" in semantic["propositions"][0]["explanation"]
