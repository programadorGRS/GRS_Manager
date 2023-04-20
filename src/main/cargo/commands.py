import click

from src import app
from src.main.cargo.cargo import Cargo
from src.main.empresa_principal.empresa_principal import EmpresaPrincipal


@app.cli.command()
def carregar_cargos():
    '''Carrega os Cargos de todas as Empresas Principais'''

    total_inseridos = 0
    total_atualizados = 0
    erros = 0

    EMPRESAS: list[EmpresaPrincipal] = EmpresaPrincipal.query.all()

    click.echo(f'Carregando Cargos das Empresas Principais...')

    for emp in EMPRESAS:
        click.echo(f'{emp.cod} - {emp.nome} - ', nl=False)
        
        infos = Cargo.carregar_cargos(cod_empresa_principal=emp.cod)

        total_inseridos = total_inseridos + infos.qtd_inseridos
        total_atualizados = total_atualizados + infos.qtd_atualizados

        if infos.erro:
            click.echo(f'Erro: {infos.erro} - ', nl=False)
            erros = erros + 1

        click.echo(f'Inseridos: {infos.qtd_inseridos} | Atualizados: {infos.qtd_atualizados}')

    click.echo(f'Done! Total -> Inseridos: {total_inseridos} | Atualizados: {total_atualizados} | Erros {erros}')

