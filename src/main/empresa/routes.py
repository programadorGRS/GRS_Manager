import datetime as dt

import pandas as pd
from flask import (flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required
from pytz import timezone
from sqlalchemy.exc import IntegrityError

from src import UPLOAD_FOLDER, app, database
from src.main.empresa.empresa import Empresa
from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
from src.main.log_acoes.log_acoes import LogAcoes
from src.utils import admin_required

from .forms import FormBuscarEmpresa, FormCriarEmpresa, FormEditarEmpresa


@app.route('/buscar_empresas', methods=['GET', 'POST'])
@login_required
def buscar_empresas():
    form = FormBuscarEmpresa()

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )

    if form.validate_on_submit() and 'botao_buscar' in request.form:
        return redirect(
            url_for(
                'empresas',
                cod_empresa_principal=form.cod_empresa_principal.data,
                id_empresa=form.id.data,
                cod=form.cod.data,
                nome=form.nome.data,
                ativo=form.ativo.data
            )
        )
    elif form.validate_on_submit() and 'botao_csv' in request.form:
        return redirect(
            url_for(
                'empresas_csv',
                cod_empresa_principal=form.cod_empresa_principal.data,
                id_empresa=form.id.data,
                cod=form.cod.data,
                nome=form.nome.data,
                ativo=form.ativo.data
            )
        )

    return render_template(
        'empresa/busca.html',
        title='GRS+Connect',
        form=form
    )

@app.route('/empresas')
@login_required
def empresas():

    query = Empresa.buscar_empresas(
        cod_empresa_principal=request.args.get(key='cod_empresa_principal', default=None, type=int),
        id_empresa=request.args.get(key='id_empresa', default=None, type=int),
        cod_empresa=request.args.get(key='cod', default=None, type=int),
        nome=request.args.get(key='nome', default=None, type=str),
        ativo=request.args.get(key='ativo', default=None, type=int)
    ).all()
    
    return render_template(
        'empresa/empresas.html',
        title='GRS+Connect',
        lista_empresas=query,
        qtd=len(query)
    )

@app.route('/empresas/csv')
@login_required
def empresas_csv():
    query = Empresa.buscar_empresas(
        cod_empresa_principal=request.args.get(key='cod_empresa_principal', default=None, type=int),
        id_empresa=request.args.get(key='id_empresa', default=None, type=int),
        cod_empresa=request.args.get(key='cod', default=None, type=int),
        nome=request.args.get(key='nome', default=None, type=str),
        ativo=request.args.get(key='ativo', default=None, type=int)
    )
    
    df = pd.read_sql(sql=query.statement, con=database.session.bind)
    
    # criar arquivo dentro da pasta
    nome_arqv = f'Empresas_{int(dt.datetime.now().timestamp())}.csv'
    camihno_arqv = f'{UPLOAD_FOLDER}/{nome_arqv}'
    df.to_csv(
        camihno_arqv,
        sep=';',
        index=False,
        encoding='iso-8859-1'
    )
    
    return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=nome_arqv)

@app.route('/empresas/criar', methods=['GET', 'POST'])
@login_required
def criar_empresa():
    form = FormCriarEmpresa()

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )

    if form.validate_on_submit():
        empresa = Empresa(
            cod_empresa_principal=form.cod_empresa_principal.data,
            cod_empresa=form.cod_empresa.data,
            razao_social_inicial=form.razao_social_inicial.data,
            razao_social=form.razao_social.data,
            nome_abrev=form.nome_abrev.data,
            cnpj=form.cnpj.data,
            uf=form.uf.data,
            emails=form.emails.data,
            conv_exames_emails=form.emails_conv_exames.data,
            absenteismo_emails=form.emails_absenteismo.data,
            exames_realizados_emails=form.emails_exames_realizados.data,
            conv_exames=form.conv_exames.data,
            ativo=form.ativo.data,
            data_inclusao=dt.datetime.now(tz=timezone('America/Sao_Paulo')),
            incluido_por=current_user.username
        )
        database.session.add(empresa)
        database.session.commit()
        
        LogAcoes.registrar_acao(
            nome_tabela = 'Empresa',
            tipo_acao = 'Inclusão',
            id_registro = int(form.cod_empresa.data),
            nome_registro = form.razao_social.data
        )
        
        flash('Empresa criada com sucesso!', 'alert-success')
        return redirect(url_for('editar_empresa', id_empresa=empresa.id_empresa))
    
    return render_template('empresa/empresa_criar.html', form=form, title='GRS+Connect')

@app.route('/empresas/editar', methods=['GET', 'POST'])
@login_required
def editar_empresa():
    # query empresa da pag atual
    empresa: Empresa = Empresa.query.get(request.args.get(key='id_empresa', type=int))

    form = FormEditarEmpresa(
        cod_empresa_principal = empresa.cod_empresa_principal,
        cod_empresa = empresa.cod_empresa,
        razao_social = empresa.razao_social,
        razao_social_inicial = empresa.razao_social_inicial,
        nome_abrev = empresa.nome_abrev,
        cnpj = empresa.cnpj,
        uf = empresa.uf,
        emails = empresa.emails,
        emails_conv_exames = empresa.conv_exames_emails,
        emails_absenteismo = empresa.absenteismo_emails,
        emails_exames_realizados = empresa.exames_realizados_emails,
        ativo = empresa.ativo,
        conv_exames = empresa.conv_exames,
        data_inclusao = empresa.data_inclusao,
        data_alteracao = empresa.data_alteracao,
        incluido_por = empresa.incluido_por,
        alterado_por = empresa.alterado_por
    )

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )

    if form.validate_on_submit():
        empresa.cod_empresa_principal = form.cod_empresa_principal.data
        empresa.cod_empresa = form.cod_empresa.data
        empresa.razao_social = form.razao_social.data
        empresa.razao_social_inicial = form.razao_social_inicial.data
        empresa.nome_abrev = form.nome_abrev.data
        empresa.cnpj = form.cnpj.data
        empresa.uf = form.uf.data
        empresa.emails = form.emails.data
        empresa.conv_exames_emails = form.emails_conv_exames.data
        empresa.absenteismo_emails = form.emails_absenteismo.data
        empresa.exames_realizados_emails = form.emails_exames_realizados.data
        empresa.ativo = form.ativo.data
        empresa.conv_exames = form.conv_exames.data

        empresa.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
        empresa.alterado_por = current_user.username
        
        database.session.commit()
    
        LogAcoes.registrar_acao(
            nome_tabela = 'Empresa',
            tipo_acao = 'Alteração',
            id_registro = empresa.cod_empresa,
            nome_registro = empresa.razao_social
        )
        
        flash(f'Empresa atualizada com sucesso!', 'alert-success')

        return redirect(url_for('editar_empresa', id_empresa=empresa.id_empresa))
    
    return render_template(
        'empresa/empresa_editar.html',
        title='GRS+Connect',
        empresa=empresa,
        form=form,
        qtd_unidades=len(empresa.unidades)
    )

@app.route('/empresas/excluir', methods=['GET', 'POST'])
@login_required
@admin_required
def excluir_empresa():
    empresa = Empresa.query.get(request.args.get('id_empresa', type=int))
    
    # excluir empresa
    try:
        database.session.delete(empresa)
        database.session.commit()

        LogAcoes.registrar_acao(
            nome_tabela = 'Empresa',
            tipo_acao = 'Exclusão',
            id_registro = int(empresa.id_empresa),
            nome_registro = empresa.razao_social,
        )

        flash(f'Empresa excluída! Empresa: {empresa.id_empresa} - {empresa.razao_social}', 'alert-danger')
        return redirect(url_for('buscar_empresas'))
    except IntegrityError:
        database.session.rollback()
        flash(f'A empresa: {empresa.id_empresa} - {empresa.razao_social} não pode ser excluída, pois há outros registros associados a ela', 'alert-danger')
        return redirect(url_for('buscar_empresas'))
