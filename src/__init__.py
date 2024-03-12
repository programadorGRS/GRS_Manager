import json
import os

from flask import Flask
from pytz import timezone
from werkzeug.middleware.proxy_fix import ProxyFix

from .extensions import initialize_extensions, database
from .loggers import setup_loggers

app = Flask(
    import_name=__name__,
    template_folder=os.path.join("main", "templates"),
    static_folder=os.path.join("main", "static"),
)

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

# carregar configs universais
try:
    app.config.from_file("../configs/email.json", load=json.load)
except:
    app.config.from_file("..\configs\email.json", load=json.load)

env = app.config.get("ENV")
if env == "production":
    # using mysql    
    try:
        app.config.from_file("../configs/prod.json", load=json.load)
    except:
        app.config.from_file("..\configs\prod.json", load=json.load) 
    #app.config.from_file("../configs/hml.json", load=json.load) #Windows
else:
    # using sqlite
    app.config.from_file("../configs/dev.json", load=json.load)

app = setup_loggers(app=app)

app = initialize_extensions(app=app)

database = database

UPLOAD_FOLDER = os.path.join(app.root_path, app.config["UPLOAD_FOLDER"])
DOWNLOAD_FOLDER = os.path.join(app.root_path, app.config["DOWNLOAD_FOLDER"])

TIMEZONE_SAO_PAULO = timezone("America/Sao_Paulo")

from src import _modelrefs, _routerefs  # noqa
from src._commandrefs import add_all_commands  # noqa
from src._routerefs import register_blueprints, register_error_handlers  # noqa

app = register_blueprints(app=app)
app = register_error_handlers(app=app)
app = add_all_commands(app=app)
