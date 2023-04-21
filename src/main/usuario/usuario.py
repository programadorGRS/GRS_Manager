import secrets
from datetime import datetime

from flask_login import UserMixin, current_user
from pytz import timezone

from src import bcrypt, database

from ..grupo.grupo import grupo_usuario


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
    foto_perfil = database.Column(database.String(255))
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
    