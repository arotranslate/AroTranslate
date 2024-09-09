import logging
from flask import Flask, jsonify, abort, request, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from services.translation_service import (translate_text, 
                                          convert_diacritics_from_orthography,
                                          )
from utils.text_processing import get_language_code
from utils.logger import configure_logging

configure_logging()

logger = logging.getLogger(__name__)

app = Flask(__name__)
if Config.TALISMAN:
    Talisman(app, force_https=True)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
limiter = Limiter(get_remote_address,
                  app=app,
                  default_limits=[Config.RATE_LIMIT],
                  storage_uri=f"memcached://{Config.MEMCACHED}",
                  )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/translate", methods=["POST"])
@limiter.limit("50 per minute")
def translate():
    data = request.get_json()
    if not data:
        abort(400, description="Invalid JSON")

    input_text = data.get("input_text", "").strip()
    input_language = data.get("input_language", "").strip()
    output_language = data.get("output_language", "").strip()
    if input_language == output_language:
        return jsonify({"translated_text": input_text, "translate_time": "0.0"})

    if not input_text or not input_language or not output_language:
        abort(400, description="Missing required fields")

    lang_from = get_language_code(input_language)
    lang_to = get_language_code(output_language)

    if not lang_from or not lang_to:
        abort(400, description="Invalid language selection.")

    try:
        translated_text, translate_time = translate_text(input_text, lang_from, lang_to)
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        abort(500, description="Translation failed")

    return jsonify(
        {
            "translated_text": translated_text,
            "translate_time": str(round(translate_time, 5)),
        }
    )



@app.route("/diacritics", methods=["POST"])
@limiter.limit("50 per minute")
def diacritics():
    data = request.get_json()
    if not data:
        abort(400, description="Invalid JSON")

    orthography = data.get("orthography", "").strip()
    text = data.get("text", "").strip()

    if not orthography or not text:
        abort(400, description="Invalid input.")

    try:
        converted_text = convert_diacritics_from_orthography(orthography, text)
    except Exception:
        abort(500, description="Diacritics conversion failed.")

    return jsonify({"text": converted_text})


if __name__ == "__main__":
    app.run(debug=Config.FLASK_DEBUG, port=Config.FLASK_PORT, host=Config.FLASK_HOST)
