from .commands import carregar_prestadores
from .routes import prestador_bp

prestador_bp.cli.short_help = "Comandos para Prestador"

# commands
prestador_bp.cli.add_command(carregar_prestadores)
