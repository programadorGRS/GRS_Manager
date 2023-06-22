from datetime import date, timedelta

import click

from src.extensions import database
from src.main.empresa.empresa import Empresa
from src.main.unidade.unidade import Unidade


def get_lista(
        modo: int,
        id_empresa: int | None = None,
        cod_unidade: str | None = None
    ) -> list[Empresa | Unidade] | None:
    match modo:
        case 1: # por empresa
            if id_empresa:
                # empresa especifica
                return (
                    database.session.query(Empresa)
                    .filter(Empresa.id_empresa == id_empresa)
                    .all()
                )
            else:
                # todas as empresas habilitadas
                return (
                    database.session.query(Empresa)
                    .filter(Empresa.ativo == True)
                    .filter(Empresa.erros_mandt_cipa == True)
                    .all()
                )
        case 2: # por unidade
            if cod_unidade:
                # unidade especifica
                if not id_empresa:
                    click.echo('id-empresa é obrigatório no modo Unidades')
                    return None
                return (
                    database.session.query(Unidade)
                    .filter(Unidade.id_empresa == id_empresa)
                    .filter(Unidade.cod_unidade == cod_unidade)
                    .all()
                )
            else:
                # todas as unidades habilitadas
                return (
                    database.session.query(Unidade)
                    .filter(Unidade.ativo == True)
                    .filter(Unidade.erros_mandt_cipa == True)
                    .all()
                )
        case _:
            click.echo('Modo inválido, use 1 (Modo Empresas) ou 2 (Modo Unidades)')
            return None

def validate_datas(
        data_inicio: date | None = None,
        data_fim: date | None = None
    ) -> tuple[date, date] | None:
    '''
        Valida as datas passadas para a funcao

        Emite msg de erro se houver

        Retorna datas padrão se nenhuma for passada
    '''
    if not data_inicio and not data_fim:
        # gerar automaticamente
        inicio = (date.today() - timedelta(days=730)) # hoje menos 2 anos
        fim = (date.today() + timedelta(days=30)) # hoje mais 30 dias
        return (inicio, fim)

    if data_inicio > data_fim:
        click.echo('Erro: data-inicio deve ser menor que data-fim')
        return None

    if data_inicio and not data_fim:
        click.echo('Erro: indique data-fim')
        return None

    if data_fim and not data_inicio:
        click.echo('Erro: indique data-inicio')
        return None

    return (data_inicio, data_fim)

