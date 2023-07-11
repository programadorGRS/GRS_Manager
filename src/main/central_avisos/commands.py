import click

from src.commands.options import opt_id_empresa
from src.extensions import database

from ..empresa.empresa import Empresa
from .routes import central_avisos


opt_id_empresa.help = "ID da Empresa para gerar o token. Defaults to all."

central_avisos.cli.short_help = 'Comandos para a Central de Avisos'

shrt_h = "Gera tokens filtro para a Empresa na Central de Avisos. \
    Registra o token gerado automaticamente na database. Obs: gerar um token novo não invalida o antigo."


@central_avisos.cli.command("gerar-tokens", params=[opt_id_empresa], short_help=shrt_h)
def gerar_tokens(id_empresa: int):
    EMPRESAS: list[Empresa]

    if id_empresa:
        EMPRESAS = (
            database.session.query(Empresa)
            .filter(Empresa.id_empresa == id_empresa)
            .all()
        )
    else:
        EMPRESAS = database.session.query(Empresa).all()

    if not EMPRESAS:
        click.echo("Nenhuma Empresa encontrada")
        return None

    click.echo("Gerando tokens...")

    for ind, emp in enumerate(EMPRESAS):
        progr = f"{ind + 1}/{len(EMPRESAS)} | "
        infos_emp = f"IdEmpresa: {emp.id_empresa} | Cod: {emp.cod_empresa} | Nome: {emp.razao_social[:15]} |"
        click.echo(progr + infos_emp, nl=False)

        token = Empresa.generate_token_central_avisos(id_empresas=[emp.id_empresa])

        emp.central_avisos_token = token

        database.session.commit()

        click.echo(f"token: {token}")

    click.echo(f"Done! Total: {len(EMPRESAS)}")
