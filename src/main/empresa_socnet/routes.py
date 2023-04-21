import datetime as dt

import pandas as pd
from flask import (flash, redirect, render_template, request,
                   send_from_directory, session, url_for)
from flask_login import current_user, login_required
from pytz import timezone
from sqlalchemy.exc import IntegrityError

from src import UPLOAD_FOLDER, app, database
from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
from src.main.empresa_socnet.empresa_socnet import EmpresaSOCNET
from src.main.log_acoes.log_acoes import LogAcoes
from src.utils import admin_required

from .forms import FormCriarEmpresaSOCNET, FormEditarEmpresaSOCNET


@app.route('/empresas_socnet')
@login_required
def empresas_socnet():
    lista_empresas = (
        EmpresaSOCNET.query
        .order_by(EmpresaSOCNET.nome_empresa)
        .all()
    )

    qtd = len(lista_empresas)
    
    session['previous'] = 'empresas_socnet'
    
    return render_template(
        'empresa/empresas_socnet.html',
        title='GRS+Connect',
        lista_empresas=lista_empresas,
        qtd=qtd
    )

@app.route('/empresas_socnet_csv')
@login_required
def empresas_socnet_csv():
    query = EmpresaSOCNET.query.order_by(EmpresaSOCNET.nome_empresa)
    
    df = pd.read_sql(sql=query.statement, con=database.session.bind)
    
    # criar arquivo dentro da pasta
    timestamp = int(dt.datetime.now().timestamp())
    nome_arqv = f'Empresas_SOCNET_{timestamp}.csv'
    camihno_arqv = f'{UPLOAD_FOLDER}/{nome_arqv}'
    df.to_csv(
        camihno_arqv,
        sep=';',
        index=False,
        encoding='iso-8859-1'
    )
    
    return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=nome_arqv)

@app.route('/empresas_socnet/criar', methods=['GET', 'POST'])
@login_required
def criar_empresa_socnet():
    form = FormCriarEmpresaSOCNET()

    opcoes = [('', 'Selecione')] + [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    form.cod_empresa_principal.choices = opcoes
    form.cod_empresa_referencia.choices = opcoes


    if form.validate_on_submit():
        empresa = EmpresaSOCNET(
            cod_empresa_principal=form.cod_empresa_principal.data,
            cod_empresa_referencia=form.cod_empresa_referencia.data,
            cod_empresa=form.cod_empresa.data,
            nome_empresa=form.nome_empresa.data,
            emails=form.emails.data,
            ativo=form.ativo.data,
            data_inclusao=dt.datetime.now(tz=timezone('America/Sao_Paulo')),
            incluido_por=current_user.username
        )
        database.session.add(empresa)
        database.session.commit()
        
        LogAcoes.registrar_acao(
            nome_tabela = 'EmpresaSOCNET',
            tipo_acao = 'Inclusão',
            id_registro = form.cod_empresa.data,
            nome_registro = form.nome_empresa.data
        )
        
        flash('Empresa criada com sucesso!', 'alert-success')
        return redirect(url_for('empresas_socnet'))
    
    return render_template('empresa/empresa_criar_socnet.html', form=form, title='GRS+Connect')

@app.route('/empresas_socnet/editar', methods=['GET', 'POST'])
@login_required
def editar_empresa_socnet():
    empresa = EmpresaSOCNET.query.get(request.args.get(key='id_empresa', type=int))

    form = FormEditarEmpresaSOCNET(
        cod_empresa_principal=empresa.cod_empresa_principal,
        cod_empresa_referencia=empresa.cod_empresa_referencia,
        cod_empresa=empresa.cod_empresa,
        nome_empresa=empresa.nome_empresa,
        emails=empresa.emails,
        ativo=empresa.ativo,
        data_inclusao=empresa.data_inclusao,
        data_alteracao=empresa.data_alteracao,
        incluido_por=empresa.incluido_por,
        alterado_por=empresa.alterado_por
    )

    opcoes = [('', 'Selecione')] + [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    form.cod_empresa_principal.choices = opcoes
    form.cod_empresa_referencia.choices = opcoes

    if form.validate_on_submit():
        empresa.cod_empresa_principal = form.cod_empresa_principal.data
        empresa.cod_empresa_referencia = form.cod_empresa_referencia.data
        empresa.cod_empresa = form.cod_empresa.data
        empresa.nome_empresa = form.nome_empresa.data
        empresa.emails=form.emails.data
        empresa.ativo = form.ativo.data

        empresa.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
        empresa.alterado_por = current_user.username
        
        database.session.commit()
    
        LogAcoes.registrar_acao(
            nome_tabela = 'EmpresaSOCNET',
            tipo_acao = 'Alteração',
            id_registro = empresa.id_empresa,
            nome_registro = empresa.nome_empresa
        )
        
        flash(f'Empresa atualizada com sucesso!', 'alert-success')
    

        return redirect(url_for('empresas_socnet'))
    
    return render_template(
        'empresa/empresa_editar_socnet.html',
        title='GRS+Connect',
        empresa=empresa,
        form=form
    )

@app.route('/empresas_socnet/excluir', methods=['GET', 'POST'])
@login_required
@admin_required
def excluir_empresa_socnet():
    empresa = EmpresaSOCNET.query.get(request.args.get('id_empresa', type=int))
    
    # excluir empresa
    try:
        database.session.delete(empresa)
        database.session.commit()

        LogAcoes.registrar_acao(
            nome_tabela = 'Empresa SOCNET',
            tipo_acao = 'Exclusão',
            id_registro = empresa.id_empresa,
            nome_registro = empresa.nome_empresa,
        )

        flash(f'Empresa excluída! Empresa: {empresa.id_empresa} - {empresa.nome_empresa}', 'alert-danger')
        return redirect(url_for('empresas_socnet'))
    except IntegrityError:
        database.session.rollback()
        flash(f'A empresa: {empresa.id_empresa} - {empresa.nome_empresa} não pode ser excluída, pois há outros registros associados a ela', 'alert-danger')
        return redirect(url_for('empresas_socnet'))
