from flask import request
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (BooleanField, DateField, DateTimeField, IntegerField,
                     SelectField, StringField, SubmitField)
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from manager import database
from manager.forms import FormBuscarASO, FormCriarEmpresa, FormEditarPedido
from manager.models_socnet import EmpresaSOCNET


class FormBuscarPedidoSOCNET(FormBuscarASO):
    opcoes = [('', 'Selecione')]
    pesquisa_geral = BooleanField('Busca Geral', render_kw={'onchange': "CarregarOpcoesBuscaSOCNET('cod_empresa_principal', 'empresa', 'prestador', 'unidade', 'flexSwitch')"}) # flexSwitch
    cod_empresa_principal = SelectField('Empresa Principal', choices=[], validators=[DataRequired()], render_kw={'onchange': "CarregarOpcoesBuscaSOCNET('cod_empresa_principal', 'empresa', 'prestador', 'unidade', 'flexSwitch')"})
    empresa = SelectField('Empresa', choices=opcoes, validators=[Optional()], validate_choice=False)


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
            .filter(EmpresaSOCNET.cod_empresa_principal == self.cod_empresa_principal.data)
            .filter(EmpresaSOCNET.cod_empresa_referencia == self.cod_empresa_referencia.data)
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
            empresa_x.cod_empresa_principal != self.cod_empresa_principal.data or
            empresa_x.cod_empresa_referencia != self.cod_empresa_referencia.data
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