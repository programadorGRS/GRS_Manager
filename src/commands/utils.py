from datetime import date

import click


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
