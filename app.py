"""
app.py
Servidor Flask para la Practica 16 - CoreNLP vs spaCy.
Rutas:
  GET  /           -> Interfaz web
  POST /analizar   -> Analisis NLP comparativo
"""

from flask import Flask, render_template, request, jsonify
import corenlp_analyzer
import spacy_analyzer

app = Flask(__name__)


@app.route("/")
def index():
    """Renderiza la pagina principal."""
    return render_template("index.html")


@app.route("/analizar", methods=["POST"])
def analizar():
    """
    Endpoint de analisis NLP.
    Recibe JSON {"texto": "..."} y retorna resultados de CoreNLP y spaCy.
    """
    data = request.get_json(silent=True)
    if not data or "texto" not in data:
        return jsonify({"error": "Se requiere el campo 'texto' en el body JSON."}), 400

    texto = data["texto"].strip()
    if not texto:
        return jsonify({"error": "El campo 'texto' no puede estar vacio."}), 400

    # Analisis con Stanford CoreNLP
    resultado_corenlp = corenlp_analyzer.analizar(texto)

    # Analisis con spaCy
    resultado_spacy = spacy_analyzer.analizar(texto)

    return jsonify({
        "texto": texto,
        "corenlp": resultado_corenlp,
        "spacy": resultado_spacy,
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
