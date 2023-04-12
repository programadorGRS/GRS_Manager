from datetime import datetime

from flask import request
from pytz import timezone

from src import database


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
