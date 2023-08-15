from datetime import date, timedelta

import click

from src.extensions import database as db

from ..mandato_configs.mandato_config_empresa import MandatoConfigEmpresa
from ..mandato_configs.mandato_config_unidade import MandatoConfigUnidade


def get_mandato_confs(
    modo: int, id_empresa: int | None = None, id_unidade: str | None = None
) -> list[MandatoConfigEmpresa | MandatoConfigUnidade] | None:
    match modo:
        case 1:  # por empresa
            if id_empresa:
                # empresa especifica
                return (
                    db.session.query(MandatoConfigEmpresa)  # type: ignore
                    .filter(MandatoConfigEmpresa.id_empresa == id_empresa)
                    .all()
                )
            else:
                # todas as empresas habilitadas
                return (
                    db.session.query(MandatoConfigEmpresa)  # type: ignore
                    .filter(
                        db.or_(  # type: ignore
                            MandatoConfigEmpresa.monit_erros == True,  # noqa
                            MandatoConfigEmpresa.monit_venc == True,  # noqa
                        )
                    )
                    .all()
                )
        case 2:  # por unidade
            if id_unidade:
                # unidade especifica
                return (
                    db.session.query(MandatoConfigUnidade)  # type: ignore
                    .filter(MandatoConfigUnidade.id_unidade == id_unidade)
                    .all()
                )
            else:
                # todas as unidades habilitadas
                return (
                    db.session.query(MandatoConfigUnidade)  # type: ignore
                    .filter(
                        db.or_(  # type: ignore
                            MandatoConfigUnidade.monit_erros == True,  # noqa
                            MandatoConfigUnidade.monit_venc == True,  # noqa
                        )
                    )
                    .all()
                )
        case _:
            click.echo("Modo inválido, use 1 (Modo Empresas) ou 2 (Modo Unidades)")
            return None


def validate_datas(
    data_inicio: date | None = None, data_fim: date | None = None
) -> tuple[date, date] | None:
    """
    Valida as datas passadas para a funcao

    Emite msg de erro se houver

    Retorna datas padrão se nenhuma for passada
    """
    if not data_inicio and not data_fim:
        # gerar automaticamente
        inicio = date.today() - timedelta(days=730)  # hoje menos 2 anos
        fim = date.today() + timedelta(days=30)  # hoje mais 30 dias
        return (inicio, fim)

    if data_inicio and not data_fim:
        click.echo("Erro: indique data-fim")
        return None

    if data_fim and not data_inicio:
        click.echo("Erro: indique data-inicio")
        return None

    if data_inicio > data_fim:  # type: ignore
        click.echo("Erro: data-inicio deve ser menor que data-fim")
        return None

    return (data_inicio, data_fim)  # type: ignore
