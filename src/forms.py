from flask import request
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (BooleanField, DateField, DateTimeField, FileField,
                     IntegerField, PasswordField, SelectField,
                     SelectMultipleField, StringField, SubmitField, TelField,
                     TextAreaField)
from wtforms.validators import (DataRequired, Email, EqualTo, InputRequired,
                                Length, Optional, ValidationError)

from src import database

from .main.empresa.empresa import Empresa
from .main.empresa_principal.empresa_principal import EmpresaPrincipal
from .main.exame.exame import Exame
from .main.grupo.grupo import Grupo
from .main.prestador.prestador import Prestador
from .main.status.status import Status
from .main.status.status_lib import StatusLiberacao
from .main.status.status_rac import StatusRAC
from .main.unidade.unidade import Unidade
from .main.usuario.usuario import Usuario
from .utils import tratar_emails


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


class FormBuscarExames(FormBuscarEmpresa):
    nome = StringField('Nome', validators=[Optional()])
    prazo = IntegerField('Id', validators=[Optional()])


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


class FormCriarConta(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(3, 50)])
    nome_usuario = StringField('Nome do Usuário', validators=[DataRequired(), Length(3, 100)])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    tel = TelField('Telefone (Opcional)', validators=[Optional(), Length(0, 20)], render_kw={'placeholder': '(11) 3741-9977'})
    cel = TelField('Celular (Opcional)', validators=[Optional(), Length(0, 20)], render_kw={'placeholder': '(11) 93741-9977'})
    senha = PasswordField('Senha', validators=[DataRequired(), Length(6, 50)])
    confirmacao_senha = PasswordField('Confirmação da Senha', validators=[DataRequired(), EqualTo('senha')])
    tipo_usuario = SelectField('Tipo de usuário', validators=[DataRequired()])
    botao_criarconta = SubmitField('Criar Conta')

    def validate_username(self, username):
        usuario = Usuario.query.filter_by(username=username.data).first()
        if usuario:
            raise ValidationError('Esse username já foi cadastrado')

    def validate_email(self, email):
        usuario = Usuario.query.filter_by(email=email.data).first()
        if usuario:
            raise ValidationError('Esse email já foi cadastrado')

    def validate_tel(self, tel):
        if tel.data:
            if not tel.data.isnumeric():
                raise ValidationError('Apenas dígitos')
    
    def validate_cel(self, cel):
        if cel.data:
            if not cel.data.isnumeric():
                raise ValidationError('Apenas dígitos')


class FormLogin(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(3, 50)])
    senha = PasswordField('Senha', validators=[DataRequired(), Length(6, 50)])
    botao_login = SubmitField('Login')


class FormOTP(FlaskForm):
    otp = StringField('Chave de acesso', validators=[DataRequired(), Length(3, 50)])
    botao_login = SubmitField('Login')


class FormEditarPerfil(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(3, 50)])
    nome_usuario = StringField('Nome do Usuário', validators=[DataRequired(), Length(3, 50)])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    tel = TelField('Telefone (Opcional)', validators=[Optional(), Length(0, 20)], render_kw={'placeholder': '(11) 3741-9977'})
    cel = TelField('Celular (Opcional)', validators=[Optional(), Length(0, 20)], render_kw={'placeholder': '(11) 93741-9977'})
    botao_salvar = SubmitField('Salvar')

    def validate_email(self, email):
        usuario = Usuario.query.get(request.args.get('id_usuario', type=int))
        
        if usuario.email != email.data:
            dono_do_email = Usuario.query.filter_by(email=email.data).first()
            if dono_do_email:
                raise ValidationError('Esse email já está sendo usado')

    def validate_username(self, username):
        usuario = Usuario.query.get(request.args.get('id_usuario', type=int))

        if usuario.username != username.data:
            dono_do_username = Usuario.query.filter_by(username=username.data).first()
            if dono_do_username:
                raise ValidationError('Esse username já está sendo usado')

    def validate_tel(self, tel):
        FormCriarConta.validate_tel(self, tel)

    def validate_cel(self, cel):
        FormCriarConta.validate_cel(self, cel)


class FormAlterarSenha(FlaskForm):
    senha = PasswordField('Senha', validators=[DataRequired(), Length(6, 50)])
    confirmacao_senha = PasswordField('Confirmação da Senha', validators=[DataRequired(), EqualTo('senha')])
    botao_salvar = SubmitField('Salvar')


class FormConfigUsuario(FlaskForm):
    ativo = BooleanField('Usuário Ativo')
    tipo_usuario = SelectField('Tipo de Usuário', choices=[], validators=[DataRequired()])
    botao_salvar = SubmitField('Salvar')


class FormAlterarChave(FlaskForm):
    chave = PasswordField('Chave de Integração', validators=[DataRequired(), Length(6, 50)])
    confirmacao_chave = PasswordField('Confirmação da Chave', validators=[DataRequired(), EqualTo('chave')])
    botao_salvar = SubmitField('Salvar')


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


class FormCriarStatus(FlaskForm):
    nome_status = StringField('Nome do Status', validators=[DataRequired(), Length(3, 100)])
    finaliza_processo = BooleanField('Finaliza Processo')
    
    data_inclusao = DateTimeField('Data Inclusão', validators=[Optional()])
    data_alteracao = DateTimeField('Data Alteração', validators=[Optional()])
    incluido_por = StringField('Incluído por', validators=[Optional()])
    alterado_por = StringField('Alterado por', validators=[Optional()])
    botao_salvar = SubmitField('Salvar')


class FormCriarGrupo(FlaskForm):
    nome_grupo = StringField('Nome do Grupo', validators=[DataRequired(), Length(3, 255)])
    
    data_inclusao = DateTimeField('Data Inclusão', validators=[Optional()])
    data_alteracao = DateTimeField('Data Alteração', validators=[Optional()])
    incluido_por = StringField('Incluído por', validators=[Optional()])
    alterado_por = StringField('Alterado por', validators=[Optional()])
    
    botao_salvar = SubmitField('Salvar')


class FormGrupoPrestadores(FlaskForm):
    select = SelectMultipleField(label='Select', choices=[], validate_choice=False, id='dualListBox')
    botao_salvar = SubmitField('Salvar')


class FormBuscarASO(FlaskForm):
    kws_pesquisa_geral = {'onchange': "CarregarOpcoesBuscaPedido('cod_empresa_principal', 'id_empresa', 'id_prestador', 'id_unidade', 'flexSwitch')"}
    kws_cod_empresa_principal = {'onchange': "CarregarOpcoesBuscaPedido('cod_empresa_principal', 'id_empresa', 'id_prestador', 'id_unidade', 'flexSwitch')"}
    kws_id_empresa = {'onchange':"carregarOpcoesUnidade('cod_empresa_principal', 'id_empresa', 'id_unidade')"}

    pesquisa_geral = BooleanField('Busca Geral', render_kw=kws_pesquisa_geral) # flexSwitch
    cod_empresa_principal = SelectField('Empresa Principal', choices=[], validators=[Optional()], render_kw=kws_cod_empresa_principal)
    id_empresa = SelectField('Empresa', choices=[], validators=[Optional()], render_kw=kws_id_empresa, validate_choice=False)
    id_unidade = SelectField('Unidade', choices=[], validators=[Optional()], validate_choice=False)
    id_prestador = SelectField('Prestador', choices=[], validators=[Optional()], validate_choice=False)
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


class FormLogAcoes(FlaskForm):
    data_inicio = DateField('Inicio', validators=[Optional()])
    data_fim = DateField('Fim', validators=[Optional()])
    usuario = SelectField('Usuário', choices=[], validators=[Optional()])
    tabela = SelectField('Tabela', validators=[Optional()])
    botao_buscar = SubmitField('Buscar')

    def validate_data_inicio(self, data_inicio):
        if data_inicio.data and self.data_fim.data:
            if data_inicio.data > self.data_fim.data:
                raise ValidationError('Inicio deve ser menor do que Fim')


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


class FormImportarDados(FlaskForm):
    opcoes_tabela = [
        ('', 'Selecione'),
        (1, 'Empresas'),
        (2, 'Unidades'),
        (3, 'Exames')
    ]

    tabela = SelectField('Tabela para Atualizar', choices=opcoes_tabela, validators=[DataRequired()])
    csv = FileField(
        'Escolher arquivo',
        validators=[
            FileRequired(),
            FileAllowed(['csv'], message='Apenas arquivos CSV')
        ]
    )
    btn_upload = SubmitField('Upload')


class FormPedidoBulkUpdate(FlaskForm):
    csv = FileField(
        'Escolher arquivo',
        validators=[
            FileRequired(),
            FileAllowed(['csv'], message='Apenas arquivos CSV')
        ]
    )
    btn_upload = SubmitField('Upload')

