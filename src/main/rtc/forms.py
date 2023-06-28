from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import BooleanField, SelectField
from wtforms.validators import DataRequired, Optional


class FormGerarRTC(FlaskForm):
    tipo_sang = BooleanField('Incluir Tipo Sanguíneo', validators=[Optional()])


class FormUploadCSV(FlaskForm):
    ENCODING = {1: 'ISO-8859-1', 2: 'UTF-8'}
    SEP = {1: ';', 2: ','}

    opc_encoding = [(k, v) for k, v in ENCODING.items()]
    opc_sep = [(k, v) for k, v in SEP.items()]

    opc_tabela = [
        ('', 'Selecione'),
        (1, 'Cargos')
    ]

    cod_emp_princ = SelectField(
        'Selecione a Empresa Principal',
        validators=[DataRequired()],
        choices=[]
    )

    tabela = SelectField(
        'Selecione a Tabela para Atualizar',
        choices=opc_tabela,
        validators=[DataRequired()]
    )

    file_encoding = SelectField(
        'Selecione a Codificação do CSV. \
        Se não tiver certeza, deixe na opção padrão',
        validators=[DataRequired()],
        choices=opc_encoding
    )

    file_sep = SelectField(
        'Selecione o separador do CSV.',
        validators=[DataRequired()],
        choices=opc_sep
    )

    csv_file = FileField(
        'Selecione um arquivo CSV',
        validators=[
            FileRequired(),
            FileAllowed(['csv'], message='Apenas arquivos CSV')
        ]
    )

