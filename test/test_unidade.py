from click.testing import CliRunner
from flask import Flask

from src.main.unidade.commands import carregar_unidades
from src.main.unidade.unidade import Unidade


def test_carregar_unidades(app: Flask):
    with app.app_context():
        infos = Unidade.carregar_unidades(cod_emp_princ=423, ativo=True)

        assert infos.ok is True


def test_carregar_unidades_command(runner: CliRunner):
    args_list = ["-cod", 423, "-atv", 1]

    res = runner.invoke(carregar_unidades, args=args_list)

    assert res.exit_code == 0
    assert res.exception is None
