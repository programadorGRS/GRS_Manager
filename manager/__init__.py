import json
import os

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from pytz import timezone


app = Flask(__name__)

# carregar configs universais
app.config.from_file("../configs/email.json", load=json.load)

dev = False
if dev:
    # using sqlite
    app.config.from_file("../configs/dev.json", load=json.load)
else:
    # using mysql
    app.config.from_file("../configs/prod.json", load=json.load)


login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.refresh_view = 'refresh_login'
login_manager.login_message = 'Faça login para acessar'
login_manager.needs_refresh_message = 'Confirme suas credenciais para acessar'
login_manager.needs_refresh_message_category = 'alert-info'
login_manager.login_message_category = 'alert-info'


bcrypt = Bcrypt(app)
database = SQLAlchemy(app)
mail = Mail(app)


UPLOAD_FOLDER = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'])
DOWNLOAD_FOLDER = os.path.join(app.root_path, app.config['DOWNLOAD_FOLDER'])

TIMEZONE_SAO_PAULO = timezone('America/Sao_Paulo')


from manager import (routes, routes_api, routes_api_internas, routes_soc,
                     routes_socnet)
from manager.modules import routes
from manager.modules.conv_exames import routes
from manager.modules.exames_realizados import routes
from manager.modules.absenteismo import routes
from manager.modules.RTC import routes
