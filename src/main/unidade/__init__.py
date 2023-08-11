from .commands import carregar_unidades
from .routes import _unidade

unidade = _unidade

# commands
unidade.cli_group = "unidade"
unidade.cli.help = "Comandos para Unidade"

unidade.cli.add_command(carregar_unidades)
