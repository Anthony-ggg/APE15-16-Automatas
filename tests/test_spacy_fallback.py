from spacy.tokens import Doc
from spacy.vocab import Vocab

from analyzers.spacy_analyzer import _sentence_propositions


def test_lexical_backup_recovers_vuela_when_model_marks_it_as_noun():
    # Simula el error observado con el modelo pequeño: «carro» como ROOT y
    # «vuela» etiquetado como NOUN. El respaldo debe recuperar el verbo real.
    doc = Doc(
        Vocab(),
        words=["El", "carro", "del", "vecino", "vuela"],
        spaces=[True, True, True, True, False],
        heads=[1, 1, 1, 1, 1],
        deps=["det", "ROOT", "case", "nmod", "appos"],
        pos=["DET", "NOUN", "ADP", "NOUN", "NOUN"],
        sent_starts=[True, False, False, False, False],
    )

    proposition = _sentence_propositions(list(doc.sents)[0])[0]

    assert proposition["subject"] == "El carro del vecino"
    assert proposition["subject_head"] == "carro"
    assert proposition["verb"] == "vuela"
    assert proposition["verb_lemma"] == "volar"
    assert proposition["object"] == "No detectado"
