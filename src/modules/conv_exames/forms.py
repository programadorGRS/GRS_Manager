from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, SubmitField, DateField, StringField, SelectMultipleField
from wtforms.validators import DataRequired, Optional, Length


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
    cod_empresa_principal = SelectField(
        'Empresa Principal',
        choices=[],
        validators=[Optional()],
        render_kw={'onchange': "carregarOpcoesEmpresa('cod_empresa_principal', 'id_empresa')"}
    )
    id_empresa = SelectField('Empresa (Opcional)', choices=[('', 'Selecione')], validators=[Optional()], validate_choice=False)
    data_inicio = DateField('Inicio', validators=[Optional()])
    data_fim = DateField('Fim', validators=[Optional()])
    cod_solicitacao = IntegerField('Cód Pedido de Processamento (Opcional)', validators=[Optional()])
    resultado_importado = SelectField('Importado', choices=opcoes, validators=[Optional()])
    obs = StringField('Observação', validators=[Optional(), Length(0, 100)])


class FormGerarRelatorios(FlaskForm):
    filtro_unidades = SelectMultipleField('Unidades', choices=[], validators=[Optional()], render_kw={'data-actions-box':"true"})
    filtro_status = SelectMultipleField('Status', choices=[], validators=[Optional()], render_kw={'data-actions-box':"true"})
    filtro_a_vencer = SelectMultipleField('A vencer', choices=[], validators=[Optional()], render_kw={'data-actions-box':"true"})

