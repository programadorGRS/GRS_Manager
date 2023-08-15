from .commands import criar_ped_proc, inserir_conv_exames, sync_configs
from .routes import _conv_exames

conv_exames = _conv_exames

# commands
conv_exames.cli_group = "conv-exames"
conv_exames.cli.short_help = "Commandos para Convocação de Exames"

conv_exames.cli.add_command(criar_ped_proc)
conv_exames.cli.add_command(inserir_conv_exames)
conv_exames.cli.add_command(sync_configs)
