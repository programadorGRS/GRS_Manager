import os

from flask import Flask, current_app

from src.config import set_app_config


def set_app_config_by_os_name(app: Flask):
    name = os.name
    print('Usando configuração: ', end='')
    if name == 'posix':
        print('prod')
        set_app_config(app=current_app, conf='prod')
    else:
        print('dev')
        set_app_config(app=current_app, conf='dev')
