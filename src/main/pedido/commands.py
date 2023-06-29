from datetime import datetime, timedelta

import click

from src import app
from src.commands.options import opt_data_fim, opt_data_inicio, opt_id_empresa
from src.commands.utils import validate_datas
from src.extensions import database

from ..empresa.empresa import Empresa
from ..job.job import Job
from .pedido import Pedido

opt_data_inicio.help = 'Data Inicio (Data da Ficha). \
    Format: "dd-mm-yyyy". Defaults to current date - 10 days'
opt_data_fim.help = 'Data Fim (Data da Ficha). \
    Format: "dd-mm-yyyy". Defaults to current date + 10 days'
opt_id_empresa.help ='Id da Empresa para carregar os Pedidos. Defaults to all.'

par = [opt_data_inicio, opt_data_fim, opt_id_empresa]
srt_help = 'Carrega Pedidos de Exames'
@app.cli.command('carregar-pedidos', params=par, short_help=srt_help)
def carregar_pedidos(id_empresa, data_inicio, data_fim):
    '''
        Carrega os Pedidos de Exame de uma Empresa específica ou de
        todas as Empresas dentro período selecionado.

        Obs: o período máximo é de 30 dias.
    '''
    # NOTE: sempre carregar apenas pedidos da base da GRS
    COD_GRS = 423

    if not data_inicio and not data_fim:
        data_inicio = (datetime.now() - timedelta(days=10)).date()
        data_fim = (datetime.now() + timedelta(days=10)).date()

    validated = validate_datas(data_inicio=data_inicio, data_fim=data_fim)
    if not validated:
        return None

    total_inseridos = 0
    total_atualizados = 0
    erros = 0

    if id_empresa:
        EMPRESAS: list[Empresa] = [Empresa.query.get(id_empresa)]
    else:
        EMPRESAS: list[Empresa] = (
            database.session.query(Empresa)
            .filter(Empresa.cod_empresa_principal == COD_GRS)
            .all()
        )

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

