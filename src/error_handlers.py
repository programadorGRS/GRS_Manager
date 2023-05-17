import traceback

from flask import render_template
from flask_login import current_user
from werkzeug.exceptions import HTTPException

from src import app


@app.errorhandler(404)
def error404(error):
    return render_template(
        'erro.html',
        title='GRS+Connect',
        cod_erro=404,
        titulo_erro='Essa página não existe'
    ), 404

@app.errorhandler(Exception)
def internalExceptions(erro):
    if current_user.is_authenticated:
        return render_template(
            'erro.html',
            title='GRS+Connect',
            cod_erro=500,
            titulo_erro=erro,
            texto_erro=traceback.format_exc()
        ), 500
    else:
        return {"message": "Internal Server Error"}, 500

@app.errorhandler(HTTPException)
def httpExeptions(error: HTTPException):
    """Return JSON instead of HTML for HTTP errors."""
    return {"message": error.name}, error.code
