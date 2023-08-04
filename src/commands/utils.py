from datetime import date

import click
from src.main.empresa.empresa import Empresa
from src.extensions import database as db


def validate_datas(data_inicio: date, data_fim: date):
    """
    Valida as datas passadas para a funcao

    Emite msg de erro se houver algum

    Retorna True/False
    """
    if not data_inicio:
        click.echo("Erro: indique data-inicio")
        return False

    if not data_fim:
        click.echo("Erro: indique data-fim")
        return False

    if data_inicio > data_fim:
        click.echo("Erro: data-inicio deve ser menor que data-fim")
        return False

    return True


def handle_id_empresa(id_empresa: int | tuple[int] | list[int] | None) -> list[Empresa]:
    if not id_empresa:
        return Empresa.query.all()
    if isinstance(id_empresa, int):
        return [Empresa.query.get(id_empresa)]
    elif isinstance(id_empresa, (tuple, list)):
        return (
            db.session.query(Empresa)  # type: ignore
            .filter(Empresa.id_empresa.in_(id_empresa))
            .all()
        )
