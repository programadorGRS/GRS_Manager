import json
import os
from datetime import datetime, timedelta

import click
from flask.cli import with_appcontext
from sqlalchemy.exc import DatabaseError, SQLAlchemyError

from src.commands.options import (DATE_FORMAT, opt_data_inicio,
                                  opt_id_empresa_multiple)
from src.commands.utils import handle_id_empresa
from src.extensions import database as db
from src.main.job.job import Job
from src.main.job.job_infos import JobInfos

from .conv_exames import ConvExames
from .conv_exames_config_handler import ConvExamesConfigHandler
from .ped_proc import PedidoProcessamento

short_help = "Cria Pedidos de Processamento para as Empresas passadas."


@click.command(
    "criar-ped-proc", params=[opt_id_empresa_multiple], short_help=short_help
)
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


def s__get_proc_assinc_configs():
    wsdl = os.path.join(
        "configs", "soc", "wsdl", "prod", "ProcessamentoAssincronoWs.xml"
    )

    keys_path = os.path.join("keys", "soc", "web_service", "grs.json")
    with open(keys_path, "r") as f:
        ws_keys = json.load(f)

    return (wsdl, ws_keys)


@click.command(
    "inserir-conv-exames",
    params=[opt_data_inicio],
    short_help="Carrega dados Conv Exames",
)
@with_appcontext
def inserir_conv_exames(data_inicio: datetime | None):
    """Carrega Conv Exames de todos os Pedidos Proc não inseridos nos ultimos dias"""
    click.echo("Inserindo Convocação de Exames...")

    if not data_inicio:
        data_inicio = datetime.now() - timedelta(days=7)

    pedidos_proc = db.session.query(  # type: ignore
        PedidoProcessamento
    ).filter(  # type: ignore
        PedidoProcessamento.resultado_importado == False  # noqa
    )

    if data_inicio:
        pedidos_proc = pedidos_proc.filter(  # type: ignore
            PedidoProcessamento.data_criacao >= data_inicio.date()
        )
        click.echo(f"Data Inicio: {data_inicio.strftime(DATE_FORMAT)}")

    if not pedidos_proc:
        click.echo("Pedidos Processamento não encontrados")
        return None

    proc_list: list[PedidoProcessamento] = pedidos_proc.all()

    total = len(proc_list)
    erros = 0

    for idx, ped_proc in enumerate(proc_list):
        click.echo(
            f"{idx + 1}/{len(proc_list)} | "
            f"ID: {ped_proc.id_proc} | Cod Sol: {ped_proc.cod_solicitacao} | "
            f"Data: {ped_proc.data_criacao.strftime(DATE_FORMAT)} | "
            f"Empresa: {ped_proc.empresa.razao_social[:15]} # {ped_proc.empresa.cod_empresa} | ",
            nl=False,
        )

        infos = JobInfos(
            tabela=ConvExames.__tablename__,
            cod_empresa_principal=ped_proc.empresa.cod_empresa_principal,
            id_empresa=ped_proc.id_empresa,
        )

        try:
            res = ConvExames.inserir_conv_exames(id_proc=ped_proc.id_proc)
        except Exception as e:
            erros += 1
            click.echo(click.style(e, fg="red"))
            infos.ok = False
            infos.add_error(str(e))
            Job.log_job(infos)
            continue

        status = res["status"]
        msg = click.style(status, fg="green")
        if status != "OK":
            msg = click.style(status, fg="red")
            erros += 1
            infos.ok = False
            infos.erro = status

        click.echo(msg)

        Job.log_job(infos)

    click.echo(f"Done! -> Total: {total} | Erros: {erros}")


@click.command("sync-configs", short_help="Sincroniza configurações de PedProcConfig")
@with_appcontext
def sync_configs():
    """Sincroniza configs da tabela PedProcConfig"""

    click.echo("Sincronizando PedProcConfig...")

    conf_handler = ConvExamesConfigHandler()
    empresas = conf_handler.get_pending_confs()

    id_empresas = [emp.id_empresa for emp in empresas]

    if not id_empresas:
        click.echo("Nenhuma configuração pendente.")
        return None

    try:
        res = conf_handler.insert_confs(id_empresas=id_empresas)
        msg = click.style(f"Sincronizadas: {res}", fg="green")
    except (SQLAlchemyError, DatabaseError) as e:
        msg = click.style(str(e), fg="red")
        db.session.rollback()  # type: ignore

    click.echo(msg)
    click.echo("Done!")
