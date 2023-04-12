from flask import request
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (BooleanField, DateField, DateTimeField, IntegerField,
                     SelectField, StringField, SubmitField)
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from src import database
from src.forms import FormCriarEmpresa
from src.main.pedido.forms import FormEditarPedido

from .main.empresa_socnet.empresa_socnet import EmpresaSOCNET


class FormBuscarASOSOCNET(FlaskForm):
    opcoes = [('', 'Selecione')]
    pesquisa_geral = BooleanField('Busca Geral', render_kw={'onchange': "CarregarOpcoesBuscaSOCNET('cod_empresa_principal', 'id_empresa', 'id_prestador', 'flexSwitch')"}) # flexSwitch
    cod_empresa_principal = SelectField('Empresa Principal', choices=[], validators=[Optional()], render_kw={'onchange': "CarregarOpcoesBuscaSOCNET('cod_empresa_principal', 'id_empresa', 'id_prestador', 'flexSwitch')"})
    id_empresa = SelectField('Empresa', choices=opcoes, validators=[Optional()], validate_choice=False)
    id_prestador = SelectField('Prestador', choices=opcoes, validators=[Optional()], validate_choice=False)
    data_inicio = DateField('Inicio', validators=[Optional()])
    data_fim = DateField('Fim', validators=[Optional()])
    nome_funcionario = StringField('Nome Funcionário', validators=[Optional(), Length(0, 255)])
    seq_ficha = IntegerField('Seq. Ficha', validators=[Optional()])
    obs = StringField('Observação', validators=[Optional(), Length(0, 100)])
    id_status = SelectField('Status ASO', choices=[], validators=[Optional()])
    id_status_rac = SelectField('Status RAC', choices=[], validators=[Optional()])
    
    def validate_data_inicio(self, data_inicio):
        if data_inicio.data and self.data_fim.data:
            if data_inicio.data > self.data_fim.data:
                raise ValidationError('Inicio deve ser menor do que Fim')


class FormCriarEmpresaSOCNET(FlaskForm):
    cod_empresa_principal = SelectField('Empresa Principal Base', choices=[], validators=[DataRequired()])
    cod_empresa_referencia = SelectField('Empresa Principal Referência', choices=[], validators=[DataRequired()])
    cod_empresa = IntegerField('Código da empresa', validators=[DataRequired()])
    nome_empresa = StringField('Nome Empresa', validators=[DataRequired(), Length(3, 255)])
    emails = StringField('E-mails (Opcional)', validators=[Length(0, 500), Optional()])
    ativo = BooleanField('Ativo')

    data_inclusao = DateTimeField('Data Inclusão', validators=[Optional()])
    data_alteracao = DateTimeField('Data Alteração', validators=[Optional()])
    incluido_por = StringField('Incluído por', validators=[Optional()])
    alterado_por = StringField('Alterado por', validators=[Optional()])

    # validar se cod da empresa ja existe
    def validate_cod_empresa(self, cod_empresa):
        empresa = (
            database.session.query(EmpresaSOCNET)
            .filter(EmpresaSOCNET.cod_empresa_principal == int(self.cod_empresa_principal.data))
            .filter(EmpresaSOCNET.cod_empresa_referencia == int(self.cod_empresa_referencia.data))
            .filter(EmpresaSOCNET.cod_empresa == cod_empresa.data)
            .first()
        )
        if empresa:
            raise ValidationError('Já existe uma empresa SOCNET com esse código')
    
    def validate_emails(self, emails):
        FormCriarEmpresa.validate_emails(self, emails)


class FormEditarEmpresaSOCNET(FormCriarEmpresaSOCNET):

    # validar se ja tem outra com o mesmo codigo
    def validate_cod_empresa(self, cod_empresa):
        # pegar cod do empresa atraves do argumento na url
        empresa_x = EmpresaSOCNET.query.get(request.args.get('id_empresa', type=int))
        # verificar se cod inputado e diferente do cod original da empresa
        if (
            empresa_x.cod_empresa != cod_empresa.data or
            empresa_x.cod_empresa_principal != int(self.cod_empresa_principal.data) or
            empresa_x.cod_empresa_referencia != int(self.cod_empresa_referencia.data)
        ):
            empresa_y = (
                database.session.query(EmpresaSOCNET)
                .filter(EmpresaSOCNET.cod_empresa_principal == self.cod_empresa_principal.data)
                .filter(EmpresaSOCNET.cod_empresa_referencia == self.cod_empresa_referencia.data)
                .filter(EmpresaSOCNET.cod_empresa == cod_empresa.data)
                .first()
            )
            if empresa_y:
                raise ValidationError('Já existe uma empresa SOCNET com esse código')


class FormUpload(FlaskForm):
    csv = FileField(
        'Escolher arquivo',
        validators=[
            FileRequired(),
            FileAllowed(['csv'], message='Apenas arquivos CSV')
        ]
    )
    btn_upload = SubmitField('Upload')


class FormCarregarPedidosSOCNET(FlaskForm):
    arquivos = SelectField('Arquivos', choices=[], validators=[DataRequired()])
    btn_carregar = SubmitField('Carregar')


class FormEditarPedidoSOCNET(FormEditarPedido):
    unidade = SelectField('Unidade', choices=[], validators=[Optional()], validate_choice=False)
    prazo = IntegerField('Prazo Liberação (Dias úteis)', validators=[Optional()])
    prev_liberacao = DateField('Previsão Liberação', validators=[Optional()])