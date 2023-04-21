import datetime as dt

import pandas as pd
from flask import render_template, send_from_directory
from flask_login import login_required

from src import UPLOAD_FOLDER, app, database
from src.main.log_acoes.log_acoes import LogAcoes
from src.utils import admin_required

from .forms import FormLogAcoes


@app.route('/log_acoes', methods=['GET', 'POST'])
@login_required
@admin_required
def log_acoes():
    form = FormLogAcoes()
    
    form.tabela.choices = (
        [('', 'Selecione')] + (
            LogAcoes.query.with_entities(LogAcoes.tabela, LogAcoes.tabela)
            .order_by(LogAcoes.tabela)
            .distinct()
            .all()
        )
    )
    
    form.usuario.choices = (
        [('', 'Selecione')] + (
            LogAcoes.query.with_entities(LogAcoes.id_usuario, LogAcoes.username)
            .order_by(LogAcoes.username)
            .distinct()
            .all()
        )
    )

    if form.validate_on_submit():
        query = LogAcoes.pesquisar_log(
            inicio=form.data_inicio.data,
            fim=form.data_fim.data,
            usuario=form.usuario.data,
            tabela=form.tabela.data
        )

        df = pd.read_sql(sql=query.statement, con=database.session.bind)
        
        # remover decimais da hora
        df['hora'] = list(map(lambda x: str(x).split('.')[0], df['hora']))
        
        # criar csv dentro da pasta
        nome_arqv = f'Log_acoes_{int(dt.datetime.now().timestamp())}.csv'
        camihno_arqv = f'{UPLOAD_FOLDER}/{nome_arqv}'
        df.to_csv(
            camihno_arqv,
            sep=';',
            index=False,
            encoding='iso-8859-1'
        )
        return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=nome_arqv)
    
    return render_template('log_acoes.html', title='GRS+Connect', form=form)
