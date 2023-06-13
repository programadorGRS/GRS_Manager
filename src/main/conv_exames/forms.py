from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import (BooleanField, DateField, Field, IntegerField, SelectField,
                     SelectMultipleField, StringField, SubmitField, TextAreaField)
from wtforms.validators import DataRequired, Length, Optional
from ..empresa_principal.empresa_principal import EmpresaPrincipal
from ..unidade.unidade import Unidade

from src.extensions import database


class FormBuscarConvEXames(FlaskForm):
    cod_empresa_principal = SelectField(
        'Empresa Principal',
        choices=[],
        validators=[DataRequired()],
        render_kw={'onchange': "carregarOpcoesEmpresa('cod_empresa_principal', 'id_empresa')"}
    )
    id_empresa = SelectField('Empresa (Opcional)', choices=[('', 'Selecione')], validators=[Optional()], validate_choice=False)


class FormAtivarConvExames(FlaskForm):
    opcoes = [('', 'Selecione'), (1, 'Sim'), (0, 'Não')]
    conv_exames = SelectField('Realizar Convocação de Exames', choices=opcoes, validators=[DataRequired()])


class FormConfigurarsConvExames(FlaskForm):
    opcoes = [(0, 'Selecione'), (1, 'Sim'), (2, 'Não')]
    convocar_clinico = SelectField('Convocar clínico (Opcional)', choices=opcoes, validators=[Optional()], coerce=int)
    exames_pendentes = SelectField('Exames pendentes (Opcional)', choices=opcoes, validators=[Optional()], coerce=int)
    conv_pendentes_pcmso = SelectField('Convocar pendentes PCMSO (Opcional)', choices=opcoes, validators=[Optional()], coerce=int)
    nunca_realizados = SelectField(
        'Nunca realizados (Opcional)',
        choices=[
            (0, 'Selecione'),
            (1, 'Nenhum'),
            (2, "Nunca realizados"),
            (3, "Periódicos nunca realizados")
        ],
        validate_choice=[Optional()],
        coerce=int
    )

    selecao = SelectField(
        'Seleção (Obrigatório)',
        choices=[
            (1, "1 - Exames não realizados do período + exames em atraso (meses anteriores)"),
            (2, "2 - Exames do período + exames em atraso (meses anteriores)")
        ],
        validate_choice=[DataRequired()],
        coerce=int

    )

    botao_salvar = SubmitField('Salvar')


class FormBuscarPedidoProcessamento(FlaskForm):
    opcoes = [('', 'Selecione'), (1, 'Sim'), (0, 'Não')]
    cod_empresa_principal = SelectField('Empresa Principal', choices=[], validators=[Optional()])
    empresas_ativas = SelectField('Empresas Ativas', choices=opcoes, validators=[Optional()])
    id_empresa = SelectField('Empresa', choices=[], validators=[Optional()], validate_choice=False)
    data_inicio = DateField('Inicio', validators=[Optional()])
    data_fim = DateField('Fim', validators=[Optional()])
    cod_solicitacao = IntegerField('Cód Pedido de Processamento', validators=[Optional()])
    resultado_importado = SelectField('Importado', choices=opcoes, validators=[Optional()])
    obs = StringField('Observação', validators=[Optional(), Length(0, 100)])

    def load_choices(self):
        self.cod_empresa_principal.choices = (
            [('', 'Selecione')] +
            [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
        )
        return None

    def get_url_args(self, data: dict):
        DATE_FORMAT = '%Y-%m-%d'

        ignore_v = [None, '']

        new_data = {}

        for key, value in data.items():
            if value in ignore_v:
                continue

            field: Field = getattr(self, key)
            match field.type:
                case 'SelectField':
                    new_data[key] = int(value)
                case 'DateField':
                    new_data[key] = datetime.strptime(value, DATE_FORMAT).date()
                case 'IntegerField':
                    new_data[key] = int(value)
                case _:
                    new_data[key] = value

        return new_data


class FormGerarRelatorios(FlaskForm):
    filtro_unidades = SelectMultipleField('Unidades', choices=[], validators=[Optional()], render_kw={'data-actions-box':"true"})
    filtro_status = SelectMultipleField('Status', choices=[], validators=[Optional()], render_kw={'data-actions-box':"true"})
    filtro_a_vencer = SelectMultipleField('A vencer', choices=[], validators=[Optional()], render_kw={'data-actions-box':"true"})

