from datetime import datetime, timedelta

import click
from flask.cli import with_appcontext

from src.commands.options import DATE_FORMAT, opt_data_inicio
from src.extensions import database as db
from src.main.job.infos_carregar import InfosCarregar
from src.main.job.job import Job

from ..empresa.empresa import Empresa
from .models import ConvExames, PedidoProcessamento


@click.command("criar-ped-proc")
@with_appcontext
def criar_ped_proc():
    """Cria Pedidos de Processamento para todas as Empresas"""
    click.echo("Criando Pedidos Processamento...")

    empresas: list[Empresa] = Empresa.query.all()

    total = len(empresas)
    erros = 0

    for idx, empresa in enumerate(empresas):
        click.echo(
            f"{idx + 1}/{len(empresas)} | "
            f"ID: {empresa.id_empresa} | Cod {empresa.cod_empresa} | "
            f"Nome: {empresa.razao_social[:15]} | ",
            nl=False,
        )

        infos = InfosCarregar(
            tabela=PedidoProcessamento.__tablename__,
            cod_empresa_principal=empresa.cod_empresa_principal,
            id_empresa=empresa.id_empresa,
        )

        res = PedidoProcessamento.criar_pedido_processamento(
            id_empresa=empresa.id_empresa
        )

        status = res["status"]
        msg = click.style(status, fg="green")
        if status != "Ok":
            msg = click.style(status, fg="red")
            erros += 1
            infos.ok = False
            infos.add_error(status)

        click.echo(msg)

        Job.log_job(infos)

    click.echo(f"Done! -> Total: {total} | Erros: {erros}")


@click.command("inserir-conv-exames", params=[opt_data_inicio])
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

        infos = InfosCarregar(
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
