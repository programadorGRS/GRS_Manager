import base64
import json
import os
from calendar import monthcalendar, setfirstweekday
from datetime import datetime
from functools import wraps
from urllib.parse import urljoin, urlparse
from zipfile import ZIP_DEFLATED, ZipFile

import jwt
import pandas as pd
from flask import flash, redirect, request, url_for
from flask_login import current_user

from src import app


def admin_required(funcao):
    '''
    Decore uma route com isto para checar se o usuario atual é do tipo "Administrador"

    Se não for retorna mensagem de acesso negado

    Criado por: https://stackoverflow.com/questions/52285012/does-flask-login-support-roles
    '''
    @wraps(funcao)
    def wrap(*args, **kwargs):
        # se o tipo de usuario for Admin
        if current_user.tipo_usuario == 1:
            return funcao(*args, **kwargs)
        else:
            flash('Você não tem permissão para executar esta ação', 'alert-danger')
            return redirect(url_for('home'))
    return wrap


def token_required(funcao):
    '''
    Valida token a partir do argumento "token" no request
    '''
    @wraps(funcao)
    def wrap(*args, **kwargs):
        token = request.args.get(key='token', type=str)
        if token:
            # validar token
            try:
                data = jwt.decode(
                    jwt=token,
                    key=app.config['SECRET_KEY'],
                    algorithms=['HS256']
                )
            except:
                return {"message": "Token invalido"}, 200

            # validar expiracao
            timestamp_now = int(datetime.utcnow().timestamp())
            if timestamp_now < data['expires']:
                return funcao(*args, **kwargs)
            else:
                return {"message": "Token expirado"}, 200
        else:
            return {"message": "Providencie um token"}, 200
    return wrap


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def zipar_arquivos(
    caminhos_arquivos: list[str],
    caminho_pasta_zip: str
):
    '''
    Zipa os arquivos passados e descarta os arquivos originais.

    caminhos_arquivos:  caminho completo de cada arquivo a ser zipado
    caminho_pasta_zip: caminho onde a pasta sera criada

    Retorna caminho da pasta Zipada
    '''
    with ZipFile(caminho_pasta_zip, mode='w', compression=ZIP_DEFLATED) as z:
        for arqv in caminhos_arquivos:
            z.write(
                filename=arqv, # caminho completo
                arcname=arqv.split('/')[-1], # apenas nome do arqv
            )

    # descartar arquivos originais
    for arqv in caminhos_arquivos:
        os.remove(arqv)
    
    return caminho_pasta_zip


def semana_do_mes(timestamp: pd.Timestamp) -> int:
    '''
    Recebe data em pd.Timestamp

    Retorna int correspondente da semana do mês  
    '''
    ano = timestamp.year
    mes = timestamp.month
    dia = timestamp.day
    # primeiro dia da semana = Domingo
    setfirstweekday(6)
    calendario = monthcalendar(ano, mes)
    for num_semana, semana in enumerate(calendario):
        if dia in semana:
            return num_semana + 1


def tratar_emails(emails_str: str):
    try:
        emails_str = emails_str.replace(',', ';')
        emails_str = emails_str.replace(' ', '')
        emails_str = emails_str.lower()
        emails_str = emails_str.split(';')

        for indice, email in enumerate(emails_str):
            if not email:
                emails_str.pop(indice)
        emails_str = ';'.join(emails_str)
        return emails_str
    except:
        return emails_str


def get_json_configs(json_path: str, encoding: str = 'iso-8859-1') -> dict:
    """Lê o arquivo json indicado e retorna um dicionario do conteudo

    Args:
        json_path (str): caminho absoluto do json
        encoding (str, optional): Defaults to 'iso-8859-1'.

    Returns:
        dict: dicionario com conteudo do json
    """
    with open(json_path, mode='r', encoding=encoding) as f:
        return dict(json.loads(f.read()))


def get_image_file_as_base64_data(img_path: str) -> str:
    with open(img_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode()


def get_data_from_form(
    data: dict,
    ignore_keys: list | None = None,
    ignore_vals: list | None = None
) -> dict:
    """
        Args:
            ignore_keys (list | None, optional): keys to ignore. Ignores 'csrf_token'  by default.
            ignore_vals (list | None, optional): values to ignore. Ignores None and empty strings '' by default.
    """
    ignore_v = [None, '']
    if ignore_vals:
        ignore_v.extend(ignore_vals)
    
    ignore_k = ['csrf_token']
    if ignore_keys:
        ignore_k.extend(ignore_keys)

    new_data = {}
    for key, val in data.items():
        if val not in ignore_v:
            if key not in ignore_k:
                new_data[key] = val

    return new_data

