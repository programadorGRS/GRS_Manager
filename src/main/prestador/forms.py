from flask import request
from flask_wtf import FlaskForm
from wtforms import (BooleanField, DateTimeField, IntegerField, SelectField,
                     StringField, SubmitField)
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from src import database

from ..empresa.forms import FormBuscarEmpresa, FormCriarEmpresa
from .prestador import Prestador


class FormBuscarPrestador(FormBuscarEmpresa):
    nome = StringField('Nome', validators=[Optional()])


class FormCriarPrestador(FlaskForm):
    cod_empresa_principal = SelectField(
        'Empresa Principal',
        choices=[],
        validators=[DataRequired()],
        render_kw={'onchange': "carregarOpcoesEmpresa('cod_empresa_principal', 'id_empresa')"}
    )
    cod_prestador = IntegerField('Codigo do Prestador', validators=[DataRequired()])
    nome_prestador = StringField('Nome do Prestador', validators=[DataRequired(), Length(3, 255)])
    cnpj = StringField('CNPJ (Opcional)', validators=[Length(0, 100), Optional()])
    uf = StringField('UF (Opcional)', validators=[Length(0, 4), Optional()])
    razao_social = StringField('Razão Social (Opcional)', validators=[Length(0, 100), Optional()])
    emails = StringField('E-mails (Opcional)', validators=[Length(0, 500), Optional()])
    ativo = BooleanField('Ativo')
    solicitar_asos = BooleanField('Solicitar ASO`s')
    
    data_inclusao = DateTimeField('Data Inclusão', validators=[Optional()])
    data_alteracao = DateTimeField('Data Alteração', validators=[Optional()])
    incluido_por = StringField('Incluído por', validators=[Optional()])
    alterado_por = StringField('Alterado por', validators=[Optional()])
    botao_salvar = SubmitField('Salvar')

    # validar se cod do prestador ja existe
    def validate_cod_prestador(self, cod_prestador):
        prestador = (
            database.session.query(Prestador)
            .filter(Prestador.cod_empresa_principal == self.cod_empresa_principal.data)
            .filter(Prestador.cod_prestador == cod_prestador.data)
            .first()
        )
        if prestador:
            raise ValidationError('Já existe um prestador com esse código')
    
    def validate_emails(self, emails):
        FormCriarEmpresa.validate_emails(self, emails)


class FormEditarPrestador(FormCriarPrestador):
    
    # validar se ja tem outro com o mesmo codigo
    def validate_cod_prestador(self, cod_prestador):
        prestador_x = Prestador.query.get(request.args.get('id_prestador'))
        # verificar se cod inputado e diferente do cod original do prestador
        if prestador_x.cod_prestador != cod_prestador.data:
            prestador_y = (
                database.session.query(Prestador)
                .filter(Prestador.cod_empresa_principal == self.cod_empresa_principal.data)
                .filter(Prestador.cod_prestador == cod_prestador.data)
                .first()
            )
            if prestador_y:
                raise ValidationError('Já existe um prestador com esse código')

