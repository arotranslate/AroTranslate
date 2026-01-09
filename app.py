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
from services.db_repository import get_db_repository
from models import Annotation
from utils.text_processing import get_language_code
from utils.logger import configure_logging

configure_logging()

logger = logging.getLogger(__name__)

try:
    db_repo = get_db_repository()
except Exception as e:
    logger.error(f"Failed to initialize MongoDB repository: {e}")
    logger.warning("Application will continue without database functionality")

app = Flask(__name__)
if Config.TALISMAN:
    logger.info("Using Talisman...")
    Talisman(app, force_https=True)

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
logger.info(f'{Config.STORAGE_URI}  {Config.RATE_LIMIT}')

limiter = Limiter(get_remote_address,
                app=app,
                default_limits=[Config.RATE_LIMIT],
                storage_uri=Config.STORAGE_URI,
                )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    health_status = {
        "status": "healthy",
        "services": {
            "api": "up"
        }
    }

    try:
        db_repo.client.admin.command('ping')
        health_status["services"]["db"] = "up"
    except Exception as e:
        health_status["services"]["db"] = "down"
        health_status["status"] = "degraded"
        logger.warning(f"MongoDB health check failed: {e}")

    status_code = 200 if health_status["status"] == "healthy" else 503
    return jsonify(health_status), status_code


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/admin")
def admin_dashboard():
    return render_template("admin_dashboard.html")


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


@app.route("/annotations", methods=["GET"])
@limiter.limit("50 per minute")
def get_annotations():
    try:
        limit = request.args.get("limit", default=100, type=int)
        offset = request.args.get("offset", default=0, type=int)

        if limit < 1 or limit > 1000:
            abort(400, description="Limit must be between 1 and 1000")

        if offset < 0:
            abort(400, description="Offset must be non-negative")

        annotations = db_repo.get_all_annotations(limit=limit, skip=offset)

        for annotation in annotations:
            annotation["_id"] = str(annotation["_id"])

        return jsonify({
            "annotations": annotations,
            "limit": limit,
            "offset": offset,
            "returned_count": len(annotations)
        })
    except Exception as e:
        logger.error(f"Failed to retrieve annotations: {e}")
        abort(500, description="Failed to retrieve annotations")


@app.route("/annotations/<annotation_id>", methods=["GET"])
@limiter.limit("50 per minute")
def get_annotation_by_id(annotation_id):
    try:
        annotation = db_repo.get_annotation_by_id(annotation_id)

        if annotation is None:
            abort(404, description="Annotation not found")

        annotation["_id"] = str(annotation["_id"])

        return jsonify(annotation)
    except Exception as e:
        logger.error(f"Failed to retrieve annotation {annotation_id}: {e}")
        abort(500, description="Failed to retrieve annotation")


@app.route("/annotations/<annotation_id>", methods=["PATCH"])
@limiter.limit("50 per minute")
def update_annotation(annotation_id):
    data = request.get_json()
    if not data:
        abort(400, description="Invalid JSON")

    private_id = data.get("private_id", "").strip()
    if not private_id:
        abort(400, description="Missing private_id")

    original_text = data.get("original_text")
    translated_text = data.get("translated_text")
    annotations_data = data.get("annotations")

    annotations = None
    if annotations_data is not None:
        if not isinstance(annotations_data, list):
            abort(400, description="Annotations must be a list")

        try:
            annotations = [
                Annotation(
                    start=ann["start"],
                    end=ann["end"],
                    level=ann["level"]
                )
                for ann in annotations_data
            ]
        except (KeyError, TypeError) as e:
            logger.error(f"Invalid annotation format: {e}")
            abort(400, description="Invalid annotation format. Each annotation must have start, end, and level")
        except ValueError as e:
            logger.error(f"Invalid annotation values: {e}")
            abort(400, description=str(e))

    try:
        result = db_repo.update_annotation(
            document_id=annotation_id,
            private_id=private_id,
            original_text=original_text,
            translated_text=translated_text,
            annotations=annotations
        )

        if not result["matched"]:
            abort(404, description="Annotation not found or private_id does not match")

        if not result["modified"]:
            return jsonify({
                "status": "no_changes",
                "message": "No fields were modified"
            }), 200

        return jsonify({
            "status": "success",
            "message": "Annotation updated successfully"
        }), 200

    except Exception as e:
        logger.error(f"Failed to update annotation: {e}")
        abort(500, description="Failed to update annotation")


@app.route("/annotations", methods=["POST"])
@limiter.limit("50 per minute")
def create_annotation():
    data = request.get_json()
    if not data:
        abort(400, description="Invalid JSON")

    original_text = data.get("original_text", "").strip()
    translated_text = data.get("translated_text", "").strip()
    annotations_data = data.get("annotations", [])

    if not original_text or not translated_text:
        abort(400, description="Missing original_text or translated_text")

    if not isinstance(annotations_data, list):
        abort(400, description="Annotations must be a list")

    try:
        annotations = [
            Annotation(
                start=ann["start"],
                end=ann["end"],
                level=ann["level"]
            )
            for ann in annotations_data
        ]
    except (KeyError, TypeError) as e:
        logger.error(f"Invalid annotation format: {e}")
        abort(400, description="Invalid annotation format. Each annotation must have start, end, and level")
    except ValueError as e:
        logger.error(f"Invalid annotation values: {e}")
        abort(400, description=str(e))

    try:
        result = db_repo.insert_annotation(
            original_text=original_text,
            translated_text=translated_text,
            annotations=annotations
        )
        return jsonify({
            "id": result["id"],
            "private_id": result["private_id"],
            "status": "success",
            "annotation_count": len(annotations)
        }), 201
    except Exception as e:
        logger.error(f"Failed to save annotation: {e}")
        abort(500, description="Failed to save annotation")


if __name__ == "__main__":
    app.run()
