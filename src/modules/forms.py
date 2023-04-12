from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import FileField, SelectField, SubmitField, BooleanField
from wtforms.validators import DataRequired


class FormConfigRelatoriosAgendados(FlaskForm):
    tabela = SelectField(
        'Tabela para Atualizar',
        choices=[
            ('', 'Selecione'),
            (1, 'Empresas'),
            (2, 'Unidades')
        ],
        validators=[DataRequired()]
    )
    celulas_null = BooleanField(
        'Excluir informações (excluir dados no banco de dados onde a celula no CSV estiver em branco)'
    )
    csv = FileField(
        'Escolher arquivo',
        validators=[
            FileRequired(),
            FileAllowed(['csv'], message='Apenas arquivos CSV')
        ]
    )
    btn_upload = SubmitField('Upload')

