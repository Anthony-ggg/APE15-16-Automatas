"""
corenlp_analyzer.py
Modulo de integracion con Stanford CoreNLP via HTTP API.
Extrae SVO (Sujeto-Verbo-Objeto), dependencias sintacticas,
arbol de parsing y clasificacion de oraciones.
"""

import requests
import re

CORENLP_URL = "http://localhost:9000"
PROPERTIES = {
    "annotators": "tokenize,ssplit,pos,lemma,depparse,ner",
    "outputFormat": "json",
    "timeout": "30000",
    "pipelineLanguage": "es",
    "tokenize.language": "es",
}

# Diccionario de conectores para clasificacion de oraciones
CONECTORES = {
    # Coordinadas
    "copulativas": ["y", "e", "ni"],
    "disyuntivas": ["o", "u"],
    "adversativas": ["pero", "sin embargo", "sino"],
    # Subordinadas
    "causales": ["porque", "ya que", "puesto que", "pues"],
    "condicionales": ["si"],
    "concesivas": ["aunque", "aun cuando", "si bien"],
    "temporales": ["mientras", "cuando", "antes de que", "despues de que"],
    "finales": ["para que", "a fin de que", "sin que"],
    "consecutivas": ["por lo tanto", "asi que", "de modo que", "por eso"],
}


def _clasificar_conector(texto_lower):
    """Detecta el conector presente en la oracion y retorna su tipo."""
    for tipo, conectores in CONECTORES.items():
        for conector in conectores:
            if conector in texto_lower:
                return tipo, conector
    return "simple", None


def clasificar_oracion(texto):
    """
    Clasifica la oracion segun su tipo sintactico.
    Retorna un diccionario con tipo, subtipo y conector detectado.
    """
    texto_lower = texto.lower().strip().rstrip(".")

    tipo, conector = _clasificar_conector(texto_lower)

    clasificacion = {
        "tipo": "Compuesta" if tipo != "simple" else "Simple",
        "subtipo": tipo.replace("s", "", 1) if tipo != "simple" else "Simple",
        "conector": conector if conector else "Ninguno",
    }

    return clasificacion


def _extraer_svo(sentencia):
    """
    Extrae Sujeto, Verbo Principal y Objeto Directo
    usando dependencias sintacticas con respaldo por POS tags y heuristica.
    """
    tokens_map = {}
    pos_map = {}
    ner_map = {}
    tokens_orden = []

    for tok in sentencia.get("tokens", []):
        idx = tok["index"]
        tokens_map[idx] = tok["word"]
        pos_map[idx] = tok.get("pos", "")
        ner_map[idx] = tok.get("ner", "O")
        tokens_orden.append(tok["word"])

    deps = sentencia.get("basicDependencies", [])

    sujeto = ""
    verbo = ""
    objeto = ""

    for dep in deps:
        rel = dep["dep"].lower()
        dependent_idx = dep["dependent"]

        if rel == "root":
            verbo = tokens_map.get(dependent_idx, "")
        elif rel in ("nsubj", "nsubj:pass", "csubj", "xsubj"):
            sujeto = tokens_map.get(dependent_idx, "")
        elif rel in ("obj", "dobj", "iobj", "pobj", "obl", "obl:arg", "obl:agent"):
            if not objeto:
                objeto = tokens_map.get(dependent_idx, "")

    # Si no se encontro sujeto/verbo por dependencias, usar heuristica POS
    if not sujeto or not verbo:
        sustantivos = []
        verbos = []

        for idx, pos in pos_map.items():
            word = tokens_map.get(idx, "")
            ner = ner_map.get(idx, "O")

            if (pos in ("NC", "NP", "NNC", "NNP", "NN", "NNS", "NNPS",
                         "Noun", "PROPN", "UNKNOWN", "Props") or
                ner in ("PERSON", "ORGANIZATION", "LOCATION")):
                sustantivos.append((idx, word))

            if (pos in ("VMN", "VMI", "VMS", "VSP", "VSG", "VMP",
                         "VB", "VBD", "VBG", "VBN", "VBP", "VBZ",
                         "VERB", "Aux", "Verb")):
                verbos.append((idx, word))

        if not verbo and verbos:
            verbo = verbos[0][1]

        if not sujeto and sustantivos:
            verbo_idx = -1
            for vidx, vword in verbos:
                if vword == verbo:
                    verbo_idx = vidx
                    break
            for sidx, sword in sustantivos:
                if verbo_idx == -1 or sidx < verbo_idx:
                    sujeto = sword
                    break
            if not sujeto:
                sujeto = sustantivos[0][1]

        if not objeto and sustantivos:
            verbo_idx = -1
            for vidx, vword in verbos:
                if vword == verbo:
                    verbo_idx = vidx
                    break
            for sidx, sword in sustantivos:
                if verbo_idx != -1 and sidx > verbo_idx and sword != sujeto:
                    objeto = sword
                    break

    return {
        "sujeto": sujeto if sujeto else "No detectado",
        "verbo": verbo if verbo else "No detectado",
        "objeto": objeto if objeto else "No detectado",
    }


def _formatear_arbol(sentencia):
    """Extrae el Parse Tree como string formateado."""
    tree = sentencia.get("parse", None)
    if tree:
        return tree
    return "Arbol no disponible (requiere annotator parse)"


def _extraer_sentiment(sentencia):
    """Extrae el sentiment de la oracion. Si no esta disponible, retorna N/A."""
    sentiment = sentencia.get("sentiment", None)
    if sentiment:
        return sentiment
    return "N/A (requiere annotator sentiment)"


def _extraer_ner(tokens):
    """Extrae entidades nombradas (NER) de los tokens."""
    entidades = []
    entidad_actual = ""
    tipo_actual = ""

    for tok in tokens:
        ner = tok.get("ner", "O")
        word = tok.get("word", "")

        if ner != "O":
            if ner == tipo_actual:
                entidad_actual += " " + word
            else:
                if entidad_actual:
                    entidades.append({"texto": entidad_actual, "tipo": tipo_actual})
                entidad_actual = word
                tipo_actual = ner
        else:
            if entidad_actual:
                entidades.append({"texto": entidad_actual, "tipo": tipo_actual})
                entidad_actual = ""
                tipo_actual = ""

    if entidad_actual:
        entidades.append({"texto": entidad_actual, "tipo": tipo_actual})

    return entidades


def analizar(texto):
    """
    Envio de texto a Stanford CoreNLP y procesamiento de respuesta.
    Retorna diccionario con tokens_pos, dependencias, arbol, svo y clasificacion.
    """
    try:
        response = requests.post(
            CORENLP_URL,
            params=PROPERTIES,
            data=texto.encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=30,
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        return {"error": "No se pudo conectar a Stanford CoreNLP en localhost:9000. Verifique que el servidor este activo."}
    except requests.exceptions.Timeout:
        return {"error": "Tiempo de espera agotado al conectar con CoreNLP."}
    except requests.exceptions.RequestException as e:
        return {"error": f"Error al conectar con CoreNLP: {str(e)}"}

    data = response.json()

    tokens_pos = []
    dependencias = []
    arbol = ""
    svo = {"sujeto": "No detectado", "verbo": "No detectado", "objeto": "No detectado"}
    sentiment = "Neutral"
    entidades = []

    for sentencia in data.get("sentences", []):
        # Tokens con POS tags y NER
        tokens_sentencia = sentencia.get("tokens", [])
        for tok in tokens_sentencia:
            tokens_pos.append({
                "token": tok["word"],
                "pos": tok["pos"],
                "ner": tok.get("ner", "O"),
            })

        # Dependencias sintacticas
        tokens_sent = sentencia.get("tokens", [])
        for dep in sentencia.get("basicDependencies", []):
            rel = dep["dep"]
            governor_idx = dep["governor"]
            dependent_idx = dep["dependent"]

            if rel.lower() == "root":
                governor_word = "ROOT"
            elif governor_idx > 0 and governor_idx <= len(tokens_sent):
                governor_word = tokens_sent[governor_idx - 1]["word"]
            else:
                governor_word = "ROOT"

            dependiente_idx = dep["dependent"]
            if dependiente_idx > 0 and dependiente_idx <= len(tokens_sent):
                dependiente_word = tokens_sent[dependiente_idx - 1]["word"]
            else:
                dependiente_word = str(dependiente_idx)

            dependencias.append({
                "relacion": rel,
                "gobernante": governor_word,
                "dependiente": dependiente_word,
            })

        # Arbol sintactico
        arbol = _formatear_arbol(sentencia)

        # SVO
        svo = _extraer_svo(sentencia)

        # Sentiment
        sentiment = _extraer_sentiment(sentencia)

        # NER
        entidades.extend(_extraer_ner(tokens_sentencia))

    clasificacion = clasificar_oracion(texto)

    return {
        "tokens_pos": tokens_pos,
        "dependencias": dependencias,
        "arbol": arbol,
        "svo": svo,
        "clasificacion": clasificacion,
        "sentiment": sentiment,
        "entidades": entidades,
    }
