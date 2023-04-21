import click

from src import app

from ..empresa_principal.empresa_principal import EmpresaPrincipal
from .empresa import Empresa
from ..job.job import Job


@app.cli.command('carregar-empresas')
def carregar_empresas():
    '''Carrega as Empresas de todas as Empresas Principais'''

    total_inseridos = 0
    total_atualizados = 0
    erros = 0

    EMPRESAS: list[EmpresaPrincipal] = EmpresaPrincipal.query.all()

    click.echo(f'Carregando Empresas das Empresas Principais...')

    for emp in EMPRESAS:
        click.echo(f'{emp.cod} - {emp.nome} - ', nl=False)
        
        infos = Empresa.carregar_empresas(cod_empresa_principal=emp.cod)

        Job.log_job(infos=infos)

        total_inseridos = total_inseridos + infos.qtd_inseridos
        total_atualizados = total_atualizados + infos.qtd_atualizados

        if infos.erro:
            click.echo(f'Erro: {infos.erro} - ', nl=False)
            erros = erros + 1

        click.echo(f'Inseridos: {infos.qtd_inseridos} | Atualizados: {infos.qtd_atualizados}')

    click.echo(f'Done! Total -> Inseridos: {total_inseridos} | Atualizados: {total_atualizados} | Erros {erros}')

