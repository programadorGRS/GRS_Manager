import json
import os

from flask import Flask
from pytz import timezone

from .config import setup_loggers
from .extensions import bcrypt, database, login_manager, mail, migrate

app = Flask(
    import_name=__name__,
    template_folder=os.path.join("main", "templates"),
    static_folder=os.path.join("main", "static"),
)

# carregar configs universais
app.config.from_file("../configs/email.json", load=json.load)

env = app.config.get("ENV")
if env == "production":
    # using mysql
    app.config.from_file("../configs/prod.json", load=json.load)
else:
    # using sqlite
    app.config.from_file("../configs/dev.json", load=json.load)

app = setup_loggers(app=app)

login_manager.init_app(app)
database.init_app(app)
migrate.init_app(app=app, db=database)
mail.init_app(app)
bcrypt.init_app(app)


UPLOAD_FOLDER = os.path.join(app.root_path, app.config["UPLOAD_FOLDER"])
DOWNLOAD_FOLDER = os.path.join(app.root_path, app.config["DOWNLOAD_FOLDER"])

TIMEZONE_SAO_PAULO = timezone("America/Sao_Paulo")

from src import _modelrefs, _routerefs  # noqa
from src._commandrefs import add_all_commands  # noqa
from src._routerefs import register_blueprints, register_error_handlers  # noqa

app = register_blueprints(app=app)
app = register_error_handlers(app=app)
app = add_all_commands(app=app)
