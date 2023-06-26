from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms.validators import Optional


class FormGerarRTC(FlaskForm):
    tipo_sang = BooleanField('Incluir Tipo Sanguíneo', validators=[Optional()])

