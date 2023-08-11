import click

from src import app
from src.commands.options import opt_ativo, opt_cod_emp_princ

from ..empresa_principal.empresa_principal import EmpresaPrincipal
from ..job.job import Job
from .unidade import Unidade

opt_ativo.help = "Unidades Ativas. 0: Não, 1: Sim. Defaults to all."
opt_cod_emp_princ.help = "Código da Empresa Principal"

srt_help = "Carrega Unidades"


@app.cli.command(
    "carregar-unidades", params=[opt_ativo, opt_cod_emp_princ], short_help=srt_help
)
def carregar_unidades(ativo, cod_emp_princ):
    """Carrega todas as Unidades da Empresa Principal."""
    total_inseridos = 0
    total_atualizados = 0
    erros = 0

    if cod_emp_princ:
        EMPRESAS: list[EmpresaPrincipal] = [EmpresaPrincipal.query.get(cod_emp_princ)]
    else:
        EMPRESAS: list[EmpresaPrincipal] = EmpresaPrincipal.query.all()

    click.echo("Carregando Unidades...")

    for ind, emp in enumerate(EMPRESAS):
        progr = f"{ind + 1}/{len(EMPRESAS)} | "
        infos_emp = f"Empresa Principal | Cod: {emp.cod} | Nome: {emp.nome.strip().upper()[:15]} | "
        click.echo(progr + infos_emp, nl=False)

        infos = Unidade.carregar_unidades(cod_emp_princ=emp.cod, ativo=ativo)

        Job.log_job(infos)

        total_inseridos = total_inseridos + infos.qtd_inseridos
        total_atualizados = total_atualizados + infos.qtd_atualizados

        stt = click.style(
            f"Inseridas: {infos.qtd_inseridos} | Atualizadas: {infos.qtd_atualizados}",
            fg="green",
        )
        if not infos.ok:
            stt = click.style(f"Erro: {infos.erro}", fg="red")
            erros = erros + 1

        click.echo(stt)

    click.echo(
        f"Done! Total -> Inseridas: {total_inseridos} | Atualizadas: {total_atualizados} | Erros {erros}"
    )
