"""Análisis semántico explicable mediante roles y restricciones de selección.

La APE 16 solicita clasificación semántica. CoreNLP y spaCy aportan la
estructura, pero no deciden por sí solos si una oración es plausible en el
mundo real. Este módulo añade una capa de reglas transparentes: identifica
las categorías del sujeto/objeto y verifica si son compatibles con el verbo.

El resultado es una advertencia lingüística, no una verdad absoluta: una
metáfora, una historia fantástica o un contexto técnico pueden cambiar la
interpretación de la oración.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.linguistic_rules import normalize_term, verb_lemma, word_tokens


@dataclass(frozen=True)
class EntityEntry:
    category: str
    label: str


ENTITY_LEXICON: dict[str, EntityEntry] = {}


def _register(words: str, category: str, label: str) -> None:
    for word in words.split():
        ENTITY_LEXICON[normalize_term(word)] = EntityEntry(category, label)


_register(
    "persona personas hombre mujer niño niña joven adulto estudiante profesor profesora "
    "docente vecino vecina maria pedro ana luis juan carlos sofia",
    "human",
    "persona",
)
_register("perro perros gato gatos caballo caballos vaca vacas leon leones mono monos", "animal", "animal")
_register("pajaro pajaros ave aves aguila aguilas canario canarios paloma palomas", "flying_animal", "animal volador")
_register("avion aviones helicoptero helicopteros dron drones cohete cohetes avioneta avionetas", "aircraft", "aeronave")
_register(
    "carro carros automovil automoviles coche coches camion camiones bus buses autobus autobuses "
    "moto motos motocicleta motocicletas bicicleta bicicletas tractor tractores",
    "ground_vehicle",
    "vehículo terrestre",
)
_register("barco barcos lancha lanchas buque buques", "water_vehicle", "vehículo acuático")
_register(
    "mesa mesas silla sillas piedra piedras libro libros lapiz lapices puerta puertas pared paredes "
    "pelota pelotas telefono telefonos computadora computadoras robot robots maquina maquinas",
    "inanimate_object",
    "objeto inanimado",
)
_register("pan panes comida comidas cena cenas almuerzo almuerzos fruta frutas carne carnes", "food", "alimento")
_register("agua aguas jugo jugos leche cafe cafes bebida bebidas", "liquid", "líquido")
_register("texto textos novela novelas cuento cuentos carta cartas informe informes", "text", "texto")
_register("idea ideas teoria teorias libertad amor tiempo examen examenes musica", "abstract", "entidad abstracta")
_register("parque parques casa casas escuela escuelas universidad universidades ciudad ciudades", "place", "lugar")
_register("arbol arboles planta plantas flor flores", "plant", "planta")


@dataclass(frozen=True)
class VerbFrame:
    allowed_subjects: frozenset[str] | None = None
    allowed_objects: frozenset[str] | None = None
    subject_description: str = ""
    object_description: str = ""
    impersonal: bool = False


ANIMATE = frozenset({"human", "animal", "flying_animal"})
MOVING_ENTITY = frozenset({
    "human", "animal", "flying_animal", "aircraft", "ground_vehicle", "water_vehicle",
})

VERB_FRAMES: dict[str, VerbFrame] = {
    "volar": VerbFrame(
        allowed_subjects=frozenset({"flying_animal", "aircraft"}),
        subject_description="un animal con capacidad de vuelo o una aeronave",
    ),
    "estudiar": VerbFrame(
        allowed_subjects=frozenset({"human"}),
        subject_description="una persona",
    ),
    "aprobar": VerbFrame(
        allowed_subjects=frozenset({"human"}),
        subject_description="una persona o estudiante",
    ),
    "cocinar": VerbFrame(
        allowed_subjects=frozenset({"human"}),
        allowed_objects=frozenset({"food"}),
        subject_description="una persona",
        object_description="un alimento o preparación",
    ),
    "limpiar": VerbFrame(
        allowed_subjects=frozenset({"human"}),
        subject_description="una persona",
    ),
    "comprar": VerbFrame(
        allowed_subjects=frozenset({"human"}),
        subject_description="una persona u organización",
    ),
    "jugar": VerbFrame(
        allowed_subjects=ANIMATE,
        subject_description="un ser animado",
    ),
    "comer": VerbFrame(
        allowed_subjects=ANIMATE,
        allowed_objects=frozenset({"food"}),
        subject_description="un ser animado",
        object_description="un alimento",
    ),
    "beber": VerbFrame(
        allowed_subjects=ANIMATE,
        allowed_objects=frozenset({"liquid"}),
        subject_description="un ser animado",
        object_description="un líquido",
    ),
    "leer": VerbFrame(
        allowed_subjects=frozenset({"human"}),
        allowed_objects=frozenset({"text"}),
        subject_description="una persona",
        object_description="un texto",
    ),
    "escribir": VerbFrame(
        allowed_subjects=frozenset({"human"}),
        allowed_objects=frozenset({"text", "abstract"}),
        subject_description="una persona",
        object_description="un texto o contenido",
    ),
    "hablar": VerbFrame(
        allowed_subjects=frozenset({"human"}),
        subject_description="una persona",
    ),
    "pensar": VerbFrame(
        allowed_subjects=frozenset({"human"}),
        subject_description="una persona",
    ),
    "dormir": VerbFrame(
        allowed_subjects=ANIMATE,
        subject_description="un ser animado",
    ),
    "conducir": VerbFrame(
        allowed_subjects=frozenset({"human"}),
        subject_description="una persona",
    ),
    "llegar": VerbFrame(
        allowed_subjects=MOVING_ENTITY,
        subject_description="una entidad capaz de desplazarse",
    ),
    "salir": VerbFrame(
        allowed_subjects=MOVING_ENTITY,
        subject_description="una entidad capaz de desplazarse",
    ),
    "ir": VerbFrame(
        allowed_subjects=MOVING_ENTITY,
        subject_description="una entidad capaz de desplazarse",
    ),
    "avanzar": VerbFrame(
        allowed_subjects=MOVING_ENTITY,
        subject_description="una entidad capaz de desplazarse",
    ),
    "llover": VerbFrame(impersonal=True),
    "tener": VerbFrame(),
}

DETERMINERS_AND_LINKS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "mi", "mis", "tu", "tus",
    "su", "sus", "este", "esta", "estos", "estas", "ese", "esa", "del", "de", "al", "a",
}


def _entity_from_phrase(phrase: str) -> dict[str, str | None]:
    if normalize_term(phrase) in {"", "no detectado", "sujeto omitido/implicito", "sujeto omitido"}:
        return {
            "head": None,
            "normalized_head": None,
            "category": "missing",
            "category_label": "no detectada",
        }
    words = word_tokens(phrase)
    normalized_words = [normalize_term(word) for word in words]

    # Se toma la primera palabra con categoría conocida. En "el carro del
    # vecino" esto evita confundir el complemento "vecino" con el núcleo
    # "carro".
    for original, normalized in zip(words, normalized_words):
        entry = ENTITY_LEXICON.get(normalized)
        if entry:
            return {
                "head": original,
                "normalized_head": normalized,
                "category": entry.category,
                "category_label": entry.label,
            }

    content = [
        (original, normalized)
        for original, normalized in zip(words, normalized_words)
        if normalized not in DETERMINERS_AND_LINKS
    ]
    if content:
        original, normalized = content[0]
        return {
            "head": original,
            "normalized_head": normalized,
            "category": "unknown",
            "category_label": "categoría no registrada",
        }
    return {
        "head": None,
        "normalized_head": None,
        "category": "missing",
        "category_label": "no detectada",
    }


def _valid_value(value: Any) -> bool:
    normalized = normalize_term(str(value or ""))
    return bool(normalized and normalized not in {"no detectado", "sujeto omitido", "sujeto omitido/implicito"})


def _proposition_score(item: dict) -> int:
    score = 0
    if _valid_value(item.get("verb")):
        score += 4
    if _valid_value(item.get("subject")):
        score += 3
    if _valid_value(item.get("object")):
        score += 1
    if verb_lemma(str(item.get("verb", "")), str(item.get("verb_lemma", ""))):
        score += 3
    return score


def _select_propositions(spacy_result: dict, corenlp_result: dict) -> list[dict]:
    """Combina resultados y elige la extracción más informativa por posición."""
    spacy_items = spacy_result.get("propositions", []) if spacy_result.get("available") else []
    core_items = corenlp_result.get("propositions", []) if corenlp_result.get("available") else []
    total = max(len(spacy_items), len(core_items))
    selected: list[dict] = []
    for index in range(total):
        candidates: list[tuple[str, dict]] = []
        if index < len(spacy_items):
            candidates.append(("spaCy", spacy_items[index]))
        if index < len(core_items):
            candidates.append(("Stanford CoreNLP", core_items[index]))
        if not candidates:
            continue
        source, best = max(candidates, key=lambda pair: _proposition_score(pair[1]))
        merged = dict(best)
        merged["source"] = source
        selected.append(merged)
    return selected


def _token_lemma_for_verb(verb: str, result: dict) -> str | None:
    normalized_verb = normalize_term(verb)
    for token in result.get("tokens", []):
        if normalize_term(str(token.get("token", ""))) == normalized_verb:
            lemma = str(token.get("lemma", ""))
            known = verb_lemma(verb, lemma)
            return known or normalize_term(lemma) or None
    return verb_lemma(verb)


def _semantic_check(item: dict, spacy_result: dict, corenlp_result: dict) -> dict[str, Any]:
    subject = str(item.get("subject", "No detectado"))
    verb = str(item.get("verb", "No detectado"))
    obj = str(item.get("object", "No detectado"))
    source_result = corenlp_result if item.get("source") == "Stanford CoreNLP" else spacy_result
    lemma = str(item.get("verb_lemma") or "") or _token_lemma_for_verb(verb, source_result) or verb_lemma(verb) or normalize_term(verb)

    subject_entity = _entity_from_phrase(subject)
    object_entity = _entity_from_phrase(obj)
    frame = VERB_FRAMES.get(normalize_term(lemma))
    findings: list[dict[str, str]] = []

    if frame is None:
        status = "unknown"
        label = "Análisis no concluyente"
        explanation = (
            f"Se identificó el verbo «{verb}», pero todavía no existe una regla de "
            "compatibilidad para ese verbo. La estructura sintáctica sí fue analizada."
        )
    elif frame.impersonal:
        if _valid_value(subject):
            status = "warning"
            label = "Posible anomalía semántica"
            explanation = f"El verbo «{lemma}» suele emplearse de forma impersonal y no requiere un sujeto léxico."
            findings.append({"role": "sujeto", "result": "incompatible", "detail": explanation})
        else:
            status = "coherent"
            label = "Compatible según las reglas"
            explanation = f"El uso impersonal del verbo «{lemma}» es compatible con la oración."
    else:
        incompatibilities: list[str] = []
        unknowns: list[str] = []

        if frame.allowed_subjects is not None:
            subject_category = str(subject_entity["category"])
            if subject_category == "unknown":
                unknowns.append("No se pudo determinar la categoría semántica del sujeto.")
            elif subject_category == "missing":
                unknowns.append("El sujeto puede estar omitido o no fue detectado.")
            elif subject_category not in frame.allowed_subjects:
                incompatibilities.append(
                    f"El sujeto «{subject}» se reconoce como {subject_entity['category_label']}, "
                    f"pero «{lemma}» normalmente requiere {frame.subject_description}."
                )
            else:
                findings.append(
                    {
                        "role": "sujeto",
                        "result": "compatible",
                        "detail": f"{subject_entity['category_label']} compatible con «{lemma}».",
                    }
                )

        if frame.allowed_objects is not None and _valid_value(obj):
            object_category = str(object_entity["category"])
            if object_category == "unknown":
                unknowns.append("No se pudo determinar la categoría semántica del objeto directo.")
            elif object_category not in frame.allowed_objects:
                incompatibilities.append(
                    f"El objeto «{obj}» se reconoce como {object_entity['category_label']}, "
                    f"pero «{lemma}» normalmente selecciona {frame.object_description}."
                )
            else:
                findings.append(
                    {
                        "role": "objeto directo",
                        "result": "compatible",
                        "detail": f"{object_entity['category_label']} compatible con «{lemma}».",
                    }
                )

        if incompatibilities:
            status = "warning"
            label = "Posible anomalía semántica literal"
            explanation = " ".join(incompatibilities)
            findings.extend(
                {"role": "restricción de selección", "result": "incompatible", "detail": detail}
                for detail in incompatibilities
            )
        elif unknowns:
            status = "unknown"
            label = "Análisis parcialmente concluyente"
            explanation = " ".join(unknowns)
        else:
            status = "coherent"
            label = "Compatible según las reglas"
            explanation = (
                f"Los roles detectados son compatibles con las restricciones registradas para el verbo «{lemma}»."
            )

    suggestions: list[str] = []
    if status == "warning" and normalize_term(lemma) == "volar":
        suggestions = ["El avión vuela.", "El pájaro vuela.", "El carro del vecino avanza."]

    return {
        "number": item.get("number"),
        "sentence_number": item.get("sentence_number"),
        "text": item.get("text", ""),
        "source": item.get("source"),
        "subject": subject,
        "subject_head": subject_entity["head"],
        "subject_category": subject_entity["category"],
        "subject_category_label": subject_entity["category_label"],
        "verb": verb,
        "verb_lemma": lemma,
        "object": obj,
        "object_head": object_entity["head"],
        "object_category": object_entity["category"],
        "object_category_label": object_entity["category_label"],
        "status": status,
        "label": label,
        "explanation": explanation,
        "findings": findings,
        "suggestions": suggestions,
    }


def analyze_semantics(
    text: str,
    classification: dict,
    spacy_result: dict,
    corenlp_result: dict,
) -> dict[str, Any]:
    selected = _select_propositions(spacy_result, corenlp_result)
    evaluations = [
        _semantic_check(item, spacy_result, corenlp_result)
        for item in selected
    ]

    statuses = {item["status"] for item in evaluations}
    if "warning" in statuses:
        overall_status = "warning"
        overall_label = "Posible anomalía semántica"
        summary = (
            "Se detectó al menos una incompatibilidad entre los roles semánticos y el verbo "
            "en una interpretación literal."
        )
    elif evaluations and statuses <= {"coherent"}:
        overall_status = "coherent"
        overall_label = "Sin anomalías detectadas"
        summary = "Las reglas disponibles no detectaron incompatibilidades semánticas literales."
    else:
        overall_status = "unknown"
        overall_label = "Análisis no concluyente"
        summary = "La estructura fue procesada, pero faltan reglas o categorías para emitir una conclusión completa."

    relation = classification.get("relation", "Sin relación compuesta")
    connector = classification.get("connector", "Ninguno")
    relation_explanation = (
        "La oración es simple y no expresa una relación entre proposiciones mediante los conectores registrados."
        if classification.get("sentence_class") == "Simple"
        else f"El conector «{connector}» establece una relación {str(relation).lower()} entre proposiciones."
    )

    return {
        "approach": "Reglas semánticas explicables y restricciones de selección",
        "overall": {
            "status": overall_status,
            "label": overall_label,
            "summary": summary,
        },
        "relation_semantics": {
            "relation": relation,
            "connector": connector,
            "explanation": relation_explanation,
        },
        "propositions": evaluations,
        "coverage": {
            "evaluated": len(evaluations),
            "with_rule": sum(1 for item in evaluations if item["status"] != "unknown"),
        },
        "limitations": (
            "El resultado evalúa compatibilidad literal con un conjunto de reglas transparentes. "
            "No demuestra que una frase sea falsa: metáforas, personificación, ciencia ficción o un contexto "
            "especial pueden volver válida una combinación aparentemente inusual."
        ),
        "input": text,
    }
