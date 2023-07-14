from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, SelectField, StringField
from wtforms.validators import Length, Optional

from src.utils import validate_email_fields


class FormBuscarEmpresa(FlaskForm):
    opcoes = [("", "Selecione"), (1, "Sim"), (0, "Não")]
    cod_empresa_principal = SelectField(
        "Empresa Principal", choices=[], validators=[Optional()]
    )
    id_empresa = IntegerField("Id", validators=[Optional()])
    cod_empresa = IntegerField("Código", validators=[Optional()])
    nome_empresa = StringField("Nome Empresa", validators=[Optional()])
    empresa_ativa = SelectField(
        "Empresa Ativa", choices=opcoes, validators=[Optional()]
    )


class FormEmpresa(FlaskForm):
    kws = {"placeholder": "E-mails"}

    # relatorios
    conv_exames = BooleanField("Conv. de Exames", validators=[Optional()])
    conv_exames_emails = StringField(
        "E-mails Convocação Exames",
        validators=[Optional(), Length(0, 500)],
        render_kw=kws,
    )

    exames_realizados = BooleanField("Exames Realizados", validators=[Optional()])
    exames_realizados_emails = StringField(
        "E-mails Exames Realizados",
        validators=[Optional(), Length(0, 500)],
        render_kw=kws,
    )

    absenteismo = BooleanField("Absenteísmo", validators=[Optional()])
    absenteismo_emails = StringField(
        "E-mails Absenteísmo", validators=[Optional(), Length(0, 500)], render_kw=kws
    )

    mandatos_cipa = BooleanField("Mandatos CIPA", validators=[Optional()])
    mandatos_cipa_emails = StringField(
        "E-mails Mandato CIPA", validators=[Optional(), Length(0, 500)], render_kw=kws
    )

    # carregamentos
    carregar_mandatos_cipa = BooleanField("Mandatos CIPA", validators=[Optional()])

    kws_dominio = {"placeholder": "exemplo.com.br"}
    dominios_email = StringField(
        "Dominio E-mail da Empresa",
        validators=[Optional(), Length(0, 100)],
        render_kw=kws_dominio,
    )

    # override Flaskform validate method to validate multiple fields
    def validate(self, *args, **kwargs):
        return validate_email_fields(
            form=self, field_name_pattern="_email", *args, **kwargs
        )
