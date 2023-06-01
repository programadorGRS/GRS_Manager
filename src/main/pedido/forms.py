from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (BooleanField, DateField, DateTimeField, FileField,
                     IntegerField, SelectField, StringField, SubmitField,
                     TextAreaField)
from wtforms.validators import (DataRequired, InputRequired, Length, Optional,
                                ValidationError)

from ..empresa_principal.empresa_principal import EmpresaPrincipal
from ..grupo.grupo import Grupo
from ..status.status import Status
from ..status.status_lib import StatusLiberacao
from ..status.status_rac import StatusRAC
from ..tipo_exame.tipo_exame import TipoExame


class FormBuscarASO(FlaskForm):
    kws_pesquisa_geral = {'onchange': "CarregarOpcoesBuscaPedido('cod_empresa_principal', 'id_empresa', 'id_prestador', 'id_unidade', 'flexSwitch')"}
    kws_cod_empresa_principal = {'onchange': "CarregarOpcoesBuscaPedido('cod_empresa_principal', 'id_empresa', 'id_prestador', 'id_unidade', 'flexSwitch')"}
    kws_id_empresa = {'onchange':"carregarOpcoesUnidade('cod_empresa_principal', 'id_empresa', 'id_unidade')"}

    pesquisa_geral = BooleanField('Busca Geral', render_kw=kws_pesquisa_geral) # flexSwitch
    cod_empresa_principal = SelectField('Empresa Principal', choices=[], validators=[Optional()], render_kw=kws_cod_empresa_principal)
    id_empresa = SelectField('Empresa', choices=[], validators=[Optional()], render_kw=kws_id_empresa, validate_choice=False)
    id_unidade = SelectField('Unidade', choices=[], validators=[Optional()], validate_choice=False)
    id_prestador = SelectField('Prestador', choices=[], validators=[Optional()], validate_choice=False)
    cod_tipo_exame = SelectField('Tipo Exame', choices=[], validators=[Optional()])
    data_inicio = DateField('Inicio', validators=[Optional()])
    data_fim = DateField('Fim', validators=[Optional()])
    nome_funcionario = StringField('Nome Funcionário', validators=[Optional(), Length(0, 255)])
    seq_ficha = IntegerField('Seq. Ficha', validators=[Optional()])
    obs = StringField('Observação', validators=[Optional(), Length(0, 100)])
    id_status = SelectField('Status ASO', choices=[], validators=[Optional()])
    id_status_rac = SelectField('Status RAC', choices=[], validators=[Optional()])
    id_tag = SelectField('Tag Prazo Liberação', choices=[], validators=[Optional()])
    id_grupos = SelectField('Grupo', choices=[], validators=[Optional()])
    
    def validate_data_inicio(self, data_inicio):
        if data_inicio.data and self.data_fim.data:
            if data_inicio.data > self.data_fim.data:
                raise ValidationError('Inicio deve ser menor do que Fim')

    def load_choices(self):
        self.cod_empresa_principal.choices = (
            [('', 'Selecione')] +
            [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
        )

        self.id_status.choices = (
            [('', 'Selecione')] +
            [
                (i.id_status, i.nome_status)
                for i in Status.query
                .order_by(Status.nome_status)
                .all()
            ]
        )
        self.id_status_rac.choices = (
            [('', 'Selecione')] +
            [
                (i.id_status, i.nome_status)
                for i in StatusRAC.query
                .order_by(StatusRAC.nome_status)
                .all()
            ]
        )

        self.id_tag.choices = (
            [('', 'Selecione')] +
            [
                (i.id_status_lib, i.nome_status_lib)
                for i in StatusLiberacao.query
                .order_by(StatusLiberacao.nome_status_lib)
                .all()
            ]
        )

        self.id_grupos.choices = (
            [
                ('my_groups', 'Meus Grupos'),
                ('all', 'Todos'),
                ('null', 'Sem Grupo')
            ] + 
            [
                (gp.id_grupo, gp.nome_grupo)
                for gp in Grupo.query.all()
            ]
        )

        self.cod_tipo_exame.choices = (
            [('', 'Selecione')] +
            [
                (i.cod_tipo_exame, i.nome_tipo_exame)
                for i in TipoExame.query
                .order_by(TipoExame.nome_tipo_exame)
                .all()
            ]
        )
        return None


class FormAtualizarStatus(FlaskForm):
    status_aso = SelectField('Status ASO', choices=[], validators=[DataRequired()])
    status_rac = SelectField('Status RAC (Opcional)', choices=[], validators=[Optional()])
    data_recebido = DateField('Data Recebimento (Opcional)', validators=[Optional()])
    data_comparecimento = DateField('Data Comparecimento (Opcional)', validators=[Optional()])
    obs = TextAreaField('Observação (Max 255 caracteres)', validators=[Optional(), Length(0, 255)])


class FormEnviarEmails(FlaskForm):
    assunto_email = StringField('Assunto (Opcional)', validators=[Optional(), Length(0, 255)], render_kw={"placeholder": "Incluir um Assunto para os E-mails (Max 255)"})
    email_copia = StringField('E-mail CC (Opcional)', validators=[Optional(), Length(0, 255)], render_kw={"placeholder": "Incluir Pessoas em Cópia (Max 255)"})
    obs_email = TextAreaField('Observação (Opcional)', validators=[Optional(), Length(0, 255)], render_kw={"placeholder": "Incluir uma Observação no corpo do E-mail (Max 255)"})


class FormEditarPedido(FlaskForm):
    cod_empresa_principal = SelectField("Empresa Principal", validators=[Optional()])
    seq_ficha = IntegerField('Seq. Ficha', validators=[Optional()])
    cod_funcionario = IntegerField('Cód. Funcionário', validators=[Optional()])
    cpf = StringField('CPF', validators=[Optional()])
    nome_funcionario = StringField('Nome Funcionário', validators=[Optional()])
    data_ficha = DateField('Data Ficha', validators=[DataRequired()])
    tipo_exame = SelectField('Tipo Exame', choices=[], validators=[DataRequired()])
    prestador = SelectField('Prestador', choices=[], validators=[DataRequired()], validate_choice=False)
    empresa = SelectField('Empresa', choices=[], validators=[DataRequired()], render_kw={'onchange':"carregarOpcoesUnidade('cod_empresa_principal', 'empresa', 'unidade')"}, validate_choice=False)
    unidade = SelectField('Unidade', choices=[], validators=[DataRequired()], coerce=int, validate_choice=False)
    status = SelectField('Status', choices=[], validators=[DataRequired()])
    data_recebido = DateField('Data Recebido', validators=[Optional()])
    obs = TextAreaField('Observação (Max 255 caracteres)', validators=[Optional(), Length(0, 255)])
    prazo = IntegerField('Prazo Liberação (Dias úteis)', validators=[InputRequired()])
    prev_liberacao = DateField('Previsão Liberação', validators=[DataRequired()])
    data_inclusao = DateTimeField('Data Inclusão', validators=[Optional()])
    data_alteracao = DateTimeField('Data Alteração', validators=[Optional()])
    incluido_por = StringField('Incluído por', validators=[Optional()])
    alterado_por = StringField('Alterado por', validators=[Optional()])
    botao_salvar = SubmitField('Salvar')
    
    def validate_prev_liberacao(self, prev_liberacao):
        if prev_liberacao.data and self.data_ficha.data:
            if prev_liberacao.data < self.data_ficha.data:
                raise ValidationError('Deve ser maior ou igual à Data da Ficha')


class FormCarregarPedidos(FlaskForm):
    cod_empresa_principal = SelectField('Empresa Principal', choices=[], validators=[DataRequired()])
    data_inicio = DateField('Inicio', validators=[DataRequired()])
    data_fim = DateField('Fim', validators=[DataRequired()])
    botao_carregar = SubmitField('Carregar')

    def validate_data_inicio(self, data_inicio):
        if data_inicio.data and self.data_fim.data:
            if data_inicio.data > self.data_fim.data:
                raise ValidationError('Inicio deve ser menor do que Fim')
            elif (self.data_fim.data - data_inicio.data).days > 31:
                raise ValidationError('Máximo de 31 dias')


class FormPedidoBulkUpdate(FlaskForm):
    csv = FileField(
        'Escolher arquivo',
        validators=[
            FileRequired(),
            FileAllowed(['csv'], message='Apenas arquivos CSV')
        ]
    )
    btn_upload = SubmitField('Upload')

