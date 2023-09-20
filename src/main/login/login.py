from datetime import datetime

from flask import request
from pytz import timezone

from src.extensions import database as db


class Login(db.Model):
    """
    Tentativas de Login
    """

    __tablename__ = "Login"
    id_log = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    tela = db.Column(db.String(50), nullable=False)
    date_time = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now(tz=timezone("America/Sao_Paulo")),
    )
    ip = db.Column(db.String(50), nullable=False)
    obs = db.Column(db.String(500))

    @classmethod
    def get_ip(cls) -> str:
        """
        Retorna ip do usuario atual HTTP_X_FORWARDED_FOR ou REMOTE_ADDR
        """
        remote_addr = request.remote_addr
        remote_addr_env = request.environ.get("REMOTE_ADDR")
        http_x_fowarded = request.environ.get("HTTP_X_FORWARDED_FOR")

        for val in (remote_addr, remote_addr_env, http_x_fowarded):
            if val:
                return val

        return "127.0.0.1"

    @classmethod
    def log_attempt(
        cls, username: str, tela: str, ip: str, obs: str | None = None
    ) -> None:
        """
        Registra tentativa de login
        """
        log = Login(username=username, tela=tela, ip=ip, obs=obs)
        db.session.add(log)  # type: ignore
        db.session.commit()  # type: ignore
        return None
