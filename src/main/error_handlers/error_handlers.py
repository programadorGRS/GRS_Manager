import traceback

from flask import jsonify, render_template
from flask_login import current_user

# NOTE: since general error handlers have no Blueprint, their templates must \
# stay at the root template folder


def error_404(error):
    if current_user.is_authenticated:  # type: ignore
        return (
            render_template(
                "error_handlers/erro.html",
                cod_erro=404,
                titulo_erro="Essa página não existe",
            ),
            404,
        )
    else:
        return jsonify("Page Not Found"), 404


def internal_exceptions(error):
    if current_user.is_authenticated:  # type: ignore
        return (
            render_template(
                "error_handlers/erro.html",
                cod_erro=500,
                titulo_erro=error,
                texto_erro=traceback.format_exc(),
            ),
            500,
        )
    else:
        return jsonify("Internal Server Error"), 500


def http_exeptions(error):
    """Return JSON instead of HTML for HTTP errors."""
    return jsonify(error.name), error.code
