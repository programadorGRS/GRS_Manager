from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import (BooleanField, DateField, Field, IntegerField, SelectField,
                     SelectMultipleField, StringField)
from wtforms.validators import Length, Optional

from src.extensions import database

from ..empresa_principal.empresa_principal import EmpresaPrincipal
from ..unidade.unidade import Unidade
from .conv_exames import ConvExames


class FormBuscarPedidoProcessamento(FlaskForm):
    opcoes = [("", "Selecione"), (1, "Sim"), (0, "Não")]
    cod_empresa_principal = SelectField(
        "Empresa Principal", choices=[], validators=[Optional()]
    )
    empresas_ativas = SelectField(
        "Empresas Ativas", choices=opcoes, validators=[Optional()]
    )
    id_empresa = SelectField(
        "Empresa", choices=[], validators=[Optional()], validate_choice=False
    )
    data_inicio = DateField("Inicio", validators=[Optional()])
    data_fim = DateField("Fim", validators=[Optional()])
    cod_solicitacao = IntegerField(
        "Cód Pedido de Processamento", validators=[Optional()]
    )
    resultado_importado = SelectField(
        "Importado", choices=opcoes, validators=[Optional()]
    )
    obs = StringField("Observação", validators=[Optional(), Length(0, 100)])

    def load_choices(self):
        self.cod_empresa_principal.choices = [("", "Selecione")] + [
            (i.cod, i.nome) for i in EmpresaPrincipal.query.all()
        ]
        return None

    def get_url_args(self, data: dict):
        DATE_FORMAT = "%Y-%m-%d"

        ignore_v = [None, ""]

        new_data = {}

        for key, value in data.items():
            if value in ignore_v:
                continue

            field: Field = getattr(self, key)
            match field.type:
                case "SelectField":
                    new_data[key] = int(value)
                case "DateField":
                    new_data[key] = datetime.strptime(value, DATE_FORMAT).date()
                case "IntegerField":
                    new_data[key] = int(value)
                case _:
                    new_data[key] = value

        return new_data


class FormGerarRelatorios(FlaskForm):
    unidades = SelectMultipleField("Unidades", validate_choice=False)
    status = SelectMultipleField("Status", validate_choice=False)
    a_vencer = SelectMultipleField("A vencer", validate_choice=False)
    gerar_ppt = BooleanField("Gerar Powerpoint", validators=[Optional()])

    def load_choices(self, id_empresa: int):
        unidades = (
            database.session.query(Unidade)  # type: ignore
            .filter(Unidade.id_empresa == id_empresa)
            .order_by(Unidade.nome_unidade)
            .all()
        )
        self.unidades.choices = [(i.id_unidade, i.nome_unidade) for i in unidades]

        self.status.choices = [
            (key, val) for key, val in ConvExames.STATUS_EXAMES.items()
        ]

        self.a_vencer.choices = [
            (key, val) for key, val in ConvExames.DIAS_VENCER_EXAMES.items()
        ]
        return None

    def get_request_form_data(self, data: dict):
        ignore_v = [None, ""]

        new_data = {}

        for key, value in data.items():
            if value in ignore_v:
                continue

            field: Field = getattr(self, key)
            match field.type:
                case "SelectMultipleField":
                    # NOTE: getlist é um metodo de Flask.request.form
                    new_data[key] = data.getlist(key, type=int)  # type: ignore
                case "BooleanField":
                    new_data[key] = bool(value)

        return new_data
