from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length


class FormLogin(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(3, 50)])
    senha = PasswordField('Senha', validators=[DataRequired(), Length(6, 50)])
    botao_login = SubmitField('Login')


class FormOTP(FlaskForm):
    otp = StringField('Chave de acesso', validators=[DataRequired(), Length(3, 50)])
    botao_login = SubmitField('Login')
