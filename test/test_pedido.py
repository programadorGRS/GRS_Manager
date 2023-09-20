import random
from datetime import datetime, timedelta

from click.testing import CliRunner
from flask import Flask

from src.extensions import database
from src.main.empresa.empresa import Empresa
from src.main.pedido.commands import carregar_pedidos
from src.main.pedido.pedido import Pedido


def test_carregar_pedidos(app: Flask):
    with app.app_context():
        EMPRESA = (
            database.session.query(Empresa)
            .filter(Empresa.cod_empresa == 529768)
            .first()
        )
        infos = Pedido.carregar_pedidos(
            id_empresa=EMPRESA.id_empresa,
            dataInicio=(datetime.now() - timedelta(days=1)).date(),
            dataFim=(datetime.now() + timedelta(days=1)).date()
        )

        assert infos.ok == True

def test_carregar_pedidos_command(app: Flask, runner: CliRunner):
    with app.app_context():
        empresas = Empresa.query.filter_by(cod_empresa_principal=423).all()
        emp: Empresa = random.choice(empresas)

        args_list = ['--id-empresa', emp.id_empresa]

    result = runner.invoke(carregar_pedidos, args=args_list)

    assert result.exit_code == 0
    assert result.exception is None

