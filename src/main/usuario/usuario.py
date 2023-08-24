import secrets
from datetime import datetime

from flask_login import UserMixin, current_user

from src import TIMEZONE_SAO_PAULO
from src.extensions import bcrypt
from src.extensions import database as db

from ..grupo.grupo import grupo_usuario


# UserMixin para carregar o usuario atraves dessa tabela
class Usuario(db.Model, UserMixin):
    """
    Tabela de Usuários

    OBS: id_cookie serve para resetar todas as sessoes do usuario.
    Ele deve ser mudado ao mudar a senha para que todos os cookies do usuario
    sejam resetados e as sessoes sejam deslogadas
    """

    __tablename__ = "Usuario"

    id_usuario = db.Column(db.Integer, primary_key=True)
    id_cookie = db.Column(db.String(255), nullable=False, unique=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    nome_usuario = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    celular = db.Column(db.String(20))
    telefone = db.Column(db.String(20))
    senha = db.Column(db.String(300), nullable=False)
    otp = db.Column(db.String(300))  # one time password
    chave_api = db.Column(db.String(300))
    tipo_usuario = db.Column(
        db.Integer, db.ForeignKey("TipoUsuario.id_role"), default=2, nullable=False
    )
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    foto_perfil = db.Column(db.String(255))

    ultimo_login = db.Column(db.DateTime)

    data_inclusao = db.Column(db.DateTime)
    incluido_por = db.Column(db.String(50))
    data_alteracao = db.Column(db.DateTime)
    alterado_por = db.Column(db.String(50))

    grupo = db.relationship(
        "Grupo", secondary=grupo_usuario, backref="usuarios", lazy=True
    )  # many to many

    def __repr__(self):
        return f"{self.id_usuario} - {self.username}"

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
        cls,
        username: str,
        nome_usuario: str,
        email: str,
        senha: str,
        tipo_usuario: int = 2,
        data_inclusao: datetime = datetime.now(TIMEZONE_SAO_PAULO),
        incluido_por: str = "Servidor",
        telefone: str | None = None,
        celular: str | None = None,
    ):
        """
        Cria um Usuario com a senha ja criptografada e adiciona da db
        """
        # criptografar senha
        senha_cript = bcrypt.generate_password_hash(senha).decode("utf-8")

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
            incluido_por=incluido_por,
        )

        db.session.add(usuario)  # type: ignore
        db.session.commit()  # type: ignore

        return usuario

    @classmethod
    def update_ultimo_login(cls):
        current_user.ultimo_login = datetime.now(TIMEZONE_SAO_PAULO)
        db.session.commit()  # type: ignore
        return None
