import datetime as dt

import pandas as pd
from flask import (flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required
from pytz import timezone

from src import UPLOAD_FOLDER, app, database
from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
from src.main.log_acoes.log_acoes import LogAcoes
from src.main.prestador.prestador import Prestador
from src.utils import admin_required

from .forms import FormBuscarPrestador, FormCriarPrestador, FormEditarPrestador


@app.route('/buscar_prestadores', methods=['GET', 'POST'])
@login_required
def buscar_prestadores():
    form = FormBuscarPrestador()

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )

    if form.validate_on_submit() and 'botao_buscar' in request.form:
        return redirect(
            url_for(
                'prestadores',
                cod_empresa_principal=form.cod_empresa_principal.data,
                id_prestador=form.id.data,
                cod=form.cod.data,
                nome=form.nome.data,
                ativo=form.ativo.data
            )
        )
    elif form.validate_on_submit() and 'botao_csv' in request.form:
        return redirect(
            url_for(
                'prestadores_csv',
                cod_empresa_principal=form.cod_empresa_principal.data,
                id_prestador=form.id.data,
                cod=form.cod.data,
                nome=form.nome.data,
                ativo=form.ativo.data
            )
        )

    return render_template(
        'prestador/busca.html',
        title='GRS+Connect',
        form=form
    )

@app.route('/prestadores')
@login_required
def prestadores():
    query = Prestador.buscar_prestadores(
        cod_empresa_principal=request.args.get(key='cod_empresa_principal', default=None, type=int),
        id_prestador=request.args.get(key='id_prestador', default=None, type=int),
        cod_prestador=request.args.get(key='cod', default=None, type=int),
        nome=request.args.get(key='nome', default=None, type=str),
        ativo=request.args.get(key='ativo', default=None, type=int)
    ).all()
    
    return render_template(
        'prestador/prestadores.html',
        title='GRS+Connect',
        lista_prestadores=query,
        qtd=len(query)
    )

@app.route('/prestadores/csv')
@login_required
def prestadores_csv():
    query = Prestador.buscar_prestadores(
        cod_empresa_principal=request.args.get(key='cod_empresa_principal', default=None, type=int),
        id_prestador=request.args.get(key='id_prestador', default=None, type=int),
        cod_prestador=request.args.get(key='cod', default=None, type=int),
        nome=request.args.get(key='nome', default=None, type=str),
        ativo=request.args.get(key='ativo', default=None, type=int)
    )

    df = pd.read_sql(sql=query.statement, con=database.session.bind)

    # criar arquivo dentro da pasta
    nome_arqv = f'Prestadores_{int(dt.datetime.now().timestamp())}.csv'
    camihno_arqv = f'{UPLOAD_FOLDER}/{nome_arqv}'
    df.to_csv(
        camihno_arqv,
        sep=';',
        index=False,
        encoding='iso-8859-1'
    )

    return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=nome_arqv)

@app.route('/prestadores/criar', methods=['GET', 'POST'])
@login_required
def criar_prestador():
    form = FormCriarPrestador()

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )

    if form.validate_on_submit():
        prestador = Prestador(
            cod_empresa_principal=form.cod_empresa_principal.data,
            cod_prestador=form.cod_prestador.data,
            nome_prestador=form.nome_prestador.data,
            emails=form.emails.data,
            ativo=form.ativo.data,
            solicitar_asos=form.solicitar_asos.data,
            cnpj=form.cnpj.data,
            uf=form.uf.data,
            razao_social=form.razao_social.data,
            data_inclusao=dt.datetime.now(tz=timezone('America/Sao_Paulo')),
            incluido_por=current_user.username
        )
        database.session.add(prestador)
        database.session.commit()
        
        LogAcoes.registrar_acao(
            nome_tabela='Prestador',
            tipo_acao='Inclusão',
            id_registro=prestador.id_prestador,
            nome_registro=prestador.nome_prestador
        )
        
        flash('Prestador criado com sucesso!', 'alert-success')
        return redirect(url_for('editar_prestador', id_prestador=prestador.id_prestador))
    return render_template('prestador/prestador_criar.html', form=form, title='GRS+Connect')

@app.route('/prestadores/editar', methods=['GET', 'POST'])
@login_required
def editar_prestador():    
    prestador = Prestador.query.get(request.args.get(key='id_prestador', type=int))

    form = FormEditarPrestador(
        cod_empresa_principal=prestador.cod_empresa_principal,
        cod_prestador=prestador.cod_prestador,
        nome_prestador=prestador.nome_prestador,
        emails=prestador.emails,
        ativo=prestador.ativo,
        solicitar_asos=prestador.solicitar_asos,
        cnpj=prestador.cnpj,
        uf=prestador.uf,
        razao_social=prestador.razao_social,
        data_inclusao=prestador.data_inclusao,
        data_alteracao=prestador.data_alteracao,
        incluido_por=prestador.incluido_por,
        alterado_por=prestador.alterado_por
    )

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )
   
    if form.validate_on_submit():
        prestador.cod_empresa_principal = form.cod_empresa_principal.data
        prestador.cod_prestador = form.cod_prestador.data
        prestador.nome_prestador = form.nome_prestador.data
        prestador.emails = form.emails.data
        prestador.ativo = form.ativo.data
        prestador.solicitar_asos = form.solicitar_asos.data
        prestador.cnpj = form.cnpj.data
        prestador.uf = form.uf.data
        prestador.razao_social = form.razao_social.data

        prestador.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
        prestador.alterado_por = current_user.username
        
        database.session.commit()
        
        LogAcoes.registrar_acao(
            nome_tabela = 'Prestador',
            tipo_acao = 'Alteração',
            id_registro = prestador.id_prestador,
            nome_registro = prestador.nome_prestador
        )
        
        flash(f'Prestador atualizado com sucesso!', 'alert-success')
        return redirect(url_for('editar_prestador', id_prestador=prestador.id_prestador))
        
    return render_template(
        'prestador/prestador_editar.html',
        title='GRS+Connect',
        prestador=prestador,
        form=form
    )

@app.route('/prestadores/excluir', methods=['GET', 'POST'])
@login_required
@admin_required
def excluir_prestador():
    prestador = Prestador.query.get(request.args.get(key='id_prestador', type=int))

    if not prestador.pedidos:
        database.session.delete(prestador)
        database.session.commit()

        LogAcoes.registrar_acao(
            nome_tabela = 'Prestador',
            tipo_acao = 'Exclusão',
            id_registro = prestador.id_prestador,
            nome_registro = prestador.nome_prestador,
        )
        
        flash(f'Prestador excluído! Prestador: {prestador.id_prestador} - {prestador.nome_prestador}', 'alert-danger')
        return redirect(url_for('buscar_prestadores'))
    else:
        flash(f'O Prestador: {prestador.id_prestador} - {prestador.nome_prestador} não pode ser excluído, pois há outros registros associados a ele', 'alert-danger')
        return redirect(url_for('buscar_prestadores'))
