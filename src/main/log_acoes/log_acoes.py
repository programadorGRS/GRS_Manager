from datetime import date, datetime

import jwt
from flask_login import current_user

from src import TIMEZONE_SAO_PAULO, app, database

from ..usuario.usuario import Usuario


class LogAcoes(database.Model):
    __tablename__ = 'LogAcoes'
    id_log = database.Column(database.Integer, primary_key=True)
    id_usuario = database.Column(database.Integer, nullable=False)
    username = database.Column(database.String(255), nullable=False)
    tabela = database.Column(database.String(50), nullable=False)
    acao = database.Column(database.String(255), nullable=False)
    # cod ou id do registro que o user alterou ex(cod_empresa, cod_prestador etc)
    id_registro = database.Column(database.Integer)
    # nome do registro alterado ex(nome_funcionario, nome_prestador, nome_empresa etc)
    nome_registro = database.Column(database.String(255))
    obs = database.Column(database.String(1000)) # tamanho do texto passa de 500 chars em alguns casos
    data = database.Column(database.Date, nullable=False, default=date.today())
    hora = database.Column(database.Time, nullable=False, default=datetime.now(tz=TIMEZONE_SAO_PAULO).time())


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
