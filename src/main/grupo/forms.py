from flask_wtf import FlaskForm
from wtforms import (DateTimeField, SelectMultipleField, StringField,
                     SubmitField)
from wtforms.validators import DataRequired, Length, Optional


class FormCriarGrupo(FlaskForm):
    nome_grupo = StringField('Nome do Grupo', validators=[DataRequired(), Length(3, 255)])
    
    data_inclusao = DateTimeField('Data Inclusão', validators=[Optional()])
    data_alteracao = DateTimeField('Data Alteração', validators=[Optional()])
    incluido_por = StringField('Incluído por', validators=[Optional()])
    alterado_por = StringField('Alterado por', validators=[Optional()])
    
    botao_salvar = SubmitField('Salvar')


class FormGrupoPrestadores(FlaskForm):
    select = SelectMultipleField(label='Select', choices=[], validate_choice=False, id='dualListBox')
    botao_salvar = SubmitField('Salvar')

