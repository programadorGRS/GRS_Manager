import datetime as dt
from io import StringIO
from sys import getsizeof

import numpy as np
import pandas as pd
from flask import (flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required
from flask_mail import Attachment, Message
from pandas.errors import IntCastingNaNError
from pytz import timezone
from sqlalchemy.exc import IntegrityError

from src import TIMEZONE_SAO_PAULO, UPLOAD_FOLDER, app, database
from src.forms import (FormBuscarEmpresa, FormBuscarExames,
                       FormBuscarPrestador, FormBuscarUnidade,
                       FormCriarEmpresa, FormCriarExame, FormCriarPrestador,
                       FormCriarUnidade, FormEditarEmpresa, FormEditarExame,
                       FormEditarPrestador, FormEditarUnidade,
                       FormImportarDados, FormManservAtualiza)
from src.main.empresa.empresa import Empresa
from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
from src.main.exame.exame import Exame
from src.main.log_acoes.log_acoes import LogAcoes
from src.main.pedido.pedido import Pedido
from src.main.prestador.prestador import Prestador
from src.main.status.status import Status
from src.main.unidade.unidade import Unidade
from src.utils import admin_required, tratar_emails

# TODO: incluir funcoes de atualizar status em massa (csv) para RAC e os outros campos novos


# BUSCA EMPRESAS----------------------------------------
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


# EMPRESAS----------------------------------------
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


# EMPRESAS GERAR CSV----------------------------------------
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


# CRIAR EMPRESA ----------------------------------------
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


# EDITAR EMPRESA-----------------------------------------------------------
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


# EXCLUIR EMPRESA-----------------------------------------------------------
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


# BUSCA UNIDADES----------------------------------------
@app.route('/buscar_unidades', methods=['GET', 'POST'])
@login_required
def buscar_unidades():
    form = FormBuscarUnidade()

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )

    if form.validate_on_submit() and 'botao_buscar' in request.form:
        return redirect(
            url_for(
                'unidades',
                cod_empresa_principal=form.cod_empresa_principal.data,
                id_empresa=form.id_empresa.data,
                id_unidade=form.id.data,
                cod_unidade=form.cod.data,
                nome=form.nome.data,
                ativo=form.ativo.data
            )
        )
    elif form.validate_on_submit() and 'botao_csv' in request.form:
        return redirect(
            url_for(
                'unidades_csv',
                cod_empresa_principal=form.cod_empresa_principal.data,
                id_empresa=form.id_empresa.data,
                id_unidade=form.id.data,
                cod_unidade=form.cod.data,
                nome=form.nome.data,
                ativo=form.ativo.data
            )
        )

    return render_template(
        'unidade/busca.html',
        title='GRS+Connect',
        form=form
    )


# UNIDADES----------------------------------------
@app.route('/unidades')
@login_required
def unidades():

    query = Unidade.buscar_unidades(
        cod_empresa_principal=request.args.get(key='cod_empresa_principal', default=None, type=int),
        id_empresa=request.args.get(key='id_empresa', default=None, type=int),
        id_unidade=request.args.get(key='id_unidade', default=None, type=int),
        cod_unidade=request.args.get(key='cod_unidade', default=None, type=str),
        nome=request.args.get(key='nome', default=None, type=str),
        ativo=request.args.get(key='ativo', default=None, type=int)
    ).all()

    return render_template(
        'unidade/unidades.html',
        title='GRS+Connect',
        lista_unidades=query,
        qtd=len(query)
    )


# UNIDADES GERAR CSV----------------------------------------
@app.route('/unidades/csv')
@login_required
def unidades_csv():
    query = Unidade.buscar_unidades(
        cod_empresa_principal=request.args.get(key='cod_empresa_principal', default=None, type=int),
        id_empresa=request.args.get(key='id_empresa', default=None, type=int),
        id_unidade=request.args.get(key='id_unidade', default=None, type=int),
        cod_unidade=request.args.get(key='cod_unidade', default=None, type=str),
        nome=request.args.get(key='nome', default=None, type=str),
        ativo=request.args.get(key='ativo', default=None, type=int)
    )

    df = pd.read_sql(sql=query.statement, con=database.session.bind)

    df = df[Unidade.COLUNAS_PLANILHA]
    
    nome_arqv = f'Unidades_{int(dt.datetime.now().timestamp())}.csv'
    camihno_arqv = f'{UPLOAD_FOLDER}/{nome_arqv}'
    df.to_csv(
        camihno_arqv,
        sep=';',
        index=False,
        encoding='iso-8859-1'
    )
    return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=nome_arqv)


# CRIAR UNIDADE ----------------------------------------
@app.route('/unidades/criar', methods=['GET', 'POST'])
@login_required
def criar_unidade():
    form = FormCriarUnidade()

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )

    if form.validate_on_submit():
        unidade = Unidade(
            cod_empresa_principal=form.cod_empresa_principal.data,
            id_empresa=form.id_empresa.data,
            cod_unidade=form.cod_unidade.data,
            nome_unidade=form.nome_unidade.data,
            razao_social=form.razao_social.data,
            cod_rh=form.cod_rh.data,
            cnpj=form.cnpj.data,
            uf=form.uf.data,
            emails=form.emails.data,
            conv_exames_emails=form.emails_conv_exames.data,
            absenteismo_emails=form.emails_absenteismo.data,
            exames_realizados_emails=form.emails_exames_realizados.data,
            ativo=form.ativo.data,
            conv_exames=form.conv_exames.data,
            data_inclusao=dt.datetime.now(tz=timezone('America/Sao_Paulo')),
            incluido_por=current_user.username
        )
        database.session.add(unidade)
        database.session.commit()

        LogAcoes.registrar_acao(
            nome_tabela = 'Unidade',
            tipo_acao = 'Inclusão',
            id_registro = unidade.id_unidade,
            nome_registro = unidade.nome_unidade
        )
        
        flash('Unidade criada com sucesso!', 'alert-success')
        return redirect(url_for('editar_unidade', id_unidade=unidade.id_unidade))
    
    return render_template(
        'unidade/unidade_criar.html',
        form=form,
        title='GRS+Connect'
    )


# EDITAR UNIDADE-----------------------------------------------------------
@app.route('/unidades/editar', methods=['GET', 'POST'])
@login_required
def editar_unidade():
    unidade: Unidade = Unidade.query.get(request.args.get(key='id_unidade', type=int))

    form = FormEditarUnidade(
        cod_empresa_principal=unidade.cod_empresa_principal,
        id_empresa=unidade.id_empresa,
        cod_unidade=unidade.cod_unidade,
        nome_unidade=unidade.nome_unidade,
        razao_social=unidade.razao_social,
        cod_rh=unidade.cod_rh,
        cnpj=unidade.cnpj,
        uf=unidade.uf,
        emails=unidade.emails,
        emails_conv_exames = unidade.conv_exames_emails,
        emails_absenteismo = unidade.absenteismo_emails,
        emails_exames_realizados = unidade.exames_realizados_emails,
        ativo=unidade.ativo,
        conv_exames=unidade.conv_exames,
        data_inclusao=unidade.data_inclusao,
        data_alteracao=unidade.data_alteracao,
        incluido_por=unidade.incluido_por,
        alterado_por=unidade.alterado_por
    )

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )

    form.id_empresa.choices = (
        [('', 'Selecione')] +
        [
            (i.id_empresa, i.razao_social)
            for i in Empresa.query
            .filter_by(cod_empresa_principal=unidade.cod_empresa_principal)
            .order_by(Empresa.razao_social)
            .all()
        ]
    )

    if form.validate_on_submit():
        unidade.cod_empresa_principal = form.cod_empresa_principal.data
        unidade.id_empresa = form.id_empresa.data
        unidade.cod_unidade = form.cod_unidade.data
        unidade.nome_unidade = form.nome_unidade.data
        unidade.ativo = form.ativo.data
        unidade.emails = form.emails.data
        unidade.conv_exames_emails = form.emails_conv_exames.data
        unidade.absenteismo_emails = form.emails_absenteismo.data
        unidade.exames_realizados_emails = form.emails_exames_realizados.data
        unidade.conv_exames = form.conv_exames.data

        unidade.cod_rh = form.cod_rh.data
        unidade.cnpj = form.cnpj.data
        unidade.uf = form.uf.data
        unidade.razao_social = form.razao_social.data

        unidade.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
        unidade.alterado_por = current_user.username
        
        database.session.commit()
    
        LogAcoes.registrar_acao(
            nome_tabela = 'Unidade',
            tipo_acao = 'Alteração',
            id_registro = unidade.id_unidade,
            nome_registro = unidade.nome_unidade
        )
        
        flash(f'Unidade atualizada com sucesso!', 'alert-success')
        return redirect(url_for('editar_unidade', id_unidade=unidade.id_unidade))
    
    return render_template(
        'unidade/unidade_editar.html',
        title='GRS+Connect',
        unidade=unidade,
        form=form
    )


# EXCLUIR UNIDADE-----------------------------------------------------------
@app.route('/unidades/excluir', methods=['GET', 'POST'])
@login_required
@admin_required
def excluir_unidade():
    unidade = Unidade.query.get(request.args.get(key='id_unidade', type=int))

    try:
        database.session.delete(unidade)
        database.session.commit()

        LogAcoes.registrar_acao(
            nome_tabela = 'Unidade',
            tipo_acao = 'Exclusão',
            id_registro = int(unidade.id_unidade),
            nome_registro = unidade.nome_unidade,
        )
        
        flash(f'Unidade excluída! Unidade: {unidade.id_unidade} - {unidade.nome_unidade}', 'alert-danger')
        return redirect(url_for('buscar_unidades'))
    except IntegrityError:
        database.session.rollback()
        flash(f'A Unidade: {unidade.id_unidade} - {unidade.nome_unidade} não pode ser excluída, pois há outros registros associados a ela', 'alert-danger')
        return redirect(url_for('buscar_unidades'))


# EXTERNO - ATUALIZAR EMAILS UNIDADES ---------------------------------------------
@app.route('/unidades/atualizar_emails/manserv', methods=['GET', 'POST'])
def unidades_atualizar_emails_manserv():
    form = FormManservAtualiza()

    empresas_manserv = [529769, 529768, 529759, 529765, 529766]

    query_empresas= (
        database.session.query(
            Empresa.id_empresa,
            Empresa.razao_social
        )
        .filter(Empresa.cod_empresa.in_(empresas_manserv))
        .order_by(Empresa.razao_social)
        .all()
    )

    form.empresa.choices = (
        [('', 'Selecione')] + 
        [(i.id_empresa, i.razao_social) for i in query_empresas]
    )

    if form.validate_on_submit():
        unidade: Unidade = Unidade.query.get(int(form.unidade.data))

        if unidade.conv_exames_emails:
            unidade.conv_exames_emails = unidade.conv_exames_emails + ';' + tratar_emails(form.emails_conv_exames.data)
        else:
            unidade.conv_exames_emails = tratar_emails(form.emails_conv_exames.data)

        unidade.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
        unidade.alterado_por = f'Guest/Cliente: {form.nome.data}'
        database.session.commit()

        LogAcoes.registrar_acao(
            nome_tabela='Unidade',
            tipo_acao='Atualização Email',
            id_registro=int(unidade.id_unidade),
            nome_registro=unidade.nome_unidade,
            id_usuario=9999,
            username=f'Guest/Cliente: {form.nome.data}'
        )

        flash(f'Dados enviados com sucesso! {form.nome.data} - {unidade.nome_unidade}', 'alert-success')
        return redirect(url_for('unidades_atualizar_emails_manserv'))

    return render_template(
        'unidade/atualizar_emails.html',
        title='GRS+Connect',
        form=form
    )


# BUSCA PRESTADORES----------------------------------------
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


# PRESTADORES----------------------------------------
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


# PRESTADORES GERAR CSV----------------------------------------
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


# CRIAR PRESTADOR-----------------------------
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


# EDITAR PRESTADOR-----------------------------------------------------------
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


# EXCLUIR PRESTADOR-----------------------------------------------------------
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


# BUSCA EXAMES----------------------------------------
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


# EXAMES----------------------------------------
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


# EXAMES GERAR CSV----------------------------------------
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


# CRIAR EXAME ----------------------------------------
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


# EDITAR EXAME-----------------------------------------------------------
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


# EXCLUIR EXAME-----------------------------------------------------------
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


# IMPORTAR DADOS-----------------------------------------------------------
@app.route('/importar_dados/atualizar', methods=['GET', 'POST'])
@login_required
@admin_required
def importar_dados_atualizar():
    form = FormImportarDados()

    if form.validate_on_submit():
        # ler arquivo
        arqv = request.files['csv']
        data = arqv.read().decode('iso-8859-1')

        # tamnho maximo
        max_size_mb = app.config['MAX_UPLOAD_SIZE_MB']
        max_bytes = max_size_mb * 1024 * 1024

        if getsizeof(data) > max_bytes:
            flash(f'O arquivo deve ser menor que {max_size_mb} MB', 'alert-danger')
            return redirect(url_for('importar_dados_atualizar'))
        
        else:
            # ler string como objeto para csv
            df = pd.read_csv(
                filepath_or_buffer=StringIO(data),
                sep=';',
                encoding='iso-8859-1',
            )

            tabela = int(form.tabela.data)
            
            match tabela:
                case 1: # Empresa
                    colunas = ['id_empresa', 'emails']
                    if list(df.columns) == colunas:
                        colunas_atualizadas = list(df.columns[1:])
                        df.drop_duplicates(subset='id_empresa', inplace=True, ignore_index=True)
                        if 'emails' in df.columns:
                            df['emails'] = list(map(tratar_emails, df['emails']))
                        df = df.to_dict(orient='records')
                        database.session.bulk_update_mappings(Empresa, df)
                        database.session.commit()
                        flash(f'Empresas atualizadas com sucesso! Linhas: {len(df)}, Colunas: {colunas_atualizadas}', 'alert-success')
                        return redirect(url_for('importar_dados_atualizar'))
                    else:
                        flash('Erro ao validar as Colunas do Arquivo', 'alert-danger')
                        return redirect(url_for('importar_dados_atualizar'))

                case 2: # Unidade
                    colunas = ['id_unidade', 'emails']
                    if list(df.columns) == colunas:
                        colunas_atualizadas = list(df.columns[1:])
                        df.drop_duplicates(subset='id_unidade', inplace=True, ignore_index=True)
                        if 'emails' in df.columns:
                            df['emails'] = list(map(tratar_emails, df['emails']))
                        df = df.to_dict(orient='records')
                        database.session.bulk_update_mappings(Unidade, df)
                        database.session.commit()
                        flash(f'Unidades atualizadas com sucesso! Linhas: {len(df)}, Colunas: {colunas_atualizadas}', 'alert-success')
                        return redirect(url_for('importar_dados_atualizar'))
                    else:
                        flash('Erro ao validar as Colunas do Arquivo', 'alert-danger')
                        return redirect(url_for('importar_dados_atualizar'))

                case 3: # Exame
                    colunas = ['id_exame', 'prazo']
                    if list(df.columns) == colunas:
                        colunas_atualizadas = list(df.columns[1:])
                        df.drop_duplicates(subset='id_exame', inplace=True, ignore_index=True)
                        df = df.to_dict(orient='records')
                        database.session.bulk_update_mappings(Exame, df)
                        database.session.commit()
                        flash(f'Exames atualizados com sucesso! Linhas: {len(df)}, Colunas: {colunas_atualizadas}', 'alert-success')
                        return redirect(url_for('importar_dados_atualizar'))
                    else:
                        flash('Erro ao validar as Colunas do Arquivo', 'alert-danger')
                        return redirect(url_for('importar_dados_atualizar'))

    return render_template('/importar_dados.html', title='GRS+Connect', form=form)

