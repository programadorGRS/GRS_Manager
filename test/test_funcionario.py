from click.testing import CliRunner
from flask import Flask

from src.extensions import database
from src.main.empresa.empresa import Empresa
from src.main.funcionario.commands import carregar_funcionarios
from src.main.funcionario.funcionario import Funcionario


def test_carregar_funcionarios(app: Flask):
    with app.app_context():
        EMPRESA = (
            database.session.query(Empresa)
            .filter(Empresa.cod_empresa == 529768)
            .first()
        )

        res = Funcionario.carregar_funcionarios(id_empresa=EMPRESA.id_empresa)

    assert res.ok == True

def test_carregar_funcionarios_command(runner:  CliRunner):
    args_list = ['-id', 1]
    res = runner.invoke(carregar_funcionarios, args=args_list)

    assert res.exit_code == 0
    assert res.exception is None

