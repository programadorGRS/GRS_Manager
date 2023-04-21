from flask_wtf import FlaskForm
from wtforms import BooleanField, DateTimeField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class FormCriarStatus(FlaskForm):
    nome_status = StringField('Nome do Status', validators=[DataRequired(), Length(3, 100)])
    finaliza_processo = BooleanField('Finaliza Processo')
    
    data_inclusao = DateTimeField('Data Inclusão', validators=[Optional()])
    data_alteracao = DateTimeField('Data Alteração', validators=[Optional()])
    incluido_por = StringField('Incluído por', validators=[Optional()])
    alterado_por = StringField('Alterado por', validators=[Optional()])
    botao_salvar = SubmitField('Salvar')
