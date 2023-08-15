from flask import Flask

from src.main.cargo.commands import carregar_cargos
from src.main.empresa.commands import carregar_empresas
from src.main.funcionario.commands import carregar_funcionarios
from src.main.mandato_cipa.commands import mandato_cipa
from src.main.pedido.commands import carregar_pedidos
from src.main.processamento.commands import cancelar_tarefas


def add_all_commands(app: Flask):
    app.cli.add_command(carregar_cargos)
    app.cli.add_command(carregar_empresas)
    app.cli.add_command(carregar_funcionarios)
    app.cli.add_command(mandato_cipa)
    app.cli.add_command(carregar_pedidos)
    app.cli.add_command(cancelar_tarefas)
    return app
