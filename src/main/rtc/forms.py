from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (BooleanField, DateField, IntegerField, SelectField,
                     StringField)
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from ..empresa_principal.empresa_principal import EmpresaPrincipal
from ..tipo_exame.tipo_exame import TipoExame


class FormBuscarRTC(FlaskForm):
    data_inicio = DateField("Data Inicio", validators=[Optional()])
    data_fim = DateField("Data Fim", validators=[Optional()])
    seq_ficha = IntegerField("Seq. Ficha", validators=[Optional()])
    nome_funcionario = StringField(
        "Nome Funcionário", validators=[Optional(), Length(0, 255)]
    )

    # busca avancada
    cod_emp_princ = SelectField(
        "Empresa Principal", choices=[], validators=[Optional()]
    )
    id_empresa = SelectField(
        "Empresa", choices=[], validators=[Optional()], validate_choice=False
    )
    id_unidade = SelectField(
        "Unidade", choices=[], validators=[Optional()], validate_choice=False
    )
    id_prestador = SelectField(
        "Prestador", choices=[], validators=[Optional()], validate_choice=False
    )
    cod_tipo_exame = SelectField("Tipo Exame", choices=[], validators=[Optional()])

    def validate_data_inicio(self, data_inicio):
        if data_inicio.data and self.data_fim.data:
            if data_inicio.data > self.data_fim.data:
                raise ValidationError("Data Inicio deve ser menor do que Data Fim")

    def load_choices(self):
        self.cod_emp_princ.choices = [("", "Selecione")] + [
            (i.cod, i.nome) for i in EmpresaPrincipal.query.all()
        ]

        self.cod_tipo_exame.choices = [("", "Selecione")] + [
            (i.cod_tipo_exame, i.nome_tipo_exame)
            for i in TipoExame.query.order_by(TipoExame.nome_tipo_exame).all()
        ]
        return None


class FormGerarRTC(FlaskForm):
    tipo_sang = BooleanField("Incluir Tipo Sanguíneo", validators=[Optional()])
    gerar_qrcode = BooleanField("Incluir QR Code", validators=[Optional()])
    regras_vida = BooleanField("Regras pela Vida", validators=[Optional()])


class FormUploadCSV(FlaskForm):
    ENCODING = {1: "ISO-8859-1", 2: "UTF-8"}
    SEP = {1: ";", 2: ","}

    opc_encoding = [(k, v) for k, v in ENCODING.items()]
    opc_sep = [(k, v) for k, v in SEP.items()]

    opc_tabela = [("", "Selecione"), (1, "Cargos")]

    cod_emp_princ = SelectField(
        "Selecione a Empresa Principal", validators=[DataRequired()], choices=[]
    )

    tabela = SelectField(
        "Selecione a Tabela para Atualizar",
        choices=opc_tabela,
        validators=[DataRequired()],
    )

    file_encoding = SelectField(
        "Selecione a Codificação do CSV. \
        Se não tiver certeza, deixe na opção padrão",
        validators=[DataRequired()],
        choices=opc_encoding,
    )

    file_sep = SelectField(
        "Selecione o separador do CSV.", validators=[DataRequired()], choices=opc_sep
    )

    csv_file = FileField(
        "Selecione um arquivo CSV",
        validators=[
            FileRequired(),
            FileAllowed(["csv"], message="Apenas arquivos CSV"),
        ],
    )
