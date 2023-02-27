import secrets
from datetime import date, datetime, timedelta

import jwt
import numpy as np
import pandas as pd
from flask import request
from flask_login import UserMixin, current_user
from pytz import timezone
from sqlalchemy import update
from sqlalchemy.inspection import inspect
from workalendar.america import Brazil

from manager import app, bcrypt, database, login_manager


# carregar usuario
@login_manager.user_loader
def load_usuario(id_cookie):
    # puxar usuario pelo id aleatorio de cookie
    return Usuario.query.filter_by(id_cookie=id_cookie).first()
    # metodo padrao:
    # return Usuario.query.get(int(id_usuario))


# TABELAS DE ASSOCIACAO MANY TO MANY ---------------------------------------
grupo_usuario = database.Table('grupo_usuario',
    database.Column('id_grupo', database.Integer, database.ForeignKey('Grupo.id_grupo')),
    database.Column('id_usuario', database.Integer, database.ForeignKey('Usuario.id_usuario'))
)


grupo_empresa = database.Table('grupo_empresa',
    database.Column('id_grupo', database.Integer, database.ForeignKey('Grupo.id_grupo')),
    database.Column('id_empresa', database.Integer, database.ForeignKey('Empresa.id_empresa'))
)


grupo_prestador = database.Table('grupo_prestador',
    database.Column('id_grupo', database.Integer, database.ForeignKey('Grupo.id_grupo')),
    database.Column('id_prestador', database.Integer, database.ForeignKey('Prestador.id_prestador'))
)


class EmpresaPrincipal(database.Model):
    __tablename__ = 'EmpresaPrincipal'
    cod = database.Column(database.Integer, primary_key=True, autoincrement=False)
    nome = database.Column(database.String(255), nullable=False)
    ativo = database.Column(database.Boolean, nullable=False, default=True)
    socnet = database.Column(database.Boolean, nullable=False, default=True)
    configs_exporta_dados = database.Column(database.String(255))
    
    empresas = database.relationship('Empresa', backref='empresa_principal', lazy=True) # one to many
    empresas_socnet = database.relationship('EmpresaSOCNET', backref='empresa_principal', lazy=True) # one to many
    unidades = database.relationship('Unidade', backref='empresa_principal', lazy=True) # one to many
    exames = database.relationship('Exame', backref='empresa_principal', lazy=True) # one to many
    
    data_inclusao = database.Column(database.DateTime)
    data_alteracao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    alterado_por = database.Column(database.String(50))

    def __repr__(self) -> str:
        return f'<{self.cod}> {self.nome}'


# UserMixin para carregar o usuario atraves dessa tabela
class Usuario(database.Model, UserMixin):
    __tablename__ = 'Usuario'
    id_usuario = database.Column(database.Integer, primary_key=True)
    # id_cookie serve para resetar todas as sessoes do usuario
    # deve ser mudado ao mudar a senha para que todos os cookies do usuario
    # sejam resetados e as sessoes sejam deslogadas
    id_cookie = database.Column(database.String(255), nullable=False, unique=True)
    username = database.Column(database.String(50), nullable=False, unique=True)
    nome_usuario = database.Column(database.String(100), nullable=False)
    email = database.Column(database.String(255), nullable=False, unique=True)
    celular = database.Column(database.String(20))
    telefone = database.Column(database.String(20))
    senha = database.Column(database.String(300), nullable=False)
    otp = database.Column(database.String(300)) # one time password
    chave_api = database.Column(database.String(300))
    tipo_usuario = database.Column(database.Integer, database.ForeignKey('TipoUsuario.id_role'), default=2, nullable=False)
    ativo = database.Column(database.Boolean, nullable=False, default=True)
    foto_perfil = database.Column(database.String(255), default='manager/static/fotos_perfil/default.png')
    grupo = database.relationship('Grupo', secondary=grupo_usuario, backref='usuarios', lazy=True) # many to many
    ultimo_login = database.Column(database.DateTime)
    
    data_inclusao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    data_alteracao = database.Column(database.DateTime)
    alterado_por = database.Column(database.String(50))


    # originalmente herdado de UserMixin
    # se o usuario for inativado, não passa mais por @login_required
    @property
    def is_active(self):
        return self.ativo


    # o get_id original e herdado de UserMixin
    # o metodo atual e modificado para que o reset de cookies funcione
    def get_id(self):
        return str(self.id_cookie)

    @classmethod
    def criar_usuario(
        self,
        username: str,
        nome_usuario: str,
        email: str,
        senha: str,
        tipo_usuario: int = 2,
        data_inclusao: datetime = datetime.now(tz=timezone('America/Sao_Paulo')),
        incluido_por: str = 'Servidor',
        telefone: str = None,
        celular: str = None
    ) -> None:
        '''
        Cria um Usuario com a senha ja criptografada e adiciona da database
        '''
        # criptografar senha
        senha_cript = bcrypt.generate_password_hash(senha).decode('utf-8')
        
        # criar usuario
        usuario = Usuario(
            # criar id aleatorio para o cookie de sessao
            id_cookie=secrets.token_hex(16),
            username=username,
            nome_usuario=nome_usuario,
            email=email,
            telefone=telefone,
            celular=celular,
            senha=senha_cript,
            tipo_usuario=tipo_usuario,
            data_inclusao=data_inclusao,
            incluido_por=incluido_por
        )
        
        database.session.add(usuario)
        database.session.commit()
        
        return usuario

    @classmethod
    def update_ultimo_login(self):
        current_user.ultimo_login = datetime.now(tz=timezone('America/Sao_Paulo'))
        database.session.commit()
        return None

    def __repr__(self) -> str:
        return f'<{self.id}> {self.username}'
    

class TipoUsuario(database.Model):
    __tablename__ = 'TipoUsuario'
    id_role = database.Column(database.Integer, primary_key=True)
    nome = database.Column(database.String(255), nullable=False)
    usuarios = database.relationship('Usuario', backref='role', lazy=True) # one to many


class Login(database.Model):
    '''
        Tentativas de Login
    '''
    __tablename__ = 'Login'
    id_log = database.Column(database.Integer, primary_key=True)
    username = database.Column(database.String(255), nullable=False)
    tela = database.Column(database.String(50), nullable=False)
    date_time = database.Column(database.DateTime, nullable=False, default=datetime.now(tz=timezone('America/Sao_Paulo')))
    ip = database.Column(database.String(50), nullable=False)
    obs = database.Column(database.String(500))

    @classmethod
    def get_ip(self) -> str:
        '''
        Retorna ip do usuario atual HTTP_X_FORWARDED_FOR ou REMOTE_ADDR
        '''
        if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
            return request.environ['REMOTE_ADDR']
        else:
            return request.environ['HTTP_X_FORWARDED_FOR'] # if behind a proxy
    
    @classmethod
    def log_attempt(self, username: str, tela: str, ip: str, obs: str=None) -> None:
        '''
        Registra tentativa de login
        '''
        log = Login(
            username=username,
            tela=tela,
            ip=ip,
            obs=obs
        )
        database.session.add(log)
        database.session.commit()
        return None


class LogAcoes(database.Model):
    __tablename__ = 'LogAcoes'
    id_log = database.Column(database.Integer, primary_key=True)
    id_usuario = database.Column(database.Integer, nullable=False)
    username = database.Column(database.String(255), nullable=False)
    tabela = database.Column(database.String(50), nullable=False)
    acao = database.Column(database.String(255), nullable=False)
    # cod ou id do registro que o user alterou ex(cod_empresa, cod_prestador etc)
    id_registro = database.Column(database.Integer, nullable=False)
    # nome do registro alterado ex(nome_funcionario, nome_prestador, nome_empresa etc)
    nome_registro = database.Column(database.String(255), nullable=False)
    obs = database.Column(database.String(1000)) # tamanho do texto passa de 500 chars em alguns casos
    data = database.Column(database.Date, nullable=False, default=date.today())
    hora = database.Column(database.Time, nullable=False, default=datetime.now(tz=timezone('America/Sao_Paulo')).time())


    @classmethod
    def registrar_acao(
        self,
        nome_tabela: str,
        tipo_acao: str,
        id_registro: int,
        nome_registro: str,
        observacao: str = None,
        id_usuario: int = None,
        username: str = None
    ):
        '''
        Cria registro no Log de acoes:
        
          
        - id_usuario = current_user.id_usuario,
        - username = current_user.username,
        '''
        if not id_usuario:
            id_usuario = current_user.id_usuario
        if not username:
            username = current_user.username

        log = self(
            id_usuario = id_usuario,
            username = username,
            tabela = nome_tabela,
            acao = tipo_acao,
            id_registro = id_registro,
            nome_registro = nome_registro,
            obs = observacao
        )
        database.session.add(log)
        database.session.commit()
        return None
    

    @classmethod
    def registrar_acao_api(
        self,
        token: str,
        nome_tabela: str,
        tipo_acao: str,
        id_registro: int,
        nome_registro: str,
        observacao: str = None,
    ):
        '''
        Cria registro no Log de acoes:

        Pega username e user id a partir do token
        '''
        data = jwt.decode(
            jwt=token,
            key=app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        usuario = Usuario.query.get(int(data['username']))
        log = self(
            id_usuario = usuario.id_usuario,
            username = usuario.username,
            tabela = nome_tabela,
            acao = tipo_acao,
            id_registro = id_registro,
            nome_registro = nome_registro,
            obs = observacao,
        )
        database.session.add(log)
        database.session.commit()
        return None
    

    @classmethod
    def pesquisar_log(
        self,
        inicio = None,
        fim = None,
        usuario = None,
        tabela = None
    ):
        parametros = []
        if inicio:
            parametros.append(self.data >= inicio)
        if fim:
            parametros.append(self.data <= fim)
        if usuario:
            parametros.append(self.id_usuario == usuario)
        if tabela:
            parametros.append(self.tabela == tabela)
        if parametros:
            query = (
                database.session.query(self)
                .filter(*parametros)
                .order_by(self.data, self.hora)
            )
        else:
            query = (
                database.session.query(self)
                .order_by(self.data, self.hora)
            )
        return query


class Grupo(database.Model):
    __tablename__ = 'Grupo'
    id_grupo = database.Column(database.Integer, primary_key=True)
    nome_grupo = database.Column(database.String(255), nullable=False) # many to many
   
    data_inclusao = database.Column(database.DateTime)
    data_alteracao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    alterado_por = database.Column(database.String(50))


class TipoExame(database.Model):
    '''
        Tipo de Ficha a que os exames pertencem
    '''
    __tablename__ = 'TipoExame'
    # cod definido pela base do SOC
    cod_tipo_exame = database.Column(database.Integer, primary_key=True, autoincrement=False)
    nome_tipo_exame = database.Column(database.String(100), nullable=False)
    
    pedidos = database.relationship('Pedido', backref='tipo_exame', lazy=True) # one to many
    pedidos_socnet = database.relationship('PedidoSOCNET', backref='tipo_exame', lazy=True) # one to many

    def __repr__(self) -> str:
        return f'<{self.cod_tipo_exame}> {self.nome_tipo_exame}'


class Status(database.Model):
    __tablename__ = 'Status'
    id_status = database.Column(database.Integer, primary_key=True)
    nome_status = database.Column(database.String(100), nullable=False)
    finaliza_processo = database.Column(database.Boolean, nullable=False, default=False)
    status_padrao = database.Column(database.Boolean) # se for padrao, nunca exluir nem editar

    pedidos = database.relationship('Pedido', backref='status', lazy=True) # one to many
    pedidos_socnet = database.relationship('PedidoSOCNET', backref='status', lazy=True) # one to many
    
    data_inclusao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    data_alteracao = database.Column(database.DateTime)
    alterado_por = database.Column(database.String(50))

    def __repr__(self) -> str:
        return f'<{self.id_status}> {self.nome_status}'


class StatusRAC(database.Model):
    __tablename__ = 'StatusRAC'
    id_status = database.Column(database.Integer, primary_key=True)
    nome_status = database.Column(database.String(100), nullable=False)
    status_padrao = database.Column(database.Boolean) # se for padrao, nunca exluir nem editar

    pedidos = database.relationship('Pedido', backref='status_rac', lazy=True) # one to many
    pedidos_socnet = database.relationship('PedidoSOCNET', backref='status_rac', lazy=True) # one to many
    
    data_inclusao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    data_alteracao = database.Column(database.DateTime)
    alterado_por = database.Column(database.String(50))

    def __repr__(self) -> str:
        return f'<{self.id_status}> {self.nome_status}'


class StatusLiberacao(database.Model):
    '''
    Status da previsão de liberacao do ASO

    Baseado na data de prev_liberacao
    '''
    __tablename__ = 'StatusLiberacao'
    id_status_lib = database.Column(database.Integer, primary_key=True)
    nome_status_lib = database.Column(database.String(50), nullable=False)
    cor_tag = database.Column(database.String(50))
    
    pedidos = database.relationship('Pedido', backref='status_lib', lazy=True) # one to many
    pedidos_socnet = database.relationship('PedidoSOCNET', backref='status_lib', lazy=True) # one to many

    def __repr__(self) -> str:
        return f'<{self.id_status_lib}> {self.nome_status_lib}'


# MODELOS SOC ---------------------------------------------------------------
class Empresa(database.Model):
    __tablename__ = 'Empresa'
    id_empresa = database.Column(database.Integer, primary_key=True)
    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    cod_empresa = database.Column(database.Integer, nullable=False)
    nome_abrev = database.Column(database.String(255))
    razao_social_inicial = database.Column(database.String(255))
    razao_social = database.Column(database.String(255), nullable=False)
    ativo = database.Column(database.Boolean, nullable=False, default=True)
    emails = database.Column(database.String(500))
    cnpj = database.Column(database.String(100))
    uf = database.Column(database.String(5))
    
    pedidos = database.relationship('Pedido', backref='empresa', lazy=True) # one to many
    pedidos_proc = database.relationship('PedidoProcessamento', backref='empresa', lazy=True) # one to many
    grupo = database.relationship('Grupo', secondary=grupo_empresa, backref='empresas', lazy=True) # many to many
    unidades = database.relationship('Unidade', backref='empresa', lazy=True) # one to many

    # convocacao de exames
    conv_exames = database.Column(database.Boolean, default=True)
    conv_exames_emails = database.Column(database.String(500))
    conv_exames_corpo_email = database.Column(database.Integer, default=1)
    
    conv_exames_convocar_clinico = database.Column(database.Boolean, default=False)
    conv_exames_nunca_realizados = database.Column(database.Boolean, default=True)
    conv_exames_per_nunca_realizados = database.Column(database.Boolean, default=False)
    conv_exames_pendentes = database.Column(database.Boolean, default=True)
    conv_exames_pendentes_pcmso = database.Column(database.Boolean, default=False)
    conv_exames_selecao = database.Column(database.Integer, default=1)

    # exames realizados
    exames_realizados = database.Column(database.Boolean, default=True)
    exames_realizados_emails = database.Column(database.String(500))

    # absenteismo
    absenteismo = database.Column(database.Boolean, default=True)
    absenteismo_emails = database.Column(database.String(500))
    
    data_inclusao = database.Column(database.DateTime)
    data_alteracao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    alterado_por = database.Column(database.String(50))

    def __repr__(self) -> str:
        return f'<{self.id_empresa}> {self.razao_social}'

    @classmethod
    def buscar_empresas(
        self,
        cod_empresa_principal: int | None = None,
        id_empresa: int = None,
        cod_empresa: int = None,
        nome: str = None,
        ativo: int = None
    ):
        params = []

        if cod_empresa_principal:
            params.append((self.cod_empresa_principal == cod_empresa_principal))
        if id_empresa:
            params.append(self.id_empresa == id_empresa)
        if cod_empresa:
            params.append(self.cod_empresa == cod_empresa)
        if nome:
            params.append(self.razao_social.like(f'%{nome}%'))
        if ativo == 0 or ativo == 1:
            params.append(self.ativo == ativo)

        query = (
            database.session.query(self)
            .filter(*params)
            .order_by(self.razao_social)
        )
        return query


    @classmethod
    def inserir_empresas(
        self,
        cod_empresa_principal: int
    ):
        '''
        Carrega todas as Empresas no exporta dados da EmpresaPrincipal selecionada (ativas e inativas)

        Insere apenas Empresas não existem na db
        '''
        

        from modules.exporta_dados import (empresas, exporta_dados,
                                           get_json_configs)


        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        par = empresas(
            empresa_principal=empresa_principal.cod,
            cod_exporta_dados=credenciais['EXPORTADADOS_EMPRESAS_COD'],
            chave=credenciais['EXPORTADADOS_EMPRESAS_KEY'],
        )
        df_exporta_dados = exporta_dados(parametro=par)
        
        if not df_exporta_dados.empty:
            df_exporta_dados = df_exporta_dados[[
                'CODIGO',
                'NOMEABREVIADO',
                'RAZAOSOCIALINICIAL',
                'RAZAOSOCIAL',
                'ATIVO',
                'CNPJ',
                'UF'
            ]]
            df_exporta_dados['CODIGO'] = df_exporta_dados['CODIGO'].astype(int)
            df_exporta_dados['ATIVO'] = df_exporta_dados['ATIVO'].astype(int)

            df_database = pd.read_sql(
                sql=(
                    database.session.query(
                        Empresa.id_empresa,
                        Empresa.cod_empresa
                    )
                    .filter(Empresa.cod_empresa_principal == cod_empresa_principal)
                ).statement,
                con=database.session.bind
            )

            if not df_database.empty:
                df_final = pd.merge(
                    df_exporta_dados,
                    df_database,
                    how='left',
                    left_on='CODIGO',
                    right_on='cod_empresa'
                )
                df_final = df_final[[
                    'id_empresa',
                    'CODIGO',
                    'NOMEABREVIADO',
                    'RAZAOSOCIALINICIAL',
                    'RAZAOSOCIAL',
                    'ATIVO',
                    'CNPJ',
                    'UF'
                ]]
                df_final = df_final[~df_final['id_empresa'].isin(df_database['id_empresa'])]
            else:
                df_final = df_exporta_dados

            # tratar df
            df_final = df_final.replace(to_replace={'': None})
            df_final = df_final.rename(columns={
                'CODIGO': 'cod_empresa',
                'NOMEABREVIADO': 'nome_abrev',
                'RAZAOSOCIALINICIAL': 'razao_social_inicial',
                'RAZAOSOCIAL': 'razao_social',
                'ATIVO': 'ativo',
                'CNPJ': 'cnpj',
                'UF': 'uf'
            })
            df_final['cod_empresa_principal'] = cod_empresa_principal
            df_final['data_inclusao'] = datetime.now(tz=timezone('America/Sao_Paulo'))
            df_final['incluido_por'] = 'Servidor'

            # inserir
            linhas_inseridas = df_final.to_sql(
                name=self.__tablename__,
                con=database.session.bind,
                if_exists='append',
                index=False
            )
            database.session.commit()
            
            return linhas_inseridas

    @classmethod
    def atualizar_empresas(
        self,
        cod_empresa_principal: int
    ):
        '''
        Carrega todas as Empresas no exporta dados da EmpresaPrincipal selecionada

        Atualiza infos das Empresas que ja existem na db

        '''
        

        from modules.exporta_dados import (empresas, exporta_dados,
                                           get_json_configs)


        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        par = empresas(
            empresa_principal=empresa_principal.cod,
            cod_exporta_dados=credenciais['EXPORTADADOS_EMPRESAS_COD'],
            chave=credenciais['EXPORTADADOS_EMPRESAS_KEY'],
        )
        df_exporta_dados = exporta_dados(parametro=par)
        
        if not df_exporta_dados.empty:
            df_exporta_dados = df_exporta_dados[[
                'CODIGO',
                'NOMEABREVIADO',
                'RAZAOSOCIALINICIAL',
                'RAZAOSOCIAL',
                'ATIVO',
                'CNPJ',
                'UF'
            ]]
            df_exporta_dados['CODIGO'] = df_exporta_dados['CODIGO'].astype(int)
            df_exporta_dados['ATIVO'] = df_exporta_dados['ATIVO'].astype(int)

            df_database = pd.read_sql(
                sql=(
                    database.session.query(
                        Empresa.id_empresa,
                        Empresa.cod_empresa
                    )
                    .filter(Empresa.cod_empresa_principal == cod_empresa_principal)
                ).statement,
                con=database.session.bind
            )

            if not df_database.empty:
                df_final = pd.merge(
                    df_exporta_dados,
                    df_database,
                    how='right',
                    left_on='CODIGO',
                    right_on='cod_empresa'
                )

                df_final.dropna(axis=0, subset=['id_empresa', 'CODIGO'], inplace=True)

                df_final = df_final[[
                    'id_empresa',
                    'NOMEABREVIADO',
                    'RAZAOSOCIALINICIAL',
                    'RAZAOSOCIAL',
                    'ATIVO',
                    'CNPJ',
                    'UF'
                ]]

                # tratar df
                df_final = df_final.replace(to_replace={'': None})
                df_final = df_final.rename(columns={
                    'NOMEABREVIADO': 'nome_abrev',
                    'RAZAOSOCIALINICIAL': 'razao_social_inicial',
                    'RAZAOSOCIAL': 'razao_social',
                    'ATIVO': 'ativo',
                    'CNPJ': 'cnpj',
                    'UF': 'uf'
                })
                df_final['data_alteracao'] = datetime.now(tz=timezone('America/Sao_Paulo'))
                df_final['alterado_por'] = 'Servidor'

                df_final = df_final.to_dict(orient='records')

                database.session.bulk_update_mappings(Empresa, df_final)
                database.session.commit()
        
            return len(df_final)


class Unidade(database.Model):
    __tablename__ = 'Unidade'
    id_unidade = database.Column(database.Integer, primary_key=True)
    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    id_empresa = database.Column(database.Integer, database.ForeignKey('Empresa.id_empresa'), nullable=False)
    cod_unidade = database.Column(database.String(255), nullable=False)
    nome_unidade = database.Column(database.String(255), nullable=False)
    emails = database.Column(database.String(500))
    ativo = database.Column(database.Boolean, nullable=False, default=True)
    
    pedidos = database.relationship('Pedido', backref='Unidade', lazy=True) # one to many

    cod_rh = database.Column(database.String(255))
    cnpj = database.Column(database.String(255))
    uf = database.Column(database.String(10))
    razao_social = database.Column(database.String(255))

    # convocacao de exames
    conv_exames = database.Column(database.Boolean, default=False)
    conv_exames_emails = database.Column(database.String(500))
    conv_exames_corpo_email = database.Column(database.Integer, default=1)

    # exames realizados
    exames_realizados = database.Column(database.Boolean, default=True)
    exames_realizados_emails = database.Column(database.String(500))

    # absenteismo
    absenteismo = database.Column(database.Boolean, default=True)
    absenteismo_emails = database.Column(database.String(500))
    
    data_inclusao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    data_alteracao = database.Column(database.DateTime)
    alterado_por = database.Column(database.String(50))

    def __repr__(self) -> str:
        return f'<{self.id_unidade}> {self.nome_unidade}'
    
    COLUNAS_PLANILHA = [
        'cod_empresa_principal',
        'id_empresa',
        'cod_empresa',
        'razao_social',
        'id_unidade',
        'cod_unidade',
        'cod_rh',
        'cnpj',
        'uf',
        'nome_unidade',
        'emails',
        'ativo',
        'conv_exames',
        'conv_exames_emails',
        'conv_exames_corpo_email',
        'exames_realizados',
        'exames_realizados_emails',
        'absenteismo',
        'absenteismo_emails',
        'data_inclusao',
        'data_alteracao',
        'incluido_por',
        'alterado_por'
    ]

    @classmethod
    def buscar_unidades(
        self,
        cod_empresa_principal: int | None = None,
        id_empresa: int = None,
        id_unidade: int = None,
        cod_unidade: int = None,
        nome: str = None,
        ativo: int = None
    ):
        models = [
            (self.id_unidade), (self.cod_empresa_principal), (self.id_empresa),
            (self.cod_unidade), (self.nome_unidade), (self.emails),
            (self.ativo), (self.conv_exames), (self.cod_rh),
            (self.cnpj), (self.uf), (self.data_inclusao), (self.data_alteracao),
            (self.incluido_por), (self.alterado_por), (self.conv_exames_emails),
            (self.conv_exames_corpo_email), (self.exames_realizados), (self.exames_realizados_emails),
            (self.absenteismo), (self.absenteismo_emails),
            (Empresa.id_empresa), (Empresa.cod_empresa), (Empresa.razao_social)
        ]

        params = []

        if cod_empresa_principal:
            params.append((self.cod_empresa_principal == cod_empresa_principal))
        if id_empresa:
            params.append(self.id_empresa == id_empresa)
        if id_unidade:
            params.append(self.id_unidade == id_unidade)
        if cod_unidade:
            params.append(self.cod_unidade.like(f'%{cod_unidade}%'))
        if nome:
            params.append(self.nome_unidade.like(f'%{nome}%'))
        if ativo == 0 or ativo == 1:
            params.append(self.ativo == ativo)

        query = (
            database.session.query(*models)
            .filter(*params)
            .join(Empresa, Empresa.id_empresa == self.id_empresa)
            .order_by(self.id_empresa)
            .order_by(self.nome_unidade)
        )
        return query

    @classmethod
    def inserir_unidades(
        self,
        cod_empresa_principal: int
    ) -> int | None:
        '''
        Carrega todas as Unidades no exporta dados da EmpresaPrincipal selecionada

        Insere apenas Unidades que cuja chave (cod_empresa + cod_unidade) não existe na db
        '''
        

        from modules.exporta_dados import (exporta_dados, get_json_configs,
                                           unidades)


        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        par = unidades(
            empresa_principal=empresa_principal.cod,
            cod_exporta_dados=credenciais['EXPORTADADOS_UNIDADES_COD'],
            chave=credenciais['EXPORTADADOS_UNIDADES_KEY']
        )
        df_exporta_dados = exporta_dados(parametro=par)
        
        if not df_exporta_dados.empty:
            df_exporta_dados = df_exporta_dados[[
                'CODIGOEMPRESA',
                'CODIGOUNIDADE',
                'NOMEUNIDADE',
                'UNIDADEATIVA',
                'CODIGORHUNIDADE',
                'CNPJUNIDADE',
                'UF',
                'RAZAOSOCIAL'
            ]]
            df_exporta_dados['CODIGOEMPRESA'] = df_exporta_dados['CODIGOEMPRESA'].astype(int)
            df_exporta_dados['UNIDADEATIVA'] = df_exporta_dados['UNIDADEATIVA'].astype(int)

            # carregar empresas da db
            empresas_db = pd.read_sql(
                sql=(
                    database.session.query(
                        Empresa.id_empresa,
                        Empresa.cod_empresa
                    )
                    .filter(Empresa.cod_empresa_principal == cod_empresa_principal)
                ).statement,
                con=database.session.bind
            )

            if not empresas_db.empty:
                # pegar ids empresas
                df_final = pd.merge(
                    df_exporta_dados,
                    empresas_db,
                    how='left',
                    left_on='CODIGOEMPRESA',
                    right_on='cod_empresa'
                )
                df_final.drop(columns='cod_empresa', inplace=True)

                # pegar ids unidades
                unidades_db = pd.read_sql(
                    sql=(
                        database.session.query(
                            Unidade.id_unidade,
                            Unidade.cod_unidade,
                            Empresa.cod_empresa
                        )
                        .join(Empresa, Unidade.id_empresa == Empresa.id_empresa)
                        .filter(Unidade.cod_empresa_principal == cod_empresa_principal)
                    ).statement,
                    con=database.session.bind
                )
                df_final = pd.merge(
                    df_final,
                    unidades_db,
                    how='left',
                    left_on=['CODIGOEMPRESA', 'CODIGOUNIDADE'],
                    right_on=['cod_empresa', 'cod_unidade']
                )
                df_final.drop(columns=['cod_empresa', 'cod_unidade'], inplace=True)

                # manter apenas unidades novas
                df_final = df_final[df_final['id_unidade'].isna()]

                # remover unidades sem empresa na db ou sem cod de unidade
                df_final.dropna(
                    axis=0,
                    subset=['id_empresa', 'CODIGOEMPRESA', 'CODIGOUNIDADE'],
                    inplace=True
                )

                # tratar df
                df_final = df_final[[
                    'id_empresa',
                    'CODIGOUNIDADE',
                    'NOMEUNIDADE',
                    'UNIDADEATIVA',
                    'CODIGORHUNIDADE',
                    'CNPJUNIDADE',
                    'UF',
                    'RAZAOSOCIAL'
                ]]
                df_final = df_final.replace(to_replace={'': None})
                df_final = df_final.rename(columns={
                    'CODIGOUNIDADE': 'cod_unidade',
                    'NOMEUNIDADE': 'nome_unidade',
                    'UNIDADEATIVA': 'ativo',
                    'CODIGORHUNIDADE': 'cod_rh',
                    'CNPJUNIDADE': 'cnpj',
                    'UF': 'uf',
                    'RAZAOSOCIAL': 'razao_social'
                })
                df_final['cod_empresa_principal'] = cod_empresa_principal
                df_final['data_inclusao'] = datetime.now(tz=timezone('America/Sao_Paulo'))
                df_final['incluido_por'] = 'Servidor'

                # inserir
                linhas_inseridas = df_final.to_sql(
                    name=self.__tablename__,
                    con=database.session.bind,
                    if_exists='append',
                    index=False
                )
                database.session.commit()
                
                return linhas_inseridas
            else:
                return None
        else:
            return None

    @classmethod
    def atualizar_unidades(
        self,
        cod_empresa_principal: int
    ):
        '''
        Carrega todas as Unidades no exporta dados da EmpresaPrincipal selecionada

        Atualiza infos das Unidades que ja existem na db

        '''
        

        from modules.exporta_dados import (exporta_dados, get_json_configs,
                                           unidades)


        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        par = unidades(
            empresa_principal=empresa_principal.cod,
            cod_exporta_dados=credenciais['EXPORTADADOS_UNIDADES_COD'],
            chave=credenciais['EXPORTADADOS_UNIDADES_KEY'],
        )
        df_exporta_dados = exporta_dados(parametro=par)
        
        if not df_exporta_dados.empty:
            df_exporta_dados = df_exporta_dados[[
                'CODIGOEMPRESA',
                'CODIGOUNIDADE',
                'NOMEUNIDADE',
                'UNIDADEATIVA',
                'CODIGORHUNIDADE',
                'CNPJUNIDADE',
                'UF',
                'RAZAOSOCIAL'
            ]]
            df_exporta_dados['CODIGOEMPRESA'] = df_exporta_dados['CODIGOEMPRESA'].astype(int)
            df_exporta_dados['UNIDADEATIVA'] = df_exporta_dados['UNIDADEATIVA'].astype(int)

            # pegar ids das unidades
            df_database = pd.read_sql(
                sql=(
                    database.session.query(
                        Unidade.id_unidade,
                        Unidade.cod_unidade,
                        Empresa.cod_empresa
                    )
                    .join(Empresa, Empresa.id_empresa == Unidade.id_empresa)
                    .filter(Unidade.cod_empresa_principal == cod_empresa_principal)
                ).statement,
                con=database.session.bind
            )

            if not df_database.empty:
                df_final = pd.merge(
                    df_exporta_dados,
                    df_database,
                    how='right',
                    left_on=['CODIGOEMPRESA', 'CODIGOUNIDADE'],
                    right_on=['cod_empresa', 'cod_unidade']
                )

                df_final.dropna(axis=0, subset=['UNIDADEATIVA', 'CODIGOUNIDADE', 'CODIGOEMPRESA'], inplace=True)
                
                df_final = df_final[[
                    'id_unidade',
                    'NOMEUNIDADE',
                    'UNIDADEATIVA',
                    'CODIGORHUNIDADE',
                    'CNPJUNIDADE',
                    'UF',
                    'RAZAOSOCIAL'
                ]]

                # tratar df
                df_final = df_final.replace(to_replace={'': None})
                df_final = df_final.rename(columns={
                    'NOMEUNIDADE': 'nome_unidade',
                    'UNIDADEATIVA': 'ativo',
                    'CODIGORHUNIDADE': 'cod_rh',
                    'CNPJUNIDADE': 'cnpj',
                    'UF': 'uf',
                    'RAZAOSOCIAL': 'razao_social'
                })
                df_final['data_alteracao'] = datetime.now(tz=timezone('America/Sao_Paulo'))
                df_final['alterado_por'] = 'Servidor'

                df_final = df_final.to_dict(orient='records')

                database.session.bulk_update_mappings(Unidade, df_final)
                database.session.commit()
        
            return len(df_final)


class Prestador(database.Model):
    __tablename__ = 'Prestador'
    id_prestador = database.Column(database.Integer, primary_key=True)
    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    cod_prestador = database.Column(database.Integer)
    nome_prestador = database.Column(database.String(255), nullable=False)
    emails = database.Column(database.String(500))
    ativo = database.Column(database.Boolean, nullable=False)
    # se recebe ou nao emails de solicitacao de ASOs
    solicitar_asos = database.Column(database.Boolean, default=True)
    cnpj = database.Column(database.String(100))
    uf = database.Column(database.String(4))
    razao_social = database.Column(database.String(255))

    pedidos = database.relationship('Pedido', backref='prestador', lazy=True) # one to many
    pedidos_socnet = database.relationship('PedidoSOCNET', backref='prestador', lazy=True) # one to many
    grupo = database.relationship('Grupo', secondary=grupo_prestador, backref='prestadores', lazy=True) # many to many

    data_inclusao = database.Column(database.DateTime)
    data_alteracao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    alterado_por = database.Column(database.String(50))

    def __repr__(self) -> str:
        return f'<{self.id_prestador}> {self.nome_prestador}'

    @classmethod
    def buscar_prestadores(
        self,
        cod_empresa_principal: int | None = None,
        id_prestador: int | None = None,
        cod_prestador: int | None = None,
        nome: str | None = None,
        ativo: int | None = None
    ):
        params = []

        if cod_empresa_principal:
            params.append(self.cod_empresa_principal == cod_empresa_principal)
        if id_prestador:
            params.append(self.id_prestador == id_prestador)
        if cod_prestador:
            params.append(self.cod_prestador == cod_prestador)
        if nome:
            params.append(self.nome_prestador.like(f'%{nome}%'))
        if ativo == 0 or ativo == 1:
            params.append(self.ativo == ativo)

        query = (
            database.session.query(self)
            .filter(*params)
            .order_by(self.nome_prestador)
        )
        return query


    @classmethod
    def inserir_prestadores(
        self,
        cod_empresa_principal: int
    ):
        '''
        Carrega todas os Prestadores no exporta dados da EmpresaPrincipal selecionada (ativos e inativos)

        Insere apenas Prestadores não existem na db
        '''
        

        from modules.exporta_dados import (exporta_dados, get_json_configs,
                                           prestadores)


        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        par = prestadores(
            cod_empresa_principal=empresa_principal.cod,
            cod_exporta_dados=credenciais['EXPORTADADOS_PRESTADORES_COD'],
            chave=credenciais['EXPORTADADOS_PRESTADORES_KEY'],
            ativo='' # carregar todos
        )
        df_exporta_dados = exporta_dados(parametro=par)
        
        if not df_exporta_dados.empty:

            df_database = pd.read_sql(
                sql=(
                    database.session.query(
                        Prestador.id_prestador,
                        Prestador.cod_prestador
                    )
                    .filter(Prestador.cod_empresa_principal == cod_empresa_principal)
                ).statement,
                con=database.session.bind
            )

            if not df_database.empty:
                df_exporta_dados['codigoPrestador'] = df_exporta_dados['codigoPrestador'].astype(int)
                df_final = pd.merge(
                    df_exporta_dados,
                    df_database,
                    how='left',
                    left_on='codigoPrestador',
                    right_on='cod_prestador'
                )
                df_final = df_final[~df_final['id_prestador'].isin(df_database['id_prestador'])]
            else:
                df_final = df_exporta_dados

            # tratar df
            df_final = df_final[[
                'codigoPrestador',
                'nomePrestador',
                'razaoSocial',
                'cnpj',
                'estado',
                'email',
                'situacao'
            ]]
            df_final = df_final.replace(to_replace={'': None})
            df_final = df_final.rename(columns={
                    'codigoPrestador': 'cod_prestador',
                    'nomePrestador': 'nome_prestador',
                    'razaoSocial': 'razao_social',
                    'email': 'emails',
                    'estado': 'uf',
                    'situacao': 'ativo'
                })
            df_final['ativo'] = df_final['ativo'].replace({'Sim': True, 'Não': False})
            df_final['cod_empresa_principal'] = cod_empresa_principal
            df_final['data_inclusao'] = datetime.now(tz=timezone('America/Sao_Paulo'))
            df_final['incluido_por'] = 'Servidor'

            # tratar emails
            df_final['emails'] = df_final['emails'].str.replace(',', ';')
            df_final['emails'] = df_final['emails'].str.replace(' ', '')
            df_final['emails'] = df_final['emails'].str.lower()
            df_final['emails'] = list(map(self.tratar_emails, df_final['emails']))

            # inserir
            linhas_inseridas = df_final.to_sql(
                name=self.__tablename__,
                con=database.session.bind,
                if_exists='append',
                index=False
            )
            database.session.commit()
            
            return linhas_inseridas

    @classmethod
    def atualizar_prestadores(
        self,
        cod_empresa_principal: int
    ):
        '''
        Carrega todas os Prestadores no exporta dados da EmpresaPrincipal selecionada

        Atualiza infos dos Prestadores que ja existem na db

        '''
        

        from modules.exporta_dados import (exporta_dados, get_json_configs,
                                           prestadores)


        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        par = prestadores(
            cod_empresa_principal=empresa_principal.cod,
            cod_exporta_dados=credenciais['EXPORTADADOS_PRESTADORES_COD'],
            chave=credenciais['EXPORTADADOS_PRESTADORES_KEY'],
        )
        df_exporta_dados = exporta_dados(parametro=par)
        
        if not df_exporta_dados.empty:

            df_database = pd.read_sql(
                sql=(
                    database.session.query(
                        Prestador.id_prestador,
                        Prestador.cod_prestador
                    )
                    .filter(Prestador.cod_empresa_principal == cod_empresa_principal)
                ).statement,
                con=database.session.bind
            )

            if not df_database.empty:
                df_exporta_dados['codigoPrestador'] = df_exporta_dados['codigoPrestador'].astype(int)
                df_final = pd.merge(
                    df_exporta_dados,
                    df_database,
                    how='right',
                    left_on='codigoPrestador',
                    right_on='cod_prestador'
                )
                df_final.dropna(axis=0, subset=['id_prestador', 'codigoPrestador'], inplace=True)

                # tratar df
                df_final = df_final[[
                    'id_prestador',
                    'nomePrestador',
                    'razaoSocial',
                    'cnpj',
                    'estado',
                    'email',
                    'situacao'
                ]]
                df_final = df_final.replace(to_replace={'': None})
                df_final = df_final.rename(columns={
                        'nomePrestador': 'nome_prestador',
                        'razaoSocial': 'razao_social',
                        'email': 'emails',
                        'estado': 'uf',
                        'situacao': 'ativo'
                })
                df_final['ativo'] = df_final['ativo'].replace({'Sim': True, 'Não': False})
                df_final['data_alteracao'] = datetime.now(tz=timezone('America/Sao_Paulo'))
                df_final['alterado_por'] = 'Servidor'

                # tratar emails
                df_final['emails'] = df_final['emails'].str.replace(',', ';')
                df_final['emails'] = df_final['emails'].str.replace(' ', '')
                df_final['emails'] = df_final['emails'].str.lower()
                df_final['emails'] = list(map(self.tratar_emails, df_final['emails']))

                df_final = df_final.to_dict(orient='records')

                database.session.bulk_update_mappings(Prestador, df_final)
                database.session.commit()
        
            return len(df_final)
    
    @staticmethod
    def tratar_emails(emails: str):
        if emails:
            emails = emails.split(sep=';')
            for indice, email in enumerate(emails):
                if not email:
                    emails.pop(indice)
            return ';'.join(emails)
        else:
            return None


class Funcionario(database.Model):
    __tablename__ = 'Funcionario'
    id_funcionario = database.Column(database.Integer, primary_key=True)
    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    cod_funcionario = database.Column(database.Integer, nullable=False)
    nome_funcionario = database.Column(database.String(100))
    cpf_funcionario = database.Column(database.String(20))
    id_empresa = database.Column(database.Integer, database.ForeignKey('Empresa.id_empresa'), nullable=False)
    id_unidade = database.Column(database.Integer, database.ForeignKey('Unidade.id_unidade'))
    cod_setor = database.Column(database.String(100))
    nome_setor = database.Column(database.String(100))
    cod_cargo = database.Column(database.String(100))
    nome_cargo = database.Column(database.String(100))
    situacao = database.Column(database.String(50))
    data_inclusao = database.Column(database.DateTime)

    @classmethod
    def inserir_funcionarios(
        self,
        cod_empresa_principal: int,
        lista_empresas: list[int]
    ):
        from modules.exporta_dados import (cadastro_funcionarios,
                                           exporta_dados, get_json_configs)

        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        total_inseridos = 0
        for id_empresa in lista_empresas:
            empresa = Empresa.query.get(id_empresa)

            print(empresa)

            par = cadastro_funcionarios(
                cod_empresa_principal=empresa_principal.cod,
                cod_exporta_dados=credenciais['EXPORTADADOS_CADFUNCIONARIOSEMPRESA_COD'],
                chave=credenciais['EXPORTADADOS_CADFUNCIONARIOSEMPRESA_KEY'],
                empresaTrabalho=empresa.cod_empresa
            )

            tentativas = 4
            for i in range(tentativas):
                try:
                    df = exporta_dados(parametro=par)
                    break
                except:
                    continue
                

            if not df.empty:
                df['CODIGOEMPRESA'] = df['CODIGOEMPRESA'].astype(int)
                df['CODIGO'] = df['CODIGO'].astype(int)

                # pegar ids dos funcionarios e remover ja existentes
                query = ( 
                        database.session.query(
                            Funcionario.id_funcionario,
                            Funcionario.cod_funcionario
                    )
                    .filter(Funcionario.cod_empresa_principal == cod_empresa_principal)
                    .filter(Funcionario.id_empresa == empresa.id_empresa)
                )
                df_database = pd.read_sql(query.statement, database.session.bind)
            
                df = pd.merge(
                    df,
                    df_database,
                    how='left',
                    left_on='CODIGO',
                    right_on='cod_funcionario'
                )
                df = df[~df['id_funcionario'].isin(df_database['id_funcionario'])]

                # buscar ids das entidades
                query = ( 
                        database.session.query(
                        Unidade.id_empresa,
                        Unidade.id_unidade,
                        Unidade.cod_unidade,
                        Empresa.cod_empresa
                    )
                    .filter(Unidade.id_empresa == empresa.id_empresa)
                    .filter(Empresa.id_empresa == empresa.id_empresa)
                    .outerjoin(Empresa, Unidade.id_empresa == Empresa.id_empresa)
                )
                df_database = pd.read_sql(query.statement, database.session.bind)

                df = pd.merge(
                    df,
                    df_database,
                    how='left',
                    left_on=['CODIGOEMPRESA', 'CODIGOUNIDADE'],
                    right_on=['cod_empresa', 'cod_unidade']
                )

                # tratar df
                df = df[[
                    'id_empresa',
                    'id_unidade',
                    'CODIGO',
                    'NOME',
                    'CPFFUNCIONARIO',
                    'CODIGOSETOR',
                    'NOMESETOR',
                    'CODIGOCARGO',
                    'NOMECARGO',
                    'SITUACAO'
                ]]
                df.dropna(
                    axis=0,
                    subset=['id_empresa', 'id_unidade'],
                    inplace=True
                )
                df = df.rename(columns={
                    'CODIGO': 'cod_funcionario',
                    'NOME': 'nome_funcionario',
                    'CPFFUNCIONARIO': 'cpf_funcionario',
                    'CODIGOSETOR': 'cod_setor',
                    'NOMESETOR': 'nome_setor',
                    'CODIGOCARGO': 'cod_cargo',
                    'NOMECARGO': 'nome_cargo',
                    'SITUACAO': 'situacao'
                })
                df['cod_empresa_principal'] = cod_empresa_principal
                df['data_inclusao'] = datetime.now(tz=timezone('America/Sao_Paulo'))

                # inserir
                qtd_inseridos = df.to_sql(
                    name=self.__tablename__,
                    con=database.session.bind,
                    if_exists='append',
                    index=False
                )
                database.session.commit()

                total_inseridos = total_inseridos + qtd_inseridos

        return total_inseridos
    

    @classmethod
    def atualizar_funcionarios(
        self,
        cod_empresa_principal: int,
        lista_empresas: list[int]
    ):
        from modules.exporta_dados import (cadastro_funcionarios,
                                           exporta_dados, get_json_configs)

        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        total_inseridos = 0
        for id_empresa in lista_empresas:
            empresa = Empresa.query.get(id_empresa)
            par = cadastro_funcionarios(
                cod_empresa_principal=empresa_principal.cod,
                cod_exporta_dados=credenciais['EXPORTADADOS_CADFUNCIONARIOSEMPRESA_COD'],
                chave=credenciais['EXPORTADADOS_CADFUNCIONARIOSEMPRESA_KEY'],
                empresaTrabalho=empresa.cod_empresa
            )
            df = exporta_dados(parametro=par)

            if not df.empty:
                df['CODIGOEMPRESA'] = df['CODIGOEMPRESA'].astype(int)
                df['CODIGO'] = df['CODIGO'].astype(int)

                query = ( 
                        database.session.query(
                            Funcionario.id_funcionario,
                            Funcionario.cod_funcionario
                    )
                    .filter(Funcionario.cod_empresa_principal == cod_empresa_principal)
                    .filter(Funcionario.id_empresa == empresa.id_empresa)
                )
                df_database = pd.read_sql(query.statement, database.session.bind)
                
                df = pd.merge(
                    df,
                    df_database,
                    how='left',
                    left_on='CODIGO',
                    right_on='cod_funcionario'
                )
                df = df[df['id_funcionario'].isin(df_database['id_funcionario'])]

                # buscar ids das entidades
                query = ( 
                        database.session.query(
                        Unidade.id_empresa,
                        Unidade.id_unidade,
                        Unidade.cod_unidade,
                        Empresa.cod_empresa
                    )
                    .filter(Unidade.cod_empresa_principal == cod_empresa_principal)
                    .filter(Empresa.cod_empresa_principal == cod_empresa_principal)
                    .outerjoin(Empresa, Unidade.id_empresa == Empresa.id_empresa)
                )
                df_database = pd.read_sql(query.statement, database.session.bind)

                df = pd.merge(
                    df,
                    df_database,
                    how='left',
                    left_on=['CODIGOEMPRESA', 'CODIGOUNIDADE'],
                    right_on=['cod_empresa', 'cod_unidade']
                )

                # tratar df
                df = df[[
                    'id_empresa',
                    'id_unidade',
                    'NOME',
                    'CPFFUNCIONARIO',
                    'CODIGOSETOR',
                    'NOMESETOR',
                    'CODIGOCARGO',
                    'NOMECARGO',
                    'SITUACAO'
                ]]
                df.dropna(
                    axis=0,
                    subset=['id_empresa', 'id_unidade'],
                    inplace=True
                )
                df = df.rename(columns={
                    'NOME': 'nome_funcionario',
                    'CPFFUNCIONARIO': 'cpf_funcionario',
                    'CODIGOSETOR': 'cod_setor',
                    'NOMESETOR': 'nome_setor',
                    'CODIGOCARGO': 'cod_cargo',
                    'NOMECARGO': 'nome_cargo',
                    'SITUACAO': 'situacao'
                })
                df['cod_empresa_principal'] = cod_empresa_principal
                
                df = df.to_dict(orient='records')

                database.session.bulk_update_mappings(Funcionario, df)
                database.session.commit()

                total_inseridos = total_inseridos + len(df)

        return total_inseridos


class Exame(database.Model):
    __tablename__ = 'Exame'
    id_exame = database.Column(database.Integer, primary_key=True)
    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    cod_exame = database.Column(database.String(255), nullable=False)
    nome_exame = database.Column(database.String(255), nullable=False)
    
    prazo = database.Column(database.Integer, default=0) # dias
    
    data_inclusao = database.Column(database.DateTime)
    data_alteracao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    alterado_por = database.Column(database.String(50))

    def __repr__(self) -> str:
        return f'<{self.id_exame}> {self.nome_exame}'

    @classmethod
    def buscar_exames(
        self,
        cod_empresa_principal: int,
        id_exame: int,
        cod_exame: str,
        nome: str,
        prazo: int
    ):
        params = [(self.cod_empresa_principal == cod_empresa_principal)]

        if id_exame:
            params.append(self.id_exame == id_exame)
        if cod_exame:
            params.append(self.cod_exame.like(f'%{cod_exame}%'))
        if nome:
            params.append(self.nome_exame.like(f'%{nome}%'))
        if prazo != None:
            params.append(self.prazo == prazo)

        query = (
            database.session.query(self)
            .filter(*params)
            .order_by(self.nome_exame)
        )
        return query


    @classmethod
    def inserir_exames(
        self,
        cod_empresa_principal: int
    ):
        '''
        Carrega todas os Exames no exporta dados da EmpresaPrincipal selecionada

        Insere os exames que ainda nao existem na db
        '''
        from modules.exporta_dados import (exames, exporta_dados,
                                           get_json_configs)


        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        par = exames(
            cod_empresa_principal=empresa_principal.cod,
            cod_exporta_dados=credenciais['EXPORTADADOS_EXAMES_COD'],
            chave=credenciais['EXPORTADADOS_EXAMES_KEY'],
        )
        df = exporta_dados(parametro=par)
        
        if not df.empty:
            exames_db = (
                database.session.query(Exame.cod_exame)
                .filter(Exame.cod_empresa_principal == cod_empresa_principal)
                .all()
            )
            exames_db = [i.cod_exame for i in exames_db]

            df = df[~df['CODIGO'].isin(exames_db)]

            # tratar df
            df = df.replace(to_replace={'': None})
            df = df.rename(columns={
                'CODIGO': 'cod_exame',
                'NOME': 'nome_exame',
            })
            df['cod_empresa_principal'] = cod_empresa_principal
            df['data_inclusao'] = datetime.now(tz=timezone('America/Sao_Paulo'))
            df['incluido_por'] = 'Servidor'

            # inserir
            linhas_inseridas = df.to_sql(
                name=self.__tablename__,
                con=database.session.bind,
                if_exists='append',
                index=False
            )
            database.session.commit()
            
            return linhas_inseridas


    @classmethod
    def atualizar_exames(
        self,
        cod_empresa_principal: int
    ):
        '''
        Carrega todas os Exames no exporta dados da EmpresaPrincipal selecionada

        Atualiza as infos dos exames que ja existem na db
        '''
        from modules.exporta_dados import (exames, exporta_dados,
                                           get_json_configs)


        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        par = exames(
            cod_empresa_principal=empresa_principal.cod,
            cod_exporta_dados=credenciais['EXPORTADADOS_EXAMES_COD'],
            chave=credenciais['EXPORTADADOS_EXAMES_KEY'],
        )
        df = exporta_dados(parametro=par)
        
        if not df.empty:
            exames_db = pd.read_sql(
                sql=(
                    database.session.query(
                        Exame.id_exame,
                        Exame.cod_exame
                    )
                    .filter(Exame.cod_empresa_principal == cod_empresa_principal)
                ).statement,
                con=database.session.bind
            )

            if not exames_db.empty:
                df = pd.merge(
                    df,
                    exames_db,
                    how='right',
                    left_on='CODIGO',
                    right_on='cod_exame'
                )

                # tratar df
                df = df.replace(to_replace={'': None})
                df = df[['id_exame', 'NOME']]
                df = df.rename(columns={'NOME': 'nome_exame'})
                df['data_alteracao'] = datetime.now(tz=timezone('America/Sao_Paulo'))
                df['alterado_por'] = 'Servidor'

                df = df.to_dict(orient='records')

                database.session.bulk_update_mappings(Exame, df)
                database.session.commit()
                
                return len(df)


class Pedido(database.Model):
    __tablename__ = 'Pedido'
    id_ficha = database.Column(database.Integer, primary_key=True)
    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    seq_ficha = database.Column(database.Integer, nullable=False)
    cod_funcionario = database.Column(database.Integer, nullable=False)
    cpf = database.Column(database.String(30))
    nome_funcionario = database.Column(database.String(150))
    data_ficha = database.Column(database.Date, nullable=False)
    cod_tipo_exame = database.Column(database.Integer, database.ForeignKey('TipoExame.cod_tipo_exame'), nullable=False)
    id_prestador = database.Column(database.Integer, database.ForeignKey('Prestador.id_prestador'))
    id_empresa = database.Column(database.Integer, database.ForeignKey('Empresa.id_empresa'), nullable=False)
    id_unidade = database.Column(database.Integer, database.ForeignKey('Unidade.id_unidade'), nullable=False)
    id_status = database.Column(database.Integer, database.ForeignKey('Status.id_status'), default=1, nullable=False)
    id_status_rac = database.Column(database.Integer, database.ForeignKey('StatusRAC.id_status'), default=1, nullable=False)
    prazo = database.Column(database.Integer, default=0)
    prev_liberacao = database.Column(database.Date)
    id_status_lib = database.Column(database.Integer, database.ForeignKey('StatusLiberacao.id_status_lib'), default=1, nullable=False)
    data_recebido = database.Column(database.Date)
    data_comparecimento = database.Column(database.Date)
    obs = database.Column(database.String(255))

    data_inclusao = database.Column(database.DateTime, nullable=False, default=datetime.now(tz=timezone('America/Sao_Paulo')))
    data_alteracao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    alterado_por = database.Column(database.String(50))

    # colunas para a planilha de pedidos
    colunas_planilha = [
        'cod_empresa_principal',
        'seq_ficha',
        'cpf',
        'nome_funcionario',
        'data_ficha',
        'nome_tipo_exame',
        'nome_prestador',
        'razao_social',
        'nome_unidade',
        'nome_status',
        'nome_status_rac',
        'prazo',
        'prev_liberacao',
        'nome_status_lib',
        'cod_funcionario',
        'cod_tipo_exame',
        'cod_prestador',
        'cod_empresa',
        'cod_unidade',
        'id_status_lib',
        'data_inclusao',
        'data_alteracao',
        'incluido_por',
        'alterado_por',
        'id_ficha',
        'id_status',
        'id_status_rac',
        'data_recebido',
        'data_comparecimento',
        'obs'
    ]

    # colunas para a tabela enviada no email
    colunas_tab_email = [
        'seq_ficha',
        'cpf',
        'nome_funcionario',
        'data_ficha',
        'nome_tipo_exame',
        'nome_prestador',
        'razao_social',
        'nome_status_lib'
    ]

    colunas_tab_email2 = [
        'Seq. Ficha',
        'CPF',
        'Nome Funcionário',
        'Data Ficha',
        'Tipo Exame',
        'Prestador',
        'Empresa',
        'Status'
    ]

    @classmethod
    def buscar_pedidos(
        self,
        pesquisa_geral:  int | None = None,
        cod_empresa_principal: int | None = None,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        id_status: int | None = None,
        id_status_rac: int | None = None,
        id_tag: int | None = None,
        id_empresa: int | None = None,
        id_unidade: int | None = None,
        id_prestador: int | None = None,
        seq_ficha: int | None = None,
        nome_funcionario: str | None = None,
        obs: str | None = None
    ):
        '''
        Realiza query filtrada pelos parametros passados

        Retorna BaseQuery com os pedidos filtrados ou com todos os pedidos
        '''
        models = [
            (Pedido.id_ficha),
            (Pedido.cod_empresa_principal), (Pedido.seq_ficha), (Pedido.data_ficha),
            (Pedido.prazo), (Pedido.prev_liberacao), (Pedido.data_recebido), (Pedido.data_comparecimento),
            (Pedido.obs), (Pedido.data_inclusao), (Pedido.data_alteracao),
            (Pedido.incluido_por), (Pedido.alterado_por), (Pedido.cpf),
            (Pedido.cod_funcionario), (Pedido.nome_funcionario),
            (TipoExame.nome_tipo_exame), (TipoExame.cod_tipo_exame),
            (Empresa.cod_empresa), (Empresa.razao_social),
            (Unidade.cod_unidade), (Unidade.nome_unidade),
            (Prestador.cod_prestador), (Prestador.nome_prestador),
            (Pedido.id_status), (Status.nome_status),
            (Pedido.id_status_rac), (StatusRAC.nome_status.label('nome_status_rac')),
            (StatusLiberacao.id_status_lib), (StatusLiberacao.nome_status_lib), (StatusLiberacao.cor_tag)
        ]

        joins = [
            (Empresa, Pedido.id_empresa == Empresa.id_empresa),
            (Unidade, Pedido.id_unidade == Unidade.id_unidade),
            (Prestador, Pedido.id_prestador == Prestador.id_prestador),
            (TipoExame, Pedido.cod_tipo_exame == TipoExame.cod_tipo_exame),
            (Status, Pedido.id_status == Status.id_status),
            (StatusRAC, Pedido.id_status_rac == StatusRAC.id_status),
            (StatusLiberacao, Pedido.id_status_lib == StatusLiberacao.id_status_lib)
        ]
        
        filtros = []
        if cod_empresa_principal:
            filtros.append(self.cod_empresa_principal == cod_empresa_principal)
        if data_inicio:
            filtros.append(self.data_ficha >= data_inicio)
        if data_fim:
            filtros.append(self.data_ficha <= data_fim)
        if id_empresa:
            filtros.append(self.id_empresa == id_empresa)
        if id_unidade:
            filtros.append(self.id_unidade == id_unidade)
        if id_prestador != None:
            if id_prestador == 0:
                filtros.append(self.id_prestador == None)
            else:
                filtros.append(self.id_prestador == id_prestador)
        if nome_funcionario:
            filtros.append(self.nome_funcionario.like(f'%{nome_funcionario}%'))
        if seq_ficha:
            filtros.append(self.seq_ficha == seq_ficha)
        if id_status:
            filtros.append(self.id_status == id_status)
        if id_status_rac:
            filtros.append(self.id_status_rac == id_status_rac)
        if obs:
            filtros.append(self.obs.like(f'%{obs}%'))
        if id_tag:
            filtros.append(self.id_status_lib == id_tag)
        
        # se nao for pesquisa geral, usar grupos do usuario atual
        if not pesquisa_geral:
            subquery_grupos = [grupo.id_grupo for grupo in current_user.grupo]

            joins.append((grupo_empresa, self.id_empresa == grupo_empresa.columns.id_empresa))
            joins.append((grupo_prestador, self.id_prestador == grupo_prestador.columns.id_prestador))
            filtros.append((grupo_prestador.columns.id_grupo.in_(subquery_grupos)))
            filtros.append((grupo_empresa.columns.id_grupo.in_(subquery_grupos)))

        query = (
            database.session.query(*models)
            .filter(*filtros)
            .outerjoin(*joins)
            .order_by(Pedido.data_ficha.desc(), Pedido.nome_funcionario)
        )
        
        return query

    @classmethod
    def inserir_pedidos(
        self,
        cod_empresa_principal: int,
        dataInicio: str,
        dataFim: str
    ):
        from modules.exporta_dados import (exporta_dados, get_json_configs,
                                           pedido_exame)

        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        empresas = Empresa.query.filter_by(cod_empresa_principal=cod_empresa_principal)

        total_inseridos = 0
        for empresa in empresas:
            print(empresa)

            par = pedido_exame(
                empresa=empresa.cod_empresa,
                cod_exporta_dados=credenciais['EXPORTADADOS_PEDIDOEXAME_COD'],
                chave=credenciais['EXPORTADADOS_PEDIDOEXAME_KEY'],
                dataInicio=dataInicio,
                dataFim=dataFim
            )
            
            df_exporta_dados = exporta_dados(parametro=par)
            
            if not df_exporta_dados.empty:
                df_exporta_dados = df_exporta_dados.replace({'': None})

                # validar pedidos duplicados
                pedidos_database = [
                    p.seq_ficha for p in
                    database.session.query(Pedido.seq_ficha)
                    .filter(Pedido.id_empresa == empresa.id_empresa)
                    .all()
                ]
                df_exporta_dados['SEQUENCIAFICHA'] = df_exporta_dados['SEQUENCIAFICHA'].astype(int)
                df_exporta_dados = df_exporta_dados[~df_exporta_dados['SEQUENCIAFICHA'].isin(pedidos_database)]

                if not df_exporta_dados.empty:
                    # pegar id do Exame e prazo
                    df_database = pd.read_sql(
                        sql=(
                            database.session.query(
                                Exame.id_exame,
                                Exame.cod_exame,
                                Exame.prazo
                            )
                            .filter(Exame.cod_empresa_principal == cod_empresa_principal)
                            .statement
                        ),
                        con=database.session.bind
                    )

                    df_exporta_dados = pd.merge(
                        df_exporta_dados,
                        df_database,
                        how='left',
                        left_on='CODIGOINTERNOEXAME',
                        right_on='cod_exame'
                    ) 

                    df_exporta_dados['id_empresa'] = empresa.id_empresa 

                    # pegar id unidade
                    df_database = pd.read_sql(
                        sql=(
                            database.session.query(
                                Unidade.id_unidade,
                                Unidade.cod_unidade
                            )
                            .filter(Unidade.id_empresa == empresa.id_empresa)
                            .statement
                        ),
                        con=database.session.bind
                    )

                    df_exporta_dados = pd.merge(
                        df_exporta_dados,
                        df_database,
                        how='left',
                        left_on='CODIGOUNIDADE',
                        right_on='cod_unidade'
                    ) 

                    # pegar id do Prestador
                    df_database = pd.read_sql(
                        sql=(
                            database.session.query(
                                Prestador.id_prestador,
                                Prestador.cod_prestador
                            )
                            .filter(Prestador.cod_empresa_principal == cod_empresa_principal)
                            .statement
                        ),
                        con=database.session.bind
                    )
                    # adicionar uma linha Nan no df database para nao travar o merge quando o prestador \
                    # estiver vazio no df_exporta_dados
                    df_database = pd.concat(
                        [df_database, pd.DataFrame({'id_prestador': [None], 'cod_prestador': [None]})],
                        axis=0,
                        ignore_index=True
                    )
                    df_database = df_database.astype('Int32')

                    df_exporta_dados['CODIGOPRESTADOR'] = df_exporta_dados['CODIGOPRESTADOR'].astype('Int32')
                    df_exporta_dados = pd.merge(
                        df_exporta_dados,
                        df_database,
                        how='left',
                        left_on='CODIGOPRESTADOR',
                        right_on='cod_prestador'
                    ) 

                    # pegar prestadores dos exames com menor prazo
                    # geralmente e o clinico ou outro exame do prestador que \
                    # pegou o ASO por ultimo
                    df_exporta_dados['prazo'] = df_exporta_dados['prazo'].fillna(0).astype(int)
                    df_prestadores = df_exporta_dados.sort_values(by='prazo', ascending=True).drop_duplicates('SEQUENCIAFICHA')
                    df_prestadores = df_prestadores[['SEQUENCIAFICHA', 'id_prestador']]
                    df_prestadores.rename(columns={'id_prestador': 'id_prestador_final'}, inplace=True)

                    # manter prazo maior de cada pedido
                    df_exporta_dados.sort_values(by='prazo', ascending=False, inplace=True)
                    df_exporta_dados.drop_duplicates('SEQUENCIAFICHA', inplace=True)

                    df_exporta_dados = pd.merge(
                        df_exporta_dados,
                        df_prestadores,
                        how='left',
                        on='SEQUENCIAFICHA'
                    )

                    df_exporta_dados.drop(labels='id_prestador', axis=1, inplace=True)
                    df_exporta_dados.rename(columns={'id_prestador_final': 'id_prestador'}, inplace=True)


                    # inserir prev de liberacao;
                    cal = Brazil() # usar workalendar
                    df_exporta_dados['DATAFICHA'] = pd.to_datetime(df_exporta_dados['DATAFICHA'], dayfirst=True).dt.date
                    df_exporta_dados['prev_liberacao'] = list(
                        map(
                            cal.add_working_days, # adicionar dias uteis
                            df_exporta_dados['DATAFICHA'].values,
                            df_exporta_dados['prazo'].values
                        )
                    )

                    # calcular tag de previsao de liberacao
                    df_exporta_dados['id_status_lib'] = 1
                    df_exporta_dados['id_status_lib'] = list(
                        map(
                            self.calcular_tag_prev_lib,
                            df_exporta_dados['prev_liberacao']
                        )
                    )
                
                    # tratar colunas
                    for col in ['SEQUENCIAFICHA', 'CODIGOFUNCIONARIO', 'CODIGOTIPOEXAME', 'CODIGOEMPRESA']:
                        df_exporta_dados[col] = df_exporta_dados[col].astype(int)
                    
                    df_exporta_dados['CPFFUNCIONARIO'] = df_exporta_dados['CPFFUNCIONARIO'].astype('string')
                    
                    df_exporta_dados['id_status'] = int(1)
                    df_exporta_dados['data_inclusao'] = datetime.now(tz=timezone('America/Sao_Paulo'))
                    df_exporta_dados['incluido_por'] = 'Servidor'
                    df_exporta_dados['cod_empresa_principal'] = cod_empresa_principal

                    df_exporta_dados = df_exporta_dados.rename(columns={
                        'SEQUENCIAFICHA': 'seq_ficha',
                        'CODIGOFUNCIONARIO': 'cod_funcionario',
                        'CPFFUNCIONARIO': 'cpf',
                        'NOMEFUNCIONARIO': 'nome_funcionario',
                        'DATAFICHA': 'data_ficha',
                        'CODIGOTIPOEXAME': 'cod_tipo_exame',
                        'CODIGOPRESTADOR': 'cod_prestador',
                        'CODIGOEMPRESA': 'cod_empresa',
                        'CODIGOUNIDADE': 'cod_unidade'
                    })

                    # pegar nomes das colunas da tabela 
                    cols_db = [col.name for col in inspect(self).c]
                    # criar lista de colunas unicas compativeis com a tabela
                    cols_df = list(dict.fromkeys([col for col in df_exporta_dados.columns if col in cols_db]))
                    # selecionar apenas as colunas q constam na tabela
                    df_exporta_dados = df_exporta_dados[cols_df]

                    df_exporta_dados.dropna(
                        axis=0,
                        subset=['id_empresa', 'id_unidade'],
                        inplace=True
                    )
                    
                    qtd_inseridos = df_exporta_dados.to_sql(name=self.__tablename__, con=database.session.bind, if_exists='append', index=False)
                    database.session.commit()

                    total_inseridos = total_inseridos + qtd_inseridos
            
        return total_inseridos


    @staticmethod
    def calcular_tag_prev_lib(data_prev: pd.Timestamp) -> int:
        '''
            Calcula o status_lib baseado na data de previsao de liberacao recebida

            Retorna id do status lib
        '''
        
        hoje = datetime.now().date()

        datas_solicitar = (
            [hoje] +
            [hoje + timedelta(days=i) for i in range(1, 3)]
        ) # folga de dois dias p solicitar

        if not data_prev:
            return 1 # Sem previsao
        elif data_prev < hoje:
            return 5 # Atrasado
        elif data_prev in datas_solicitar:
            return 3 # Solicitar
        elif data_prev > hoje:
            return 4 # Em dia
        else:
            return 1 # Sem previsao
    

    @classmethod
    def atualizar_tags_prev_liberacao(self):
        '''
        Atualiza todas as tags de previsao de liberacao \
        de acordo com as condicoes:

        1=Sem previsao, 2=OK, 3=Solicitar, 4=Em dia, 5=Atrasado

        Retorna num de linhas afetadas.
        '''
        hoje = datetime.now().date()

        datas_solicitar = (
            [hoje] +
            [hoje + timedelta(days=i) for i in range(1, 3)]
        ) # folga de dois dias p solicitar

        finaliza_processo = [
            int(status.id_status)
            for status in Status.query.filter_by(finaliza_processo=True)
        ]
        
        parametros = [
            (Pedido.prev_liberacao == None, 1),
            (Pedido.prev_liberacao < hoje, 5),
            (Pedido.prev_liberacao > hoje, 4),
            (Pedido.prev_liberacao.in_(datas_solicitar), 3),
            (Pedido.id_status.in_(finaliza_processo), 2)
        ]

        linhas_afetadas = 0
        # afeta as mesmas linhas varias vezes, \
        # pode gerar numero maior do que o total de linhas na tabela

        for par, tag in parametros:
            q = database.session.execute(
                update(Pedido).
                where(par).
                values(id_status_lib=tag)
            )
            database.session.commit()

            linhas_afetadas = linhas_afetadas + q.rowcount
        
        return linhas_afetadas

    @classmethod
    def atualizar_pedidos(
        self,
        cod_empresa_principal: int,
        dataInicio: str,
        dataFim: str
    ):
        from modules.exporta_dados import (exporta_dados, get_json_configs,
                                           pedido_exame)

        empresa_principal = EmpresaPrincipal.query.get(cod_empresa_principal)
        credenciais = get_json_configs(empresa_principal.configs_exporta_dados)

        empresas = Empresa.query.filter_by(cod_empresa_principal=cod_empresa_principal)

        total_inseridos = 0
        for empresa in empresas:
            print(empresa)

            par = pedido_exame(
                empresa=empresa.cod_empresa,
                cod_exporta_dados=credenciais['EXPORTADADOS_PEDIDOEXAME_COD'],
                chave=credenciais['EXPORTADADOS_PEDIDOEXAME_KEY'],
                dataInicio=dataInicio,
                dataFim=dataFim
            )
            
            tentativas = 4
            for i in range(tentativas):
                try:
                    df_exporta_dados = exporta_dados(parametro=par)
                    break
                except:
                    continue
            
            if not df_exporta_dados.empty:
                df_exporta_dados = df_exporta_dados.replace({'': None})

                pedidos_database = [
                    p.seq_ficha for p in
                    database.session.query(Pedido.seq_ficha)
                    .filter(Pedido.id_empresa == empresa.id_empresa)
                    .all()
                ]
                df_exporta_dados['SEQUENCIAFICHA'] = df_exporta_dados['SEQUENCIAFICHA'].astype(int)
                df_exporta_dados = df_exporta_dados[df_exporta_dados['SEQUENCIAFICHA'].isin(pedidos_database)]

                if not df_exporta_dados.empty:
                    # pegar id da ficha
                    df_database = pd.read_sql(
                        sql=(
                            database.session.query(
                                Pedido.id_ficha,
                                Pedido.seq_ficha,
                                Pedido.id_status,
                                Pedido.id_status_lib,
                                Pedido.data_ficha
                            )
                            .filter(Pedido.id_empresa == empresa.id_empresa)
                            .statement
                        ),
                        con=database.session.bind
                    )
                    df_exporta_dados = pd.merge(
                        df_exporta_dados,
                        df_database,
                        how='left',
                        left_on='SEQUENCIAFICHA',
                        right_on='seq_ficha'
                    )

                    # pegar id do Exame e prazo
                    df_database = pd.read_sql(
                        sql=(
                            database.session.query(
                                Exame.id_exame,
                                Exame.cod_exame,
                                Exame.prazo
                            )
                            .filter(Exame.cod_empresa_principal == cod_empresa_principal)
                            .statement
                        ),
                        con=database.session.bind
                    )
                    df_exporta_dados = pd.merge(
                        df_exporta_dados,
                        df_database,
                        how='left',
                        left_on='CODIGOINTERNOEXAME',
                        right_on='cod_exame'
                    ) 

                    df_exporta_dados['id_empresa'] = empresa.id_empresa 

                    # pegar id unidade
                    df_database = pd.read_sql(
                        sql=(
                            database.session.query(
                                Unidade.id_unidade,
                                Unidade.cod_unidade
                            )
                            .filter(Unidade.id_empresa == empresa.id_empresa)
                            .statement
                        ),
                        con=database.session.bind
                    )
                    df_exporta_dados = pd.merge(
                        df_exporta_dados,
                        df_database,
                        how='left',
                        left_on='CODIGOUNIDADE',
                        right_on='cod_unidade'
                    ) 

                    # pegar id do Prestador
                    df_database = pd.read_sql(
                        sql=(
                            database.session.query(
                                Prestador.id_prestador,
                                Prestador.cod_prestador
                            )
                            .filter(Prestador.cod_empresa_principal == cod_empresa_principal)
                            .statement
                        ),
                        con=database.session.bind
                    )
                    # adicionar uma linha Nan no df database para nao travar o merge quando o prestador \
                    # estiver vazio no df_exporta_dados
                    df_database = pd.concat(
                        [df_database, pd.DataFrame({'id_prestador': [None], 'cod_prestador': [None]})],
                        axis=0,
                        ignore_index=True
                    )
                    df_database = df_database.astype('Int32')
                    df_exporta_dados['CODIGOPRESTADOR'] = df_exporta_dados['CODIGOPRESTADOR'].astype('Int32')
                    df_exporta_dados = pd.merge(
                        df_exporta_dados,
                        df_database,
                        how='left',
                        left_on='CODIGOPRESTADOR',
                        right_on='cod_prestador'
                    ) 

                    # pegar prestadores dos exames com menor prazo
                    # geralmente e o clinico ou outro exame do prestador que \
                    # pegou o ASO por ultimo
                    df_exporta_dados['prazo'] = df_exporta_dados['prazo'].fillna(0).astype(int)
                    df_prestadores = df_exporta_dados.sort_values(by='prazo', ascending=True).drop_duplicates('SEQUENCIAFICHA')
                    df_prestadores = df_prestadores[['SEQUENCIAFICHA', 'id_prestador']]
                    df_prestadores.rename(columns={'id_prestador': 'id_prestador_final'}, inplace=True)

                    # manter prazo maior de cada pedido
                    df_exporta_dados.sort_values(by='prazo', ascending=False, inplace=True)
                    df_exporta_dados.drop_duplicates('SEQUENCIAFICHA', inplace=True)

                    df_exporta_dados = pd.merge(
                        df_exporta_dados,
                        df_prestadores,
                        how='left',
                        on='SEQUENCIAFICHA'
                    )

                    df_exporta_dados.drop(labels='id_prestador', axis=1, inplace=True)
                    df_exporta_dados.rename(columns={'id_prestador_final': 'id_prestador'}, inplace=True)


                    # inserir prev de liberacao;
                    cal = Brazil() # usar workalendar
                    df_exporta_dados['DATAFICHA'] = pd.to_datetime(df_exporta_dados['DATAFICHA'], dayfirst=True).dt.date
                    df_exporta_dados['prev_liberacao'] = list(
                        map(
                            cal.add_working_days, # adicionar dias uteis
                            df_exporta_dados['DATAFICHA'].values,
                            df_exporta_dados['prazo'].values
                        )
                    )

                    # calcular nova tag de previsao de liberacao
                    df_exporta_dados = df_exporta_dados.rename(columns={'data_ficha': 'data_ficha_antiga'})
                    df_exporta_dados['atualizar_tag'] = df_exporta_dados['DATAFICHA'].ne(df_exporta_dados['data_ficha_antiga'])
                    df_exporta_dados['id_status_lib2'] = list(
                        map(
                            self.calcular_tag_prev_lib2,
                            df_exporta_dados['atualizar_tag'],
                            df_exporta_dados['id_status'],
                            df_exporta_dados['prev_liberacao'],
                            df_exporta_dados['id_status_lib']
                        )
                    )

                    # tratar colunas
                    for col in ['SEQUENCIAFICHA', 'CODIGOFUNCIONARIO', 'CODIGOTIPOEXAME', 'CODIGOEMPRESA']:
                        df_exporta_dados[col] = df_exporta_dados[col].astype(int)
                    
                    df_exporta_dados['CPFFUNCIONARIO'] = df_exporta_dados['CPFFUNCIONARIO'].astype('string')

                    df_exporta_dados = df_exporta_dados.rename(columns={
                        'SEQUENCIAFICHA': 'seq_ficha',
                        'CODIGOFUNCIONARIO': 'cod_funcionario',
                        'CPFFUNCIONARIO': 'cpf',
                        'NOMEFUNCIONARIO': 'nome_funcionario',
                        'DATAFICHA': 'data_ficha',
                        'CODIGOTIPOEXAME': 'cod_tipo_exame',
                        'CODIGOPRESTADOR': 'cod_prestador',
                        'CODIGOEMPRESA': 'cod_empresa',
                        'CODIGOUNIDADE': 'cod_unidade'
                    })

                    df_exporta_dados = df_exporta_dados[[
                        'id_ficha',
                        'cod_funcionario',
                        'cpf',
                        'nome_funcionario',
                        'data_ficha',
                        'cod_tipo_exame',
                        'id_prestador',
                        'id_unidade',
                        'prazo',
                        'prev_liberacao',
                        'id_status_lib2'
                    ]]

                    df_exporta_dados = df_exporta_dados.rename(columns={'id_status_lib2': 'id_status_lib'})

                    df_exporta_dados['data_alteracao'] = datetime.now(tz=timezone('America/Sao_Paulo'))
                    df_exporta_dados['alterado_por'] = 'Servidor'

                    df_exporta_dados.dropna(
                        axis=0,
                        subset=['id_ficha', 'id_unidade'],
                        inplace=True
                    )

                    df_exporta_dados = df_exporta_dados.replace({np.nan: None})
                    df_exporta_dados = df_exporta_dados.to_dict(orient='records')
                    database.session.bulk_update_mappings(Pedido, df_exporta_dados)
                    database.session.commit()

                    total_inseridos = total_inseridos + len(df_exporta_dados)

        return total_inseridos

    @staticmethod
    def calcular_tag_prev_lib2(
        atualizar_tag: bool,
        id_status: int,
        data_prev: pd.Timestamp,
        id_status_lib: int
    ) -> int:
        """Calcula o id_status_lib baseado no Status atual e data_prev. \
        Se o Status atual for Recebido, nao altera id_status_lib.

        Usado junto com a funcao de atualizar_pedidos

        Returns:
            int: id_status_lib
        """
        if atualizar_tag:
            # se nao for "Recebido", calcular
            if id_status != 2:
                hoje = datetime.now().date()

                datas_solicitar = (
                    [hoje] +
                    [hoje + timedelta(days=i) for i in range(1, 3)]
                ) # folga de dois dias p solicitar

                if not data_prev:
                    return 1 # Sem previsao
                elif data_prev < hoje:
                    return 5 # Atrasado
                elif data_prev in datas_solicitar:
                    return 3 # Solicitar
                elif data_prev > hoje:
                    return 4 # Em dia
                else:
                    return 1 # Sem previsao
            # se for "Recebido", manter mesma tag
            else:
                return id_status_lib
        else:
            return id_status_lib

