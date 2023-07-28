from flask import Flask
from werkzeug.exceptions import HTTPException

from src.api import routes
from src.api.routes_internas import internal_api
from src.main.central_avisos.routes import central_avisos
from src.main.conv_exames.routes import conv_exames
from src.main.empresa.routes import empresa
from src.main.empresa_socnet.routes import empresa_socnet
from src.main.error_handlers import error_handlers
from src.main.error_handlers.error_handlers import (error_404, http_exeptions,
                                                    internal_exceptions)
from src.main.exame import routes
from src.main.exames_realizados import routes
from src.main.grupo import routes
from src.main.home import routes
from src.main.importacao import routes
from src.main.licenca import routes
from src.main.log_acoes import routes
from src.main.login.routes import user_auth
from src.main.manual import routes
from src.main.pedido import routes
from src.main.pedido_socnet import routes
from src.main.prestador import routes
from src.main.relatorios_agendados import routes
from src.main.rtc.routes import rtc
from src.main.status import routes
from src.main.unidade import routes
from src.main.usuario import routes


def register_all_blueprints(app: Flask):
    app = __register_error_handlers(app=app)

    app.register_blueprint(central_avisos)
    app.register_blueprint(empresa)
    app.register_blueprint(empresa_socnet)
    app.register_blueprint(internal_api)
    app.register_blueprint(user_auth)
    app.register_blueprint(conv_exames)
    app.register_blueprint(rtc)
    return app


def __register_error_handlers(app: Flask):
    app.register_error_handler(404, error_404)
    app.register_error_handler(Exception, internal_exceptions)
    app.register_error_handler(HTTPException, http_exeptions)
    return app
