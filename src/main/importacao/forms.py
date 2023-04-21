from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import FileField, SelectField, SubmitField
from wtforms.validators import DataRequired


class FormImportarDados(FlaskForm):
    opcoes_tabela = [
        ('', 'Selecione'),
        (1, 'Empresas'),
        (2, 'Unidades'),
        (3, 'Exames')
    ]

    tabela = SelectField('Tabela para Atualizar', choices=opcoes_tabela, validators=[DataRequired()])
    csv = FileField(
        'Escolher arquivo',
        validators=[
            FileRequired(),
            FileAllowed(['csv'], message='Apenas arquivos CSV')
        ]
    )
    btn_upload = SubmitField('Upload')
