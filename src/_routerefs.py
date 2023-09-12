from flask import Flask
from flask_limiter.errors import RateLimitExceeded
from werkzeug.exceptions import HTTPException

from src.api.routes import api_bp
from src.api.routes_internas import internal_api
from src.main.absenteismo.routes import absenteismo_bp
from src.main.central_avisos import central_avisos
from src.main.conv_exames import conv_exames
from src.main.empresa.routes import empresa
from src.main.empresa_socnet.routes import empresa_socnet
from src.main.error_handlers.error_handlers import (error_404, http_exceptions,
                                                    internal_exceptions,
                                                    rate_limit_exceptions)
from src.main.exame import exame_bp
from src.main.exames_realizados.routes import exames_realizados_bp
from src.main.grupo.routes import grupo_bp
from src.main.home.routes import home_bp
from src.main.importacao.routes import importacao_bp
from src.main.log_acoes.routes import log_acoes_bp
from src.main.login.routes import user_auth
from src.main.manual.routes import manual_bp
from src.main.pedido import routes
from src.main.pedido_socnet import routes
from src.main.prestador import prestador_bp
from src.main.relatorios_agendados.routes import rel_agendados_bp
from src.main.rtc.routes import rtc
from src.main.status import status_bp
from src.main.unidade import unidade
from src.main.usuario.routes import usuario_bp


def register_blueprints(app: Flask):
    """Registers all Blueprints"""
    BPS = [
        central_avisos,
        empresa,
        empresa_socnet,
        internal_api,
        user_auth,
        conv_exames,
        rtc,
        unidade,
        status_bp,
        absenteismo_bp,
        exame_bp,
        usuario_bp,
        exames_realizados_bp,
        prestador_bp,
        home_bp,
        log_acoes_bp,
        manual_bp,
        rel_agendados_bp,
        api_bp,
        grupo_bp,
        importacao_bp,
    ]

    for bp in BPS:
        app.register_blueprint(bp)
    return app


def register_error_handlers(app: Flask):
    """Registers main error handlers"""
    app.register_error_handler(404, error_404)
    app.register_error_handler(Exception, internal_exceptions)
    app.register_error_handler(HTTPException, http_exceptions)
    app.register_error_handler(RateLimitExceeded, rate_limit_exceptions)
    return app
