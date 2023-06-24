from flask import request
from flask_wtf import FlaskForm
from wtforms import BooleanField, IntegerField, SelectField, StringField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from src import database
from src.main.empresa_principal.empresa_principal import EmpresaPrincipal

from .empresa_socnet import EmpresaSOCNET


class FormBuscarEmpresaSOCNET(FlaskForm):
    opcoes = [('', 'Selecione'), (1, 'Sim'), (0, 'Não')]
    cod_empresa_principal = SelectField('Empresa Principal', choices=[], validators=[Optional()])
    cod_empresa_referencia = SelectField('Empresa Referência', choices=[], validators=[Optional()])
    id_empresa = IntegerField('Id', validators=[Optional()])
    cod_empresa = IntegerField('Código', validators=[Optional()])
    nome_empresa = StringField('Nome Empresa', validators=[Optional()])
    empresa_ativa = SelectField('Empresa Ativa', choices=opcoes, validators=[Optional()])

    def load_choices(self):
        opts = (
            [('', 'Selecione')] +
            [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
        )

        self.cod_empresa_principal.choices = opts
        self.cod_empresa_referencia.choices = opts
        return None


class FormEmpresaSOCNET(FlaskForm):
    def __init__(
            self,
            modo: int = 1,
            id_empresa: int | None = None,
            *args,
            **kwargs
        ):
        '''
            Args:
                modo (int): modo de utilização do formulário. 1: Inserir, 2: Editar.
                Defaults to 1.
        '''
        super().__init__(*args, **kwargs)
        self.modo = modo
        self.id_empresa = id_empresa

    cod_empresa_principal = SelectField('Empresa Base', choices=[], validators=[DataRequired()])
    cod_empresa_referencia = SelectField('Empresa Referência', choices=[], validators=[DataRequired()])

    cod_empresa = IntegerField('Código empresa', validators=[DataRequired()])
    nome_empresa = StringField('Nome Empresa', validators=[DataRequired(), Length(3, 255)])

    ativo = BooleanField('Empresa Ativa')

    def load_choices(self):
        opcoes = (
            [('', 'Selecione')] + 
            [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
        )

        self.cod_empresa_principal.choices = opcoes
        self.cod_empresa_referencia.choices = opcoes
        return None

    def validate_cod_empresa(self, cod_empresa):
        MSG = 'Outra Empresa SOCNET já está usando \
            esta combinação de Empresa Base + Referência + Código'

        match self.modo:
            case 1:
                self.validar_inclusao(MSG)
            case 2:
                self.validar_edicao(MSG)

        return None

    def validar_inclusao(self, msg):
        empresa = (
            database.session.query(EmpresaSOCNET)
            .filter(EmpresaSOCNET.cod_empresa_principal == int(self.cod_empresa_principal.data))
            .filter(EmpresaSOCNET.cod_empresa_referencia == int(self.cod_empresa_referencia.data))
            .filter(EmpresaSOCNET.cod_empresa == int(self.cod_empresa.data))
            .first()
        )

        if empresa:
            raise ValidationError(msg)

        return None

    def validar_edicao(self, msg):
        # NOTE: em casos de edicao, receber id_empresa atraves do metodo init do form
        empresa_x = EmpresaSOCNET.query.get(self.id_empresa)

        empresa_y = (
            database.session.query(EmpresaSOCNET)
            .filter(EmpresaSOCNET.cod_empresa_principal == int(self.cod_empresa_principal.data))
            .filter(EmpresaSOCNET.cod_empresa_referencia == int(self.cod_empresa_referencia.data))
            .filter(EmpresaSOCNET.cod_empresa == int(self.cod_empresa.data))
            .first()
        )

        if empresa_y:
            if empresa_x.id_empresa != empresa_y.id_empresa:
                raise ValidationError(msg)

        return None

