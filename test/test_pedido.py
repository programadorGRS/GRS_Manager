import random
from datetime import datetime, timedelta

from click.testing import CliRunner
from flask import Flask

from src.main.pedido.commands import carregar_pedidos
from src.main.pedido.pedido import Pedido
from src.main.empresa.empresa import Empresa


def test_carregar_pedidos(app: Flask):
    with app.app_context():
        qtd_empresas = Empresa.query.count()
        infos = Pedido.carregar_pedidos(
            id_empresa=random.randint(1, qtd_empresas),
            dataInicio=(datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y'),
            dataFim=(datetime.now() + timedelta(days=1)).strftime('%d/%m/%Y')
        )

def test_carregar_pedidos_command(app: Flask, runner: CliRunner):
    COD_GRS = 423

    with app.app_context():
        empresas = Empresa.query.filter_by(cod_empresa_principal=423).all()
        emp: Empresa = random.choice(empresas)

        args_list = [
            '--id-empresa', emp.id_empresa,
            '--data-inicio', (datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y'),
            '--data-fim', (datetime.now() + timedelta(days=1)).strftime('%d/%m/%Y')
        ]

    result = runner.invoke(carregar_pedidos, args=args_list)

    assert result.exit_code == 0
    assert result.exception is None

