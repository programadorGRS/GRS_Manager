from datetime import datetime, timedelta

import click

from src import app

from ..empresa.empresa import Empresa
from ..job.job import Job
from .pedido import Pedido


opt_dataInicio = click.Option(
    default=(datetime.now() - timedelta(days=10)).strftime('%d/%m/%Y'),
    param_decls=['-dti', '--data-inicio'],
    type=str,
    show_default=True,
    help='Data Inicio (Data da Ficha). Format: "dd/mm/yyyy". Defaults to current date - 10 days'
)

opt_dataFim = click.Option(
    param_decls=['-dtf', '--data-fim'],
    default=(datetime.now() + timedelta(days=10)).strftime('%d/%m/%Y'),
    type=str,
    show_default=True,
    help='Data Fim (Data da Ficha). Format: "dd/mm/yyyy". Defaults to current date + 10 days'
)

opt_id_empresa = click.Option(
    param_decls=['-id', '--id-empresa'],
    default=None,
    type=int,
    show_default=False,
    help='Id da Empresa para carregar os Pedidos. Defaults to all.'
)

par = [opt_id_empresa, opt_dataInicio, opt_dataFim]
srt_help = 'Carrega Pedidos de Exames'

@app.cli.command('carregar-pedidos', params=par, short_help=srt_help)
def carregar_pedidos(id_empresa, data_inicio, data_fim):
    '''
        Carrega os Pedidos de Exame de uma Empresa específica ou de
        todas as Empresas dentro período selecionado.

        Obs: o período máximo é de 30 dias.
    '''

    total_inseridos = 0
    total_atualizados = 0
    erros = 0

    if id_empresa:
        EMPRESAS: list[Empresa] = [Empresa.query.get(id_empresa)]
    else:
        EMPRESAS: list[Empresa] = Empresa.query.all()

    click.echo(f'Carregando Pedidos no período: {data_inicio} - {data_fim}...')

    for emp in EMPRESAS:
        click.echo(f'{emp.id_empresa} - {emp.razao_social} - ', nl=False)

        infos = Pedido.carregar_pedidos(
            id_empresa=emp.id_empresa,
            dataInicio=data_inicio,
            dataFim=data_fim
        )

        Job.log_job(infos)

        total_inseridos = total_inseridos + infos.qtd_inseridos
        total_atualizados = total_atualizados + infos.qtd_atualizados

        if infos.erro:
            click.echo(f'Erro: {infos.erro} - ', nl=False)
            erros = erros + 1

        click.echo(f'Inseridos: {infos.qtd_inseridos} | Atualizados: {infos.qtd_atualizados}')

    click.echo(f'Done! Total -> Inseridos: {total_inseridos} | Atualizados: {total_atualizados} | Erros {erros}')

