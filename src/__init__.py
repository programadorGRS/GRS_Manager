import json
import os

from flask import Flask
from pytz import timezone

from .extensions import bcrypt, database, login_manager, mail

app = Flask(__name__)

# carregar configs universais
app.config.from_file("../configs/email.json", load=json.load)

dev = True
if dev:
    # using sqlite
    app.config.from_file("../configs/dev.json", load=json.load)
else:
    # using mysql
    app.config.from_file("../configs/prod.json", load=json.load)


login_manager.init_app(app)
database.init_app(app)
mail.init_app(app)
bcrypt.init_app(app)


UPLOAD_FOLDER = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
DOWNLOAD_FOLDER = os.path.join(app.root_path, app.config['DOWNLOAD_FOLDER'])

TIMEZONE_SAO_PAULO = timezone('America/Sao_Paulo')


from src import (routes, routes_api, routes_api_internas, routes_soc,
                     routes_socnet)
from .modules import routes
from .modules.absenteismo import routes
from .modules.conv_exames import routes
from .modules.exames_realizados import routes
from .modules.RTC import routes

