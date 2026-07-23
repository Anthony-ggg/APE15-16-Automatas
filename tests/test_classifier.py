from services.classifier import classify_sentence, detect_connectors


def test_simple_sentence_does_not_match_letters_inside_words():
    result = classify_sentence("Pedro compró un automóvil.")
    assert result["sentence_class"] == "Simple"
    assert result["connector"] == "Ninguno"


def test_coordinated_copulative():
    result = classify_sentence("Pedro llegó y Ana salió.")
    assert result["type"] == "Compuesta Coordinada"
    assert result["relation"] == "Copulativa"
    assert result["connector"].lower() == "y"


def test_subordinate_causal():
    result = classify_sentence("María estudia porque mañana tiene un examen.")
    assert result["type"] == "Compuesta Subordinada"
    assert result["relation"] == "Causal"


def test_multiword_connector_has_priority():
    connectors = detect_connectors("Terminó; por lo tanto, descansó.")
    assert connectors[0]["connector"] == "por lo tanto"
    assert connectors[0]["relation"] == "Consecutiva"


def test_conditional_si_does_not_match_inside_word():
    assert classify_sentence("La música suena.")["sentence_class"] == "Simple"
    assert classify_sentence("Si estudias aprobarás.")["relation"] == "Condicional"
