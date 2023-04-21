import datetime as dt

import pandas as pd
from flask import (flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required
from pytz import timezone
from sqlalchemy.exc import IntegrityError

from src import UPLOAD_FOLDER, app, database
from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
from src.main.exame.exame import Exame
from src.main.log_acoes.log_acoes import LogAcoes
from src.utils import admin_required

from .forms import FormBuscarExames, FormCriarExame, FormEditarExame


@app.route('/buscar_exames', methods=['GET', 'POST'])
@login_required
def busca_exames():
    form = FormBuscarExames()

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )

    if form.validate_on_submit() and 'botao_buscar' in request.form:
        return redirect(
            url_for(
                'exames',
                cod_empresa_principal=form.cod_empresa_principal.data,
                id_exame=form.id.data,
                cod=form.cod.data,
                nome=form.nome.data,
                prazo=form.prazo.data
            )
        )

    elif form.validate_on_submit() and 'botao_csv' in request.form:
        return redirect(
            url_for(
                'exames_csv',
                cod_empresa_principal=form.cod_empresa_principal.data,
                id_exame=form.id.data,
                cod=form.cod.data,
                nome=form.nome.data,
                prazo=form.prazo.data
            )
        )

    return render_template(
        'exame/busca.html',
        title='GRS+Connect',
        form=form
    )

@app.route('/exames')
@login_required
def exames():
    query = Exame.buscar_exames(
        cod_empresa_principal=request.args.get(key='cod_empresa_principal', default=None, type=str),
        id_exame=request.args.get(key='id_exame', default=None, type=str),
        cod_exame=request.args.get(key='cod', default=None, type=str),
        nome=request.args.get(key='nome', default=None, type=str),
        prazo=request.args.get(key='prazo', default=None, type=int)
    ).all()

    qtd = len(query)

    return render_template(
        'exame/exames.html',
        title='GRS+Connect',
        lista_exames=query,
        qtd=qtd
    )

@app.route('/exames_csv')
@login_required
def exames_csv():
    query = Exame.buscar_exames(
        cod_empresa_principal=request.args.get(key='cod_empresa_principal', default=None, type=str),
        id_exame=request.args.get(key='id_exame', default=None, type=str),
        cod_exame=request.args.get(key='cod', default=None, type=str),
        nome=request.args.get(key='nome', default=None, type=str),
        prazo=request.args.get(key='prazo', default=None, type=int)
    )
    
    df = pd.read_sql(sql=query.statement, con=database.session.bind)
    
    # criar arquivo dentro da pasta
    timestamp = int(dt.datetime.now().timestamp())
    nome_arqv = f'Exames_{timestamp}.csv'
    camihno_arqv = f'{UPLOAD_FOLDER}/{nome_arqv}'
    df.to_csv(
        camihno_arqv,
        sep=';',
        index=False,
        encoding='iso-8859-1'
    )
    
    return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=nome_arqv)

@app.route('/exames/criar', methods=['GET', 'POST'])
@login_required
def criar_exame():
    form = FormCriarExame()

    if form.validate_on_submit():
        exame = Exame(
            cod_empresa_principal=form.cod_empresa_principal.data,
            cod_exame=form.cod_exame.data,
            nome_exame=form.nome_exame.data,
            prazo=form.prazo.data,
            data_inclusao=dt.datetime.now(tz=timezone('America/Sao_Paulo')),
            incluido_por=current_user.username
        )
        database.session.add(exame)
        database.session.commit()
        
        LogAcoes.registrar_acao(
            nome_tabela = 'Exame',
            tipo_acao = 'Inclusão',
            id_registro = exame.id_exame,
            nome_registro = exame.nome_exame
        )
        
        flash('Exame criado com sucesso!', 'alert-success')
        return redirect(url_for('editar_exame', id_exame=exame.id_exame))
    
    return render_template('exame/exame_criar.html', form=form, title='GRS+Connect')

@app.route('/exames/editar', methods=['GET', 'POST'])
@login_required
def editar_exame():
    exame = Exame.query.get(request.args.get(key='id_exame', type=int))

    form = FormEditarExame(
        cod_empresa_principal=exame.cod_empresa_principal,
        cod_exame=exame.cod_exame,
        nome_exame=exame.nome_exame,
        prazo=exame.prazo,
        data_inclusao=exame.data_inclusao,
        data_alteracao=exame.data_alteracao,
        incluido_por=exame.incluido_por,
        alterado_por=exame.alterado_por
    )

    if form.validate_on_submit():
        exame.cod_empresa_principal = form.cod_empresa_principal.data
        exame.cod_exame = form.cod_exame.data
        exame.nome_exame = form.nome_exame.data
        exame.prazo = form.prazo.data

        exame.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
        exame.alterado_por = current_user.username
        
        database.session.commit()
    
        LogAcoes.registrar_acao(
            nome_tabela = 'Exame',
            tipo_acao = 'Alteração',
            id_registro = exame.id_exame,
            nome_registro = exame.nome_exame
        )
        
        flash(f'Exame atualizado com sucesso!', 'alert-success')
        return redirect(url_for('editar_exame', id_exame=exame.id_exame))
    
    return render_template(
        'exame/exame_editar.html',
        title='GRS+Connect',
        exame=exame,
        form=form
    )

@app.route('/exames/excluir', methods=['GET', 'POST'])
@login_required
@admin_required
def excluir_exame():
    exame = Exame.query.get(request.args.get('id_exame', type=int))
    
    try:
        database.session.delete(exame)
        database.session.commit()

        LogAcoes.registrar_acao(
            nome_tabela = 'Exame',
            tipo_acao = 'Exclusão',
            id_registro = exame.id_exame,
            nome_registro = exame.nome_exame,
        )

        flash(f'Exame excluído! Exame: {exame.id_exame} - {exame.nome_exame}', 'alert-danger')
        return redirect(url_for('buscar_exames'))
    except IntegrityError:
        database.session.rollback()
        flash(f'O Exame: {exame.id_exame} - {exame.nome_exame} não pode ser excluído, pois há outros registros associados a ele', 'alert-danger')
        return redirect(url_for('buscar_exames'))

