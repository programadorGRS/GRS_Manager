from flask import request
from flask_wtf import FlaskForm
from wtforms import (BooleanField, DateTimeField, IntegerField, SelectField,
                     StringField)
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from src import database
from src.utils import tratar_emails

from .empresa import Empresa


class FormBuscarEmpresa(FlaskForm):
    opcoes = [('', 'Selecione'), (1, 'Sim'), (0, 'Não')]
    cod_empresa_principal = SelectField('Empresa Principal', choices=[], validators=[Optional()])
    id = IntegerField('Id', validators=[Optional()])
    cod = IntegerField('Código', validators=[Optional()])
    nome = StringField('Razao Social', validators=[Optional()])
    ativo = SelectField('Ativo', choices=opcoes, validators=[Optional()])


class FormCriarEmpresa(FlaskForm):
    cod_empresa_principal = SelectField('Empresa Principal', choices=[], validators=[DataRequired()])
    cod_empresa = IntegerField('Código da empresa', validators=[DataRequired()])
    razao_social = StringField('Razão Social', validators=[DataRequired(), Length(3, 255)])
    razao_social_inicial = StringField('Razão Social Inicial (Opcional)', validators=[Length(0, 255), Optional()])
    nome_abrev = StringField('Nome Abreviado (Opcional)', validators=[Length(0, 255), Optional()])
    cnpj = StringField('CNPJ (Opcional)', validators=[Length(0, 100), Optional()])
    uf = StringField('UF (Opcional)', validators=[Length(0, 4), Optional()])
    emails = StringField('E-mails (Opcional)', validators=[Length(0, 500)])
    emails_conv_exames = StringField('E-mails Convocação Exames (Opcional)', validators=[Length(0, 500)])
    emails_absenteismo = StringField('E-mails Absenteísmo (Opcional)', validators=[Length(0, 500)])
    emails_exames_realizados = StringField('E-mails Exames Realizados (Opcional)', validators=[Length(0, 500)])
    ativo = BooleanField('Ativo')
    conv_exames = BooleanField('Conv. de Exames')
    
    data_inclusao = DateTimeField('Data Inclusão', validators=[Optional()])
    data_alteracao = DateTimeField('Data Alteração', validators=[Optional()])
    incluido_por = StringField('Incluído por', validators=[Optional()])
    alterado_por = StringField('Alterado por', validators=[Optional()])
    

    # validar se cod da empresa ja existe
    def validate_cod_empresa(self, cod_empresa):
        empresa = (
            database.session.query(Empresa)
            .filter(Empresa.cod_empresa_principal == self.cod_empresa_principal.data)
            .filter(Empresa.cod_empresa == cod_empresa.data)
            .first()
        )
        if empresa:
            raise ValidationError('Já existe uma empresa com esse código')

    def validate_emails(self, emails):
        for field_name, field in self._fields.items():
            if 'email' in field_name and field.type == 'StringField':
                try:
                    field.data = tratar_emails(field.data)
                except:
                    raise ValidationError('Erro ao validar Emails')


class FormEditarEmpresa(FormCriarEmpresa):
    
    # validar se ja tem outra com o mesmo codigo
    def validate_cod_empresa(self, cod_empresa):
        # pegar cod do empresa atraves do argumento na url
        empresa_x = Empresa.query.get(request.args.get('id_empresa'))
        # verificar se cod inputado e diferente do cod original da empresa
        if empresa_x.cod_empresa != cod_empresa.data:
            empresa_y = (
                database.session.query(Empresa)
                .filter(Empresa.cod_empresa_principal == empresa_x.cod_empresa_principal)
                .filter(Empresa.cod_empresa == cod_empresa.data)
                .first()
            )
            if empresa_y:
                raise ValidationError('Já existe uma empresa com esse código')
