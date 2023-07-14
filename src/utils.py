import base64
import json
import os
from calendar import monthcalendar, setfirstweekday
from datetime import date, datetime, timedelta
from functools import wraps
from sys import getsizeof
from urllib.parse import urljoin, urlparse
from zipfile import ZIP_DEFLATED, ZipFile

import jwt
import pandas as pd
from flask import flash, redirect, request, url_for
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import Field

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
                arcname=arqv.split('/')[-1] if os.name == 'posix' else arqv.split('\\')[-1], # apenas nome do arqv
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


def tratar_emails(email_str: str) -> str:
    '''
        Itera sobre os Emails e remove os vazios.

        Substitui separadores de vírgula por ponto e vírgula.

        Raises:
            ValueError: se email_str não for um string.
    '''
    # TODO: isso é necessário?
    if not isinstance(email_str, str):
        raise ValueError(f'email_str must be of type str, not {email_str.__class__.__name__}')

    email_str = email_str.replace(',', ';')
    email_str = email_str.replace(' ', '')
    email_str = email_str.lower()

    email_list = email_str.split(';')
    email_list = [email for email in email_list if email]

    return ';'.join(email_list)


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

def get_data_from_args(prev_form: FlaskForm, data: dict):
    DATE_FORMAT = '%Y-%m-%d'

    ignore_v = [None, '']

    new_data = {}

    for key, value in data.items():
        if value in ignore_v:
            continue
        if key not in prev_form._fields.keys():
            continue

        field: Field = getattr(prev_form, key)
        match field.type:
            case 'SelectField':
                try:
                    new_data[key] = int(value)
                except ValueError:
                    new_data[key] = value
            case 'DateField':
                new_data[key] = datetime.strptime(value, DATE_FORMAT).date()
            case 'IntegerField':
                new_data[key] = int(value)
            case _:
                new_data[key] = value

    return new_data

def get_pagination_url_args(data: dict):
    pagination_url_args = data.copy()
    if 'page' in pagination_url_args.keys():
        pagination_url_args.pop('page')
    return pagination_url_args

def gerar_datas(
    data_inicio: date,
    data_fim: date,
    passo_dias: int
) -> list[tuple[date, date]]:
    '''
        gera lista de tuplas [(data_inicio, data_fim)] baseada nos argumentos
    '''
    datas_inicio = []
    datas_fim = []

    while data_inicio < data_fim:
        datas_inicio.append(data_inicio)
        data_inicio = (data_inicio + timedelta(days=passo_dias + 1))

    for dt in datas_inicio:
        dt_fim = dt + timedelta(days=passo_dias)

        if dt_fim <= data_fim:
            datas_fim.append(dt_fim)
        else:
            datas_fim.append(data_fim)

    return list(zip(datas_inicio, datas_fim))


def validate_email_fields(
    form: FlaskForm,
    field_name_pattern: str = '_emails',
    field_type: str = 'StringField',
    *args,
    **kwargs
):
    validated = FlaskForm.validate(form, *args, **kwargs)

    if not validated:
        return False

    for field_name, field in form._fields.items():
        if field_name_pattern in field_name and field.type == field_type:
            try:
                field.data = tratar_emails(field.data)
            except Exception:
                field.errors.append('Erro ao validar Emails')

    if form.errors:
        return False
    else:
        return True


def validate_upload_file_size(file_data):
    max_size_mb = app.config['MAX_UPLOAD_SIZE_MB']
    max_bytes = max_size_mb * 1024 * 1024

    if getsizeof(file_data) <= max_bytes:
        return True
    else:
        return False
