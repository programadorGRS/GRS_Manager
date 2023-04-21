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
from src.main.unidade.unidade import Unidade
from src.utils import admin_required, tratar_emails

from .forms import (FormBuscarUnidade, FormCriarUnidade, FormEditarUnidade,
                    FormManservAtualiza)


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

