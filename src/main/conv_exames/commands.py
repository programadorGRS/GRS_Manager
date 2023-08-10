import click
from flask.cli import with_appcontext

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

    for empresa in empresas:
        click.echo(
            f"ID: {empresa.id_empresa} | Cod {empresa.cod_empresa} | Nome: {empresa.razao_social[:20]} | ",
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


@click.command("inserir-conv-exames")
@with_appcontext
def inserir_conv_exames():
    """Carrega Conv Exames de todos os Pedidos Proc não inseridos"""
    click.echo("Inserindo Convocação de Exames...")

    pedidos_proc: list[PedidoProcessamento] = (
        db.session.query(PedidoProcessamento)  # type: ignore
        .filter(PedidoProcessamento.resultado_importado == False)  # noqa
        .all()
    )

    total = len(pedidos_proc)
    erros = 0

    for ped_proc in pedidos_proc:
        click.echo(
            f"ID: {ped_proc.id_proc} | Cod Sol: {ped_proc.cod_solicitacao} "
            f"| Empresa: {ped_proc.empresa.razao_social[:20]} | ",
            nl=False,
        )

        infos = InfosCarregar(
            tabela=ConvExames.__tablename__,
            cod_empresa_principal=ped_proc.empresa.cod_empresa_principal,
            id_empresa=ped_proc.id_empresa,
        )

        res = ConvExames.inserir_conv_exames(id_proc=ped_proc.id_proc)

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
