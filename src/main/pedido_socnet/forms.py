from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (BooleanField, DateField, IntegerField, SelectField,
                     StringField, SubmitField)
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from ..pedido.forms import FormEditarPedido


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
