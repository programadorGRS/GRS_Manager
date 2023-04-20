from click.testing import CliRunner
from flask import Flask

from src.main.cargo.cargo import Cargo
from src.main.cargo.commands import carregar_cargos


def test_carregar_cargos(app: Flask):
    with app.app_context():
        infos = Cargo.carregar_cargos(cod_empresa_principal=423)

    assert infos.erro is None
    assert infos.ok == True

def test_carregar_cargos_command(runner: CliRunner):
    result = runner.invoke(carregar_cargos)

    assert result.exit_code == 0
    assert result.exception is None

