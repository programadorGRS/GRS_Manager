from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, SelectField, StringField
from wtforms.validators import Length, Optional


class FormBuscarPrestador(FlaskForm):
    opcoes = [("", "Selecione"), (1, "Sim"), (0, "Não")]

    cod_emp_princ = SelectField(
        "Empresa Principal", choices=[], validators=[Optional()]
    )
    id_prestador = IntegerField("Id", validators=[Optional()])
    cod_prestador = IntegerField("Código", validators=[Optional()])
    nome_prestador = StringField("Nome Prestador", validators=[Optional()])
    prestador_ativo = SelectField(
        "Prestador Ativo", choices=opcoes, validators=[Optional()]
    )


class FormPrestador(FlaskForm):
    emails = StringField("E-mails", validators=[Length(0, 500), Optional()])
    solicitar_asos = BooleanField("Solicitar ASOs")
