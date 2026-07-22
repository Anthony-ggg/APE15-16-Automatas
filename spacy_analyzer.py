"""
spacy_analyzer.py
Modulo de analisis NLP con spaCy y benchmark de tiempo de ejecucion.
Carga el modelo es_core_news_sm para espanol.
"""

import time

try:
    import spacy
    nlp = spacy.load("es_core_news_sm")
except OSError:
    nlp = None
except ImportError:
    nlp = None


def _construir_arbol(doc):
    """
    Construye una representacion textual del arbol de dependencias.
    Muestra la jerarquia de gobernante -> dependiente.
    """
    if not doc:
        return "Arbol no disponible"

    # Encontrar la raiz (token cuyo head es el mismo)
    raiz = None
    for token in doc:
        if token.dep_ == "ROOT":
            raiz = token
            break

    if raiz is None:
        raiz = doc[0]

    def _nodo_a_texto(token, nivel=0):
        indent = "  " * nivel
        hijos = [h for h in token.children]
        if not hijos:
            return f"{indent}{token.text} [{token.dep_}]"
        else:
            lineas = [f"{indent}{token.text} [{token.dep_}]"]
            for hijo in hijos:
                lineas.append(_nodo_a_texto(hijo, nivel + 1))
            return "\n".join(lineas)

    return _nodo_a_texto(raiz)


def analizar(texto):
    """
    Procesa el texto con spaCy, midiendo el tiempo de ejecucion.
    Retorna tokens, POS tags, dependencias, NER y arbol de dependencias.
    """
    if nlp is None:
        return {
            "error": (
                "El modelo es_core_news_sm no esta disponible. "
                "Ejecute: python -m spacy download es_core_news_sm"
            )
        }

    inicio = time.perf_counter()
    doc = nlp(texto)
    fin = time.perf_counter()

    tiempo_ms = round((fin - inicio) * 1000, 2)

    tokens_pos = []
    dependencias = []
    entidades = []

    for token in doc:
        tokens_pos.append({
            "token": token.text,
            "pos": token.pos_,
            "tag": token.tag_,
            "lema": token.lemma_,
        })

        dependencias.append({
            "relacion": token.dep_,
            "gobernante": token.head.text,
            "dependiente": token.text,
        })

    # NER (entidades nombradas)
    for ent in doc.ents:
        entidades.append({
            "texto": ent.text,
            "tipo": ent.label_,
        })

    # Arbol de dependencias textual
    arbol_dep = _construir_arbol(doc)

    return {
        "tokens_pos": tokens_pos,
        "dependencias": dependencias,
        "entidades": entidades,
        "arbol_dep": arbol_dep,
        "tiempo_ms": tiempo_ms,
    }
