"""Reglas lingüísticas compartidas para respaldar a los analizadores.

Estas reglas no sustituyen a spaCy ni CoreNLP. Se aplican únicamente cuando
un modelo etiqueta de forma dudosa una forma verbal frecuente en español.
"""

from __future__ import annotations

import re
import unicodedata


def normalize_term(value: str) -> str:
    """Convierte texto a minúsculas y elimina tildes para comparar reglas."""
    decomposed = unicodedata.normalize("NFD", (value or "").casefold().strip())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


# Formas frecuentes usadas en las prácticas y en pruebas de coherencia.
# El diccionario es deliberadamente explícito para no confundir sustantivos
# con verbos mediante terminaciones demasiado generales.
_VERB_FORMS: dict[str, set[str]] = {
    "volar": {
        "volar", "vuelo", "vuelas", "vuela", "volamos", "volais", "vuelan",
        "vole", "volo", "volaron", "volaba", "volaban", "volara", "volaran",
        "volaria", "volarian", "volando", "volado",
    },
    "estudiar": {
        "estudiar", "estudio", "estudias", "estudia", "estudiamos", "estudian",
        "estudie", "estudio", "estudiaron", "estudiaba", "estudiaban", "estudiando",
    },
    "tener": {
        "tener", "tengo", "tienes", "tiene", "tenemos", "tienen", "tuvo",
        "tuvieron", "tenia", "tenian", "tendra", "tendran", "teniendo", "tenido",
    },
    "llegar": {
        "llegar", "llego", "llegas", "llega", "llegamos", "llegan", "llegue",
        "llegaron", "llegaba", "llegando", "llegado",
    },
    "salir": {
        "salir", "salgo", "sales", "sale", "salimos", "salen", "salio", "salieron",
        "salia", "saldra", "saliendo", "salido",
    },
    "llover": {"llover", "llueve", "llovio", "llovia", "llovera", "lloviendo", "llovido"},
    "ir": {
        "ir", "voy", "vas", "va", "vamos", "vais", "van", "fui", "fue", "fuimos",
        "fueron", "iba", "iban", "ire", "iras", "ira", "iran", "iremos", "yendo", "ido",
    },
    "aprobar": {
        "aprobar", "apruebo", "apruebas", "aprueba", "aprobamos", "aprueban",
        "aprobo", "aprobaron", "aprobare", "aprobaras", "aprobara", "aprobando", "aprobado",
    },
    "cocinar": {
        "cocinar", "cocino", "cocinas", "cocina", "cocinamos", "cocinan", "cocino",
        "cocinaron", "cocinaba", "cocinando", "cocinado",
    },
    "limpiar": {
        "limpiar", "limpio", "limpias", "limpia", "limpiamos", "limpian", "limpio",
        "limpiaron", "limpiaba", "limpiando", "limpiado",
    },
    "comprar": {
        "comprar", "compro", "compras", "compra", "compramos", "compran", "compro",
        "compraron", "compraba", "comprando", "comprado",
    },
    "jugar": {
        "jugar", "juego", "juegas", "juega", "jugamos", "juegan", "jugo", "jugaron",
        "jugaba", "jugando", "jugado",
    },
    "comer": {
        "comer", "como", "comes", "come", "comemos", "comen", "comio", "comieron",
        "comia", "comiendo", "comido",
    },
    "beber": {
        "beber", "bebo", "bebes", "bebe", "bebemos", "beben", "bebio", "bebieron",
        "bebia", "bebiendo", "bebido",
    },
    "leer": {
        "leer", "leo", "lees", "lee", "leemos", "leen", "leyo", "leyeron", "leia",
        "leyendo", "leido",
    },
    "escribir": {
        "escribir", "escribo", "escribes", "escribe", "escribimos", "escriben",
        "escribio", "escribieron", "escribia", "escribiendo", "escrito",
    },
    "hablar": {
        "hablar", "hablo", "hablas", "habla", "hablamos", "hablan", "hablo",
        "hablaron", "hablando", "hablado",
    },
    "pensar": {
        "pensar", "pienso", "piensas", "piensa", "pensamos", "piensan", "penso",
        "pensaron", "pensando", "pensado",
    },
    "dormir": {
        "dormir", "duermo", "duermes", "duerme", "dormimos", "duermen", "durmio",
        "durmieron", "durmiendo", "dormido",
    },
    "conducir": {
        "conducir", "conduzco", "conduces", "conduce", "conducimos", "conducen",
        "condujo", "condujeron", "conduciendo", "conducido",
    },
    "avanzar": {
        "avanzar", "avanzo", "avanzas", "avanza", "avanzamos", "avanzan", "avanzo",
        "avanzaron", "avanzando", "avanzado",
    },
}

FORM_TO_LEMMA: dict[str, str] = {
    normalize_term(form): lemma
    for lemma, forms in _VERB_FORMS.items()
    for form in forms | {lemma}
}

TRANSITIVE_VERBS = {
    "comprar", "cocinar", "limpiar", "comer", "beber", "leer", "escribir", "conducir",
}


def verb_lemma(value: str, model_lemma: str | None = None) -> str | None:
    """Obtiene un lema verbal conocido a partir de la forma o del lema del modelo."""
    for candidate in (model_lemma, value):
        normalized = normalize_term(candidate or "")
        if normalized in FORM_TO_LEMMA:
            return FORM_TO_LEMMA[normalized]
    return None


def is_known_verb(value: str, model_lemma: str | None = None) -> bool:
    return verb_lemma(value, model_lemma) is not None


def is_probable_verb_record(record: dict) -> bool:
    """Evalúa un token serializado por POS, morfología o léxico de respaldo."""
    pos = normalize_term(str(record.get("pos", "")))
    tag = normalize_term(str(record.get("tag", "")))
    morph = normalize_term(str(record.get("morph", "")))
    return (
        pos in {"verb", "aux"}
        or tag.startswith("v")
        or "verbform=fin" in morph
        or "verbform=inf" in morph
        or is_known_verb(str(record.get("text", record.get("token", ""))), str(record.get("lemma", "")))
    )


def word_tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", text or "")
