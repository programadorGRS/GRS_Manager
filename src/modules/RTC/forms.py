from flask_wtf import FlaskForm
from wtforms  import SubmitField


class FormGerarRTC(FlaskForm):
    btn = SubmitField('Gerar RACs')

