import json
import os

from flask import Flask
from pytz import timezone

from .extensions import bcrypt, database, login_manager, mail, migrate

app = Flask(
    import_name=__name__,
    template_folder=os.path.join('main', 'templates'),
    static_folder=os.path.join('main', 'static')
)

# carregar configs universais
app.config.from_file("../configs/email.json", load=json.load)

dev = False
if dev:
    # using sqlite
    app.config.from_file("../configs/dev.json", load=json.load)
else:
    # using mysql
    app.config.from_file("../configs/prod.json", load=json.load)


login_manager.init_app(app)
database.init_app(app)
migrate.init_app(app=app, db=database)
mail.init_app(app)
bcrypt.init_app(app)


UPLOAD_FOLDER = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
DOWNLOAD_FOLDER = os.path.join(app.root_path, app.config['DOWNLOAD_FOLDER'])

TIMEZONE_SAO_PAULO = timezone('America/Sao_Paulo')

from src import _commandrefs, _modelrefs, _routerefs
