from flask.cli import AppGroup

from .commands import carregar_hist_mandatos, monitorar_mandatos, sync_configs

mandato_cipa = AppGroup(name="mandato-cipa")

mandato_cipa.short_help = "Comanddos para Mandato CIPA"

mandato_cipa.add_command(carregar_hist_mandatos)
mandato_cipa.add_command(monitorar_mandatos)
mandato_cipa.add_command(sync_configs)
