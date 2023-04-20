import pytest
from flask import Flask
from click.testing import CliRunner
from dotenv import dotenv_values

from src import app as original_app

@pytest.fixture()
def app():
    yield original_app

@pytest.fixture()
def client(app: Flask):
    return app.test_client()

@pytest.fixture()
def runner():
    '''
        Use this runner to run the apps CLI commands

        Also allows to step into the commands code
    '''
    conf = dotenv_values(dotenv_path='.flaskenv')
    return CliRunner(env=conf, mix_stderr=False)

