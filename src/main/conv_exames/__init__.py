from .routes import _conv_exames
from .commands.ped_proc import criar_ped_proc


conv_exames = _conv_exames

# commands
conv_exames.cli.short_help = "Comandos para Convocação de Exames"
conv_exames.cli.add_command(criar_ped_proc)
