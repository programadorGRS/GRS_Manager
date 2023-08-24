from flask import Flask
from flask_limiter.errors import RateLimitExceeded
from werkzeug.exceptions import HTTPException

from src.api import routes
from src.api.routes_internas import internal_api
from src.main.central_avisos import central_avisos
from src.main.conv_exames import conv_exames
from src.main.empresa.routes import empresa
from src.main.empresa_socnet.routes import empresa_socnet
from src.main.error_handlers.error_handlers import (error_404, http_exceptions,
                                                    internal_exceptions,
                                                    rate_limit_exceptions)
from src.main.exame import exame_bp
from src.main.exames_realizados import routes
from src.main.grupo import routes
from src.main.home import routes
from src.main.importacao import routes
from src.main.licenca import absenteismo_bp
from src.main.log_acoes import routes
from src.main.login.routes import user_auth
from src.main.manual import routes
from src.main.pedido import routes
from src.main.pedido_socnet import routes
from src.main.prestador import routes
from src.main.relatorios_agendados import routes
from src.main.rtc.routes import rtc
from src.main.status import status_bp
from src.main.unidade import unidade
from src.main.usuario.routes import usuario_bp


def register_blueprints(app: Flask):
    """Registers all Blueprints"""
    app.register_blueprint(central_avisos)
    app.register_blueprint(empresa)
    app.register_blueprint(empresa_socnet)
    app.register_blueprint(internal_api)
    app.register_blueprint(user_auth)
    app.register_blueprint(conv_exames)
    app.register_blueprint(rtc)
    app.register_blueprint(unidade)
    app.register_blueprint(status_bp)
    app.register_blueprint(absenteismo_bp)
    app.register_blueprint(exame_bp)
    app.register_blueprint(usuario_bp)
    return app


def register_error_handlers(app: Flask):
    """Registers main error handlers"""
    app.register_error_handler(404, error_404)
    app.register_error_handler(Exception, internal_exceptions)
    app.register_error_handler(HTTPException, http_exceptions)
    app.register_error_handler(RateLimitExceeded, rate_limit_exceptions)
    return app
