from click.testing import CliRunner
from flask import Flask

from src.main.empresa.commands import carregar_empresas
from src.main.empresa.empresa import Empresa


def test_carregar_empresas(app: Flask):
    with app.app_context():
        infos = Empresa.carregar_empresas(cod_empresa_principal=423)

    assert infos.erro is None
    assert infos.ok == True

def test_carregar_empresas_command(runner: CliRunner):
    result = runner.invoke(carregar_empresas)

    assert result.exit_code == 0
    assert result.exception is None

