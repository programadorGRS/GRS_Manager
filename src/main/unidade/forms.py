from flask import request
from flask_wtf import FlaskForm
from wtforms import (BooleanField, DateTimeField, SelectField, StringField,
                     SubmitField)
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from src import database

from ..empresa.forms import FormBuscarEmpresa, FormCriarEmpresa
from .unidade import Unidade


class FormBuscarUnidade(FormBuscarEmpresa):
    cod_empresa_principal = SelectField(
        'Empresa Principal',
        choices=[],
        validators=[Optional()],
        render_kw={'onchange': "carregarOpcoesEmpresa('cod_empresa_principal', 'id_empresa')"}
    )
    nome = StringField('Nome', validators=[Optional()])
    cod = StringField('Código', validators=[Optional()])
    id_empresa = SelectField('Empresa', choices=[('', 'Selecione')], validators=[Optional()], validate_choice=False)


class FormCriarUnidade(FlaskForm):
    cod_empresa_principal = SelectField(
        'Empresa Principal',
        choices=[],
        validators=[DataRequired()],
        render_kw={'onchange': "carregarOpcoesEmpresa('cod_empresa_principal', 'id_empresa')"}
    )
    id_empresa = SelectField('Empresa', choices=[], validators=[DataRequired()], validate_choice=False)
    cod_unidade = StringField('Código da unidade', validators=[DataRequired()])
    nome_unidade = StringField('Nome da unidade', validators=[DataRequired(), Length(3, 255)])
    razao_social = StringField('Razão Social (Opcional)', validators=[Length(0, 100), Optional()])
    cod_rh = StringField('Código RH (Opcional)', validators=[Length(0, 100), Optional()])
    cnpj = StringField('CNPJ (Opcional)', validators=[Length(0, 100), Optional()])
    uf = StringField('UF (Opcional)', validators=[Length(0, 4), Optional()])
    emails = StringField('E-mails (Opcional)', validators=[Length(0, 500), Optional()])
    emails_conv_exames = StringField('E-mails Convocação Exames (Opcional)', validators=[Length(0, 500)])
    emails_absenteismo = StringField('E-mails Absenteísmo (Opcional)', validators=[Length(0, 500)])
    emails_exames_realizados = StringField('E-mails Exames Realizados (Opcional)', validators=[Length(0, 500)])
    ativo = BooleanField('Ativo')
    conv_exames = BooleanField('Conv. de Exames')
    
    data_inclusao = DateTimeField('Data Inclusão', validators=[Optional()])
    data_alteracao = DateTimeField('Data Alteração', validators=[Optional()])
    incluido_por = StringField('Incluído por', validators=[Optional()])
    alterado_por = StringField('Alterado por', validators=[Optional()])
    botao_salvar = SubmitField('Salvar')

    # validar se cod da unidade ja existe
    def validate_cod_unidade(self, cod_unidade):
        unidade = (
            database.session.query(Unidade)
            .filter(Unidade.cod_empresa_principal == self.cod_empresa_principal.data)
            .filter(Unidade.id_empresa == self.id_empresa.data)
            .filter(Unidade.cod_unidade == cod_unidade.data)
            .first()
        )
        if unidade:
            raise ValidationError('Já existe uma unidade na empresa com esse código')
    
    def validate_emails(self, emails):
        FormCriarEmpresa.validate_emails(self, emails)


class FormEditarUnidade(FormCriarUnidade):

    # validar se ja tem outra com o mesmo codigo
    def validate_cod_unidade(self, cod_unidade):        
        unidade_x = Unidade.query.get(int(request.args.get('id_unidade')))

        # verificar se cod inputado e diferente do cod original da unidade
        if unidade_x.cod_unidade != cod_unidade.data:
            
            unidade_y = (
            database.session.query(Unidade)
                .filter(Unidade.cod_empresa_principal == self.cod_empresa_principal.data)
                .filter(Unidade.id_empresa == self.id_empresa.data)
                .filter(Unidade.cod_unidade == cod_unidade.data)
                .first()
            )
            
            if unidade_y:
                raise ValidationError('Já existe uma unidade na empresa com esse código')


class FormManservAtualiza(FlaskForm):
    '''
    Form para atualizar os emails das unidades das Empesas do Grupo MANSERV

    Pode ser acessado sem login_required
    '''
    cod_empresa_principal = SelectField('Empresa Principal', choices=[(423, 'GRS Núcleo')], validators=[DataRequired()])
    empresa = SelectField('Empresa', choices=[], validators=[DataRequired()], render_kw={'onchange': "carregarOpcoesUnidadePublic('cod_empresa_principal', 'empresa', 'unidade')"})
    unidade = SelectField('Unidade', choices=[], validators=[DataRequired()], coerce=int, validate_choice=False)
    nome = StringField('Nome', validators=[DataRequired(), Length(0, 255)])
    emails_conv_exames = StringField('E-mails (se houver mais de um separar por ";")', validators=[DataRequired(), Length(0, 500)])
    disclaimer = BooleanField('Declaração', validators=[DataRequired()])
    botao_salvar = SubmitField('Enviar')
