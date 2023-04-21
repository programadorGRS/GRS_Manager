from flask import request
from flask_wtf import FlaskForm
from wtforms import (BooleanField, DateTimeField, IntegerField, SelectField,
                     StringField)
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from src import database

from ..empresa.forms import FormCriarEmpresa
from .empresa_socnet import EmpresaSOCNET


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

