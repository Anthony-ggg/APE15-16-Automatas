"""Aplicación web para resolver de forma integrada las APE 15 y 16."""

from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from analyzers import corenlp_analyzer, spacy_analyzer
from config import Config
from services.classifier import classify_sentence, fallback_proposition_count
from services.comparison import build_comparison
from services.semantic_analyzer import analyze_semantics


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/health")
    def health():
        return jsonify(
            {
                "spacy": spacy_analyzer.health(),
                "corenlp": corenlp_analyzer.health(app.config["CORENLP_URL"]),
            }
        )

    @app.post("/analizar")
    def analizar():
        payload = request.get_json(silent=True) or {}
        text = payload.get("texto")
        if not isinstance(text, str):
            return jsonify({"error": "Debe enviar el campo texto como una cadena."}), 400

        text = text.strip()
        if not text:
            return jsonify({"error": "La oración no puede estar vacía."}), 400
        if len(text) > app.config["MAX_TEXT_LENGTH"]:
            return jsonify(
                {
                    "error": (
                        f"El texto supera el máximo de {app.config['MAX_TEXT_LENGTH']} caracteres."
                    )
                }
            ), 400

        classification = classify_sentence(text)
        spacy_result = spacy_analyzer.analizar(text)
        corenlp_result = corenlp_analyzer.analizar(
            text,
            app.config["CORENLP_URL"],
            app.config["CORENLP_TIMEOUT_SECONDS"],
        )
        comparison = build_comparison(spacy_result, corenlp_result)
        semantic_result = analyze_semantics(
            text, classification, spacy_result, corenlp_result
        )

        proposition_count = max(
            spacy_result.get("proposition_count", 0),
            corenlp_result.get("proposition_count", 0),
        ) or fallback_proposition_count(text)

        warnings: list[str] = []
        if not spacy_result.get("available"):
            warnings.append(spacy_result.get("error", "spaCy no está disponible."))
        if not corenlp_result.get("available"):
            warnings.append(corenlp_result.get("error", "CoreNLP no está disponible."))

        return jsonify(
            {
                "text": text,
                "classification": classification,
                "proposition_count": proposition_count,
                "spacy": spacy_result,
                "corenlp": corenlp_result,
                "comparison": comparison,
                "semantic": semantic_result,
                "warnings": warnings,
            }
        )

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Ruta no encontrada."}), 404

    @app.errorhandler(500)
    def internal_error(_error):
        return jsonify({"error": "Se produjo un error interno en el servidor."}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
