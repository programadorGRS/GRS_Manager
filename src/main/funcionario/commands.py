import click

from src import app
from src.commands.options import opt_id_empresa

from ..empresa.empresa import Empresa
from ..job.job import Job
from .funcionario import Funcionario

opt_id_empresa.help ='Id da Empresa para carregar os Funcionários. \
    Defaults to all.'

srt_help = 'Carrega Funcionários'
@app.cli.command(
    'carregar-funcionarios',
    params=[opt_id_empresa],
    short_help=srt_help
)
def carregar_funcionarios(id_empresa):
    '''
        Carrega os Funcionários de uma Empresa específica \
        ou de todas as Empresas.
    '''
    total_inseridos = 0
    total_atualizados = 0
    erros = 0

    if id_empresa:
        EMPRESAS: list[Empresa] = [Empresa.query.get(id_empresa)]
    else:
        EMPRESAS: list[Empresa] = Empresa.query.all()

    click.echo(f'Carregando Funcionários...')

    for ind, emp in enumerate(EMPRESAS):
        progr = f'{ind + 1}/{len(EMPRESAS)} | '
        infos_emp = f'IdEmpresa: {emp.id_empresa} | Cod: {emp.cod_empresa} | Nome: {emp.razao_social.strip().upper()[:15]} | '
        click.echo(progr + infos_emp, nl=False)

        infos = Funcionario.carregar_funcionarios(id_empresa=emp.id_empresa)

        Job.log_job(infos)

        total_inseridos = total_inseridos + infos.qtd_inseridos
        total_atualizados = total_atualizados + infos.qtd_atualizados

        stt = click.style(
            f'Inseridos: {infos.qtd_inseridos} | Atualizados: {infos.qtd_atualizados}',
            fg='green'
        )
        if not infos.ok:
            stt = click.style(f'Erro: {infos.erro}', fg='red')
            erros = erros + 1

        click.echo(stt)

    click.echo(f'Done! Total -> Inseridos: {total_inseridos} | Atualizados: {total_atualizados} | Erros {erros}')

