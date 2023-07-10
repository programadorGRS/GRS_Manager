from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, SelectField, StringField
from wtforms.validators import Length, Optional

from manager.models import EmpresaPrincipal


class FormBuscarContratos(FlaskForm):
    cod_empresa_principal = SelectField(
        'Empresa Principal',
        choices= [('', 'Selecione')] + [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()],
        validators=[Optional()],
        render_kw={'onchange': "carregarOpcoesEmpresa('cod_empresa_principal', 'id_empresa')"}
    )
    data_vencimento_inicio = DateField('Data Vencimento Inicio', validators=[Optional()])
    data_vencimento_fim = DateField('Data Vencimento Fim', validators=[Optional()])
    data_realizado_inicio = DateField('Data Realizado Inicio', validators=[Optional()])
    data_realizado_fim = DateField('Data Realizado Fim', validators=[Optional()])
    id_empresa = SelectField('Empresa', choices=[('', 'Selecione')], validators=[Optional()], validate_choice=False, render_kw={'onchange':"carregarOpcoesUnidade('cod_empresa_principal', 'id_empresa', 'id_unidade')"})
    id_unidade = SelectField('Unidade', choices=[('', 'Selecione'), (0, 'Vazio')], validators=[Optional()], validate_choice=False)
    cod_produto = IntegerField('Cód Produto', validators=[Optional()])
    nome_produto = StringField('Nome Produto', validators=[Optional()])
    situacao = StringField('Situacao', validators=[Optional(), Length(0, 100)])

