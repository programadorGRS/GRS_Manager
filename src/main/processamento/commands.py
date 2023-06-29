import click

from src import app

from .processamento import Processamento

srt_help = 'Cancela todas as tarefas'
@app.cli.command('cancelar-tarefas', short_help=srt_help)
def cancelar_tarefas():
    '''
        Seta o status de todas as tarefas Em Andamento para Cancelado
    '''
    res = Processamento.cancelar_todas_tarefas()
    click.echo(f'Tarefas Em Andamento Canceladas. Total: {res}')
    return None

