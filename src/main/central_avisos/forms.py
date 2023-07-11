from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, StringField
from wtforms.validators import DataRequired, Length, Optional

from src.extensions import database

from ..unidade.unidade import Unidade


class FormCentralUnidades(FlaskForm):
    kws = {"placeholder": "E-mails"}

    id_unidades = SelectMultipleField(
        "Unidades", choices=[], validators=[DataRequired()], coerce=int  # type: ignore
    )

    # relatorios
    conv_exames_emails = StringField(
        "E-mails Convocação Exames",
        validators=[Length(0, 500), Optional()],
        render_kw=kws,
    )

    exames_realizados_emails = StringField(
        "E-mails Exames Realizados",
        validators=[Length(0, 500), Optional()],
        render_kw=kws,
    )

    absenteismo_emails = StringField(
        "E-mails Absenteísmo", validators=[Length(0, 500), Optional()], render_kw=kws
    )

    mandatos_cipa_emails = StringField(
        "E-mails Mandato CIPA", validators=[Length(0, 500), Optional()], render_kw=kws
    )

    def load_choices(self, id_empresas: list[int]):
        query = (
            database.session.query(Unidade)
            .filter(Unidade.id_empresa.in_(id_empresas))
            .filter(Unidade.ativo == True)  # noqa
        )

        self.id_unidades.choices = [(un.id_unidade, un.nome_unidade) for un in query]

        return None
