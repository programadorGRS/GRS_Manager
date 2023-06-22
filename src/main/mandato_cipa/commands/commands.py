import click

from src import app
from src.extensions import database
from src.main.empresa.empresa import Empresa
from src.main.job.job import Job
from src.main.unidade.unidade import Unidade
from src.utils import gerar_datas

from ..historico_mandatos import HistoricoMandatos
from ..monitora_mandato import MonitoraMandato
from .helpers import get_lista, validate_datas
from .options import (ativo_multiple, ativo_single, cod_unidade, data_fim,
                      data_inicio, dias_vencimento, id_empresa, modo)

par = (id_empresa, data_inicio, data_fim, ativo_multiple)
srt_help = 'Carrega os mandatos CIPA'
@app.cli.command('carregar-hist-mandatos', params=par, short_help=srt_help)
def carregar_hist_mandatos(id_empresa, data_inicio, data_fim, ativo):
    total_inseridos = 0
    erros = 0

    if id_empresa:
        EMPRESAS: list[Empresa] = [Empresa.query.get(id_empresa)]
    else:
        EMPRESAS: list[Empresa] = (
            database.session.query(Empresa)
            .filter(Empresa.ativo == True)
            .filter(Empresa.hist_mandt_cipa == True)
            .all()
        )

    # NOTE: as datas servem para filtrar a coluna DATAINICIOMANDATO no Exporta Dados
    DATAS_LIMITE = validate_datas(data_inicio=data_inicio, data_fim=data_fim)
    if not DATAS_LIMITE:
        return None

    par_inicio, par_fim = DATAS_LIMITE

    par_inicio_str = par_inicio.strftime('%d/%m/%Y')
    par_fim_str = par_fim.strftime('%d/%m/%Y')

    click.echo(f'Carregando Mandatos no periodo de {par_inicio_str} a {par_fim_str}...')

    LISTA_DATAS = gerar_datas(data_inicio=par_inicio, data_fim=par_fim, passo_dias=365)

    for ind, emp in enumerate(EMPRESAS):
        for status in ativo:
            for inicio, fim in LISTA_DATAS:
                progr = f'{ind + 1}/{len(EMPRESAS)} | '
                infos_emp = f'IdEmpresa: {emp.id_empresa} | Cod: {emp.cod_empresa} | Nome: {emp.razao_social[:15]} |'
                click.echo(progr + infos_emp, nl=False)


                inicio_str = inicio.strftime('%d/%m/%Y')
                fim_str = fim.strftime('%d/%m/%Y')

                stt = click.style(status, fg='green')
                if status == 0:
                    stt = click.style(status, fg='red')

                click.echo(f'Periodo: {inicio_str} a {fim_str} | MandatosAtivos: {stt} | ', nl=False)

                infos = HistoricoMandatos.carregar_mandatos(
                    id_empresa=emp.id_empresa,
                    data_inicio=inicio,
                    data_fim=fim,
                    mandato_ativo=status
                )

                Job.log_job(infos)

                erro = infos.erro
                if erro:
                    click.echo(click.style(text=f'Erro: {erro}', fg='red'))
                    erros = erros + 1
                else:
                    click.echo(click.style(text=f'Inseridos: {infos.qtd_inseridos}', fg='green'))

                total_inseridos = total_inseridos + infos.qtd_inseridos

    click.echo(f'Done! Total: {len(EMPRESAS)} | Inseridos: {total_inseridos} | Erros {erros}')

par = (
    id_empresa,
    cod_unidade,
    data_inicio,
    data_fim,
    ativo_single,
    dias_vencimento,
    modo
)
srt_help = 'Executa rotina de monitoramento de Mandatos CIPA'
@app.cli.command('monitorar-mandatos', params=par, short_help=srt_help)
def monitorar_mandatos(id_empresa, data_inicio, data_fim, ativo, dias_vencimento, cod_unidade, modo):
    total = 0
    erros = 0

    LISTA = get_lista(modo=modo, id_empresa=id_empresa, cod_unidade=cod_unidade)
    if not LISTA:
        return None

    # NOTE: as datas servem para filtrar a coluna DATAINICIOMANDATO no Exporta Dados
    DATAS = validate_datas(data_inicio=data_inicio, data_fim=data_fim)
    if not DATAS:
        return None

    inicio, fim = DATAS

    inicio_str = inicio.strftime('%d/%m/%Y')
    fim_str = fim.strftime('%d/%m/%Y')

    click.echo(f'Buscando Mandatos no periodo de {inicio_str} a {fim_str}...')

    for ind, obj in enumerate(LISTA):

        if isinstance(obj, Empresa):
            cod = obj.cod_empresa
            nome = obj.razao_social
        elif isinstance(obj, Unidade):
            cod = obj.cod_unidade
            nome = obj.nome_unidade
        else:
            return None

        progresso = f'{ind + 1}/{len(LISTA)} | '
        infos_obj = f'IdEmpresa: {obj.id_empresa} | Cod: {cod} | Nome: {nome} | '
        click.echo(progresso + infos_obj, nl=False)

        infos = MonitoraMandato.rotina_monitorar_mandatos(
            id_empresa=obj.id_empresa,
            data_inicio=inicio,
            data_fim=fim,
            mandatos_ativos=ativo,
            dias_ate_vencimento=dias_vencimento,
            cod_unidade=getattr(obj, 'cod_unidade', None)
        )

        erro = infos.get('erro')
        if erro:
            click.echo(click.style(text=f'Erro: {erro}', fg='red'))
            erros = erros + 1
        else:
            click.echo(click.style(text='Email Enviado', fg='green'))

        total = total + 1

    click.echo(f'Done! Total: {total} | Erros: {erros}')

