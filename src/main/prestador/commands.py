import json
from io import BytesIO

import click
from flask.cli import with_appcontext

from src import app

from ..empresa_principal.empresa_principal import EmpresaPrincipal
from ..job.job import Job
from .prestador import Prestador


@click.command("carregar-prestadores")
@with_appcontext
def carregar_prestadores():
    """Carrega todos os Prestadores"""

    COD_EMPRESA = app.config["COD_EMP_PRINC"]
    EMPRESA = EmpresaPrincipal.query.get(COD_EMPRESA)

    try:
        WSDL, ED_KEYS = __get_credentials()
    except Exception as e:
        click.echo(str(e))
        return None

    click.echo("Carregando Prestadores...")

    click.echo(f"Cod: {EMPRESA.cod} | Nome: {EMPRESA.nome} | ", nl=False)

    infos = Prestador.carregar_prestadores(
        cod_emp_princ=EMPRESA.cod, wsdl=WSDL, ed_keys=ED_KEYS
    )

    Job.log_job(infos=infos)

    if infos.erro:
        click.echo(click.style(f"Erro: {infos.erro}", fg="red"))

    click.echo(
        click.style(
            f"Inseridos: {infos.qtd_inseridos} | Atualizados: {infos.qtd_atualizados}",
            fg="green",
        )
    )

    click.echo("Done!")


def __get_credentials():
    with open("configs/soc/wsdl/prod/ExportaDadosWs.xml", mode="rb") as f:
        wsdl = BytesIO(f.read())

    with open("keys/soc/exporta_dados/grs.json", mode="rt") as f:
        ed_keys = json.load(f)

    return (wsdl, ed_keys)
