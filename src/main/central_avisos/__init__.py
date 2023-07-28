from .commands import gerar_tokens
from .error_handlers import error_404_central
from .routes import _central_avisos

central_avisos = _central_avisos

# error handlers
central_avisos.register_error_handler(404, error_404_central)

# commands
central_avisos.cli.short_help = "Comandos para a Central de Avisos"
central_avisos.cli.add_command(gerar_tokens)
