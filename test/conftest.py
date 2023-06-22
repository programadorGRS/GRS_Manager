import json

import pytest
from click.testing import CliRunner
from dotenv import dotenv_values
from flask import Flask

from src import app as original_app


@pytest.fixture()
def app():
    conf = dotenv_values(dotenv_path='.flaskenv')

    env = conf.get('FLASK_ENV')
    if env == 'production':
        # using mysql
        original_app.config.from_file("../configs/prod.json", load=json.load)
    else:
        # using sqlite
        original_app.config.from_file("../configs/dev.json", load=json.load)

    yield original_app

@pytest.fixture()
def client(app: Flask):
    return app.test_client()

@pytest.fixture()
def runner(app: Flask):
    '''
        Use this runner to run the apps CLI commands

        Also allows to step into the commands code
    '''
    conf = dotenv_values(dotenv_path='.flaskenv')
    return CliRunner(env=conf, mix_stderr=False)

