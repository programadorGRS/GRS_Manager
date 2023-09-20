from flask import Flask
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

login_manager = LoginManager()

login_manager.login_view = "user_auth.login"  # type: ignore
login_manager.refresh_view = "user_auth.refresh_login"  # type: ignore
login_manager.login_message = "Faça login para acessar"
login_manager.needs_refresh_message = "Confirme suas credenciais para acessar"
login_manager.needs_refresh_message_category = "alert-info"
login_manager.login_message_category = "alert-info"


bcrypt = Bcrypt()
database = SQLAlchemy()
migrate = Migrate()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)


@login_manager.user_loader
def load_usuario(id_cookie):
    from .main.usuario.usuario import Usuario
    return Usuario.query.filter_by(id_cookie=id_cookie).first()


def initialize_extensions(app: Flask):
    EXTENSIONS = (
        bcrypt,
        database,
        mail,
        login_manager,
        limiter,
    )

    for ex in EXTENSIONS:
        ex.init_app(app=app)

    migrate.init_app(app=app, db=database)

    return app
