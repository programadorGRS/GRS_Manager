from flask import jsonify, render_template
from werkzeug.exceptions import HTTPException

from src import app

# NOTE: since general error handlers have no Blueprint, their templates must \
# stay at the root template folder


def error_404(error):
    return (
        render_template(
            "error_handlers/erro.html",
            titulo_erro="Page not Found",
            descr_erro="Essa página não existe",
        ),
        404,
    )


def internal_exceptions(error):
    app.logger.error(error, exc_info=True)
    return (
        render_template(
            "error_handlers/erro.html",
            titulo_erro="Internal Server Error",
            descr_erro="Houve um erro inesperado no sistema",
        ),
        500,
    )


def http_exceptions(error):
    """Return JSON instead of HTML for HTTP errors."""
    return jsonify(error.name), error.code
