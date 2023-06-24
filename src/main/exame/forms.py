from flask import request
from flask_wtf import FlaskForm
from wtforms import (DateTimeField, IntegerField, SelectField, StringField,
                     SubmitField)
from wtforms.validators import (DataRequired, InputRequired, Optional,
                                ValidationError)

from src import database

from .exame import Exame


class FormBuscarExames(FlaskForm):
    cod_empresa_principal = SelectField('Empresa Principal', choices=[], validators=[Optional()])
    id = IntegerField('Id', validators=[Optional()])
    cod = IntegerField('Código', validators=[Optional()])
    nome = StringField('Nome', validators=[Optional()])
    prazo = IntegerField('Prazo', validators=[Optional()])


class FormCriarExame(FlaskForm):
    cod_empresa_principal = SelectField(
        'Empresa Principal',
        choices=[],
        validators=[DataRequired()],
        render_kw={'onchange': "carregarOpcoesEmpresa('cod_empresa_principal', 'id_empresa')"}
    )
    cod_exame = StringField('Cód. Exame', validators=[DataRequired()])
    nome_exame = StringField('Nome Exame', validators=[DataRequired()])
    prazo = IntegerField('Prazo (Dias úteis)', validators=[InputRequired()])

    data_inclusao = DateTimeField('Data Inclusão', validators=[Optional()])
    data_alteracao = DateTimeField('Data Alteração', validators=[Optional()])
    incluido_por = StringField('Incluído por', validators=[Optional()])
    alterado_por = StringField('Alterado por', validators=[Optional()])

    botao_salvar = SubmitField('Salvar')

    def validate_cod_exame(self, cod_exame):
        prestador = (
            database.session.query(Exame)
            .filter(Exame.cod_empresa_principal == self.cod_empresa_principal.data)
            .filter(Exame.cod_exame == cod_exame.data)
            .first()
        )
        if prestador:
            raise ValidationError('Já existe um Exame com esse código')


class FormEditarExame(FormCriarExame):

    # validar se ja tem outro com o mesmo codigo
    def validate_cod_prestador(self, cod_exame):
        exame_x = Exame.query.get(request.args.get('id_exame'))
        # verificar se cod inputado e diferente do cod original do prestador
        if exame_x.cod_exame != cod_exame.data:
            exame_y = (
                database.session.query(Exame)
                .filter(Exame.cod_empresa_principal == self.cod_empresa_principal.data)
                .filter(Exame.cod_exame == cod_exame.data)
                .first()
            )
            if exame_y:
                raise ValidationError('Já existe um Exame com esse código')
