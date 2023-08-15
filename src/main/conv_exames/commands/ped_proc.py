import json
import os

import click
from flask.cli import with_appcontext

from src.commands.options import opt_id_empresa
from src.commands.utils import handle_id_empresa
from src.main.job.job import Job

from ..ped_proc import PedidoProcessamento

opt_id_empresa.multiple = True

short_help = "Cria Pedidos de Processamento para as Empresas passadas."


@click.command("criar-ped-proc", params=[opt_id_empresa], short_help=short_help)
@with_appcontext
def criar_ped_proc(id_empresa: list[int] | int | None):
    criados = 0
    erros = 0

    EMPRESAS = handle_id_empresa(id_empresa=id_empresa)

    click.echo("Criando Pedidos de Processamento...")

    try:
        WSDL, WS_KEYS = __get_proc_assinc_configs()
    except Exception as e:
        click.echo(click.style(f"Erro: {str(e)}", fg="red"))
        return None

    for idx, emp in enumerate(EMPRESAS):
        click.echo(
            (
                f"{idx + 1}/{len(EMPRESAS)} | "
                f"IdEmpresa: {emp.id_empresa} | "
                f"Cod: {emp.cod_empresa} | Nome: {emp.razao_social[:15]} | "
            ),
            nl=False,
        )

        infos = PedidoProcessamento.criar_ped_proc(
            id_empresa=emp.id_empresa, wsdl=WSDL, ws_keys=WS_KEYS
        )

        Job.log_job(infos)

        if infos.ok:
            criados += 1

        msg_stt = click.style("Pedido Processamento criado", fg="green")
        if infos.erro:
            erros += 1
            msg_stt = click.style(f"Erro: {infos.erro}", fg="red")

        click.echo(msg_stt)

    click.echo(f"Done! -> Total: {len(EMPRESAS)} | Criados: {criados} | Erros {erros}")

    return None


def __get_proc_assinc_configs():
    wsdl = os.path.join(
        "configs", "soc", "wsdl", "prod", "ProcessamentoAssincronoWs.xml"
    )

    keys_path = os.path.join("keys", "soc", "web_service", "grs.json")
    with open(keys_path, "r") as f:
        ws_keys = json.load(f)

    return (wsdl, ws_keys)
