import click
from flask.cli import with_appcontext
from sqlalchemy.exc import DatabaseError, SQLAlchemyError

from src.extensions import database
from src.main.job.job import Job
from src.utils import gerar_datas

from ..historico_mandatos import HistoricoMandatos
from ..mandato_configs.mandato_config_empresa import MandatoConfigEmpresa
from ..mandato_configs.mandato_config_handler import MandatoConfigHandler
from ..mandato_configs.mandato_config_unidade import MandatoConfigUnidade
from ..monitora_mandato import MonitoraMandato
from .helpers import get_mandato_confs, validate_datas
from .options import (ativo_multiple, ativo_single, data_fim, data_inicio,
                      dias_vencimento, id_empresa, id_unidade, modo)

par = (id_empresa, data_inicio, data_fim, ativo_multiple)
srt_help = "Carrega os mandatos CIPA"


@click.command("carregar-hist-mandatos", params=par, short_help=srt_help)
@with_appcontext
def carregar_hist_mandatos(id_empresa, data_inicio, data_fim, ativo):
    total_inseridos = 0
    erros = 0

    if id_empresa:
        MANDATO_CONFS: list[MandatoConfigEmpresa] = (
            database.session.query(MandatoConfigEmpresa)  # type: ignore
            .filter(MandatoConfigEmpresa.id_empresa == id_empresa)
            .all()
        )
    else:
        MANDATO_CONFS = (
            database.session.query(MandatoConfigEmpresa)  # type: ignore
            .filter(MandatoConfigEmpresa.load_hist == True)  # noqa
            .all()
        )

    # NOTE: as datas servem para filtrar a coluna DATAINICIOMANDATO no Exporta Dados
    DATAS_LIMITE = validate_datas(data_inicio=data_inicio, data_fim=data_fim)
    if not DATAS_LIMITE:
        return None

    par_inicio, par_fim = DATAS_LIMITE

    par_inicio_str = par_inicio.strftime("%d/%m/%Y")
    par_fim_str = par_fim.strftime("%d/%m/%Y")
    click.echo(f"Carregando Mandatos no periodo de {par_inicio_str} a {par_fim_str}...")

    LISTA_DATAS = gerar_datas(data_inicio=par_inicio, data_fim=par_fim, passo_dias=365)

    for ind, conf in enumerate(MANDATO_CONFS):
        for status in ativo:
            for inicio, fim in LISTA_DATAS:
                progr = f"{ind + 1}/{len(MANDATO_CONFS)} | "
                infos_emp = f"IdEmpresa: {conf.id_empresa} | Cod: {conf.empresa.cod_empresa} | Nome: {conf.empresa.razao_social[:15]} |"
                click.echo(progr + infos_emp, nl=False)

                inicio_str = inicio.strftime("%d/%m/%Y")
                fim_str = fim.strftime("%d/%m/%Y")

                stt = click.style(status, fg="green")
                if status == 0:
                    stt = click.style(status, fg="red")

                click.echo(
                    f"Periodo: {inicio_str} a {fim_str} | MandatosAtivos: {stt} | ",
                    nl=False,
                )

                infos = HistoricoMandatos.carregar_mandatos(
                    id_empresa=conf.id_empresa,
                    data_inicio=inicio,
                    data_fim=fim,
                    mandato_ativo=status,
                )

                Job.log_job(infos)

                erro = infos.erro
                if erro:
                    click.echo(click.style(text=f"Erro: {erro}", fg="red"))
                    erros = erros + 1
                else:
                    click.echo(
                        click.style(
                            text=f"Inseridos: {infos.qtd_inseridos}", fg="green"
                        )
                    )

                total_inseridos = total_inseridos + infos.qtd_inseridos

    click.echo(
        f"Done! Total: {len(MANDATO_CONFS)} | Inseridos: {total_inseridos} | Erros {erros}"
    )


par = (
    id_empresa,
    id_unidade,
    data_inicio,
    data_fim,
    ativo_single,
    dias_vencimento,
    modo,
)
srt_help = "Executa rotina de monitoramento de Mandatos CIPA"


@click.command("monitorar-mandatos", params=par, short_help=srt_help)
@with_appcontext
def monitorar_mandatos(
    id_empresa, data_inicio, data_fim, ativo, dias_vencimento, id_unidade, modo
):
    total = 0
    erros = 0

    MANDATO_CONFS = get_mandato_confs(
        modo=modo, id_empresa=id_empresa, id_unidade=id_unidade
    )
    if not MANDATO_CONFS:
        click.echo(
            "Nenhuma configuração de Mandato encontrada para os parametros atuais"
        )
        return None

    # NOTE: as datas servem para filtrar a coluna DATAINICIOMANDATO no Exporta Dados
    DATAS = validate_datas(data_inicio=data_inicio, data_fim=data_fim)
    if not DATAS:
        return None

    inicio, fim = DATAS

    inicio_str = inicio.strftime("%d/%m/%Y")
    fim_str = fim.strftime("%d/%m/%Y")
    click.echo(f"Buscando Mandatos no periodo de {inicio_str} a {fim_str}...")

    for ind, conf in enumerate(MANDATO_CONFS):
        if isinstance(conf, MandatoConfigEmpresa):
            id_obj = conf.id_empresa
            cod_obj = conf.empresa.cod_empresa
            nome_obj = conf.empresa.razao_social
            id_emp = conf.id_empresa
            cod_un = None
        elif isinstance(conf, MandatoConfigUnidade):
            id_obj = conf.id_unidade
            cod_obj = conf.unidade.cod_unidade
            nome_obj = conf.unidade.nome_unidade
            id_emp = conf.unidade.id_empresa
            cod_un = conf.unidade.cod_unidade
        else:
            return None

        progresso = f"{ind + 1}/{len(MANDATO_CONFS)} | "
        infos_obj = f"Id: {id_obj} | Cod: {cod_obj} | Nome: {nome_obj} | "
        click.echo(progresso + infos_obj, nl=False)

        mon = MonitoraMandato()
        infos = mon.rotina_monitorar_mandatos(
            id_empresa=id_emp,
            data_inicio=inicio,
            data_fim=fim,
            mandatos_ativos=ativo,
            dias_ate_vencimento=dias_vencimento,
            cod_unidade=cod_un,
            erros=conf.monit_erros,
            vencimentos=conf.monit_venc,
        )

        erro = infos.get("erro")
        if erro:
            click.echo(click.style(text=f"Erro: {erro}", fg="red"))
            erros = erros + 1
        else:
            click.echo(click.style(text="Email Enviado", fg="green"))

        total = total + 1

    click.echo(f"Done! Total: {total} | Erros: {erros}")


@click.command("sync-configs", short_help="Sincroniza configurações")
@with_appcontext
def sync_configs():
    """Sincroniza configs das tabelas MandatoConfigEmpresa e MandatoConfigUnidade"""

    click.echo("Sincronizando configs...")

    for tab in (MandatoConfigEmpresa.__tablename__, MandatoConfigUnidade.__tablename__):
        click.echo(f"{tab} | ", nl=False)
        try:
            res = __sync(table_name=tab)
            msg = click.style(f"Sincronizadas: {res}", fg="green")
        except (SQLAlchemyError, DatabaseError) as e:
            msg = click.style(str(e), fg="red")
            database.session.rollback()  # type: ignore

        click.echo(msg)
    click.echo("Done!")


def __sync(table_name: str):
    conf_hand = MandatoConfigHandler(
        tab_empresa=MandatoConfigEmpresa.__tablename__,
        tab_unidade=MandatoConfigUnidade.__tablename__,
    )
    pend = conf_hand.get_pending_confs(table_name=table_name)

    if not pend:
        return 0

    if table_name == conf_hand.empresa:
        att_name = "id_empresa"
    else:
        att_name = "id_unidade"

    obj_ids = [getattr(obj, att_name) for obj in pend]

    if not obj_ids:
        return 0

    res = conf_hand.insert_confs(table_name=table_name, obj_ids=obj_ids)

    return res
