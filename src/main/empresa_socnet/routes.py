from datetime import datetime

import pandas as pd
from flask import (flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from src import TIMEZONE_SAO_PAULO, UPLOAD_FOLDER, app, database
from src.main.empresa_socnet.empresa_socnet import EmpresaSOCNET
from src.utils import (get_data_from_args, get_data_from_form,
                       get_pagination_url_args)

from .forms import FormBuscarEmpresaSOCNET, FormEmpresaSOCNET

RESULTS_PER_PAGE = 200

@app.route('/buscar-empresas-socnet', methods=['GET', 'POST'])
@login_required
def buscar_empresas_socnet():
    form: FormBuscarEmpresaSOCNET = FormBuscarEmpresaSOCNET()
    form.socnet = True
    form.title = 'Buscar Empresas SOCNET'

    form.load_choices()

    if form.validate_on_submit():
        data = get_data_from_form(data=form.data)

        if 'botao_buscar' in request.form:
            return redirect(url_for('empresas_socnet', **data))
        elif 'botao_csv' in request.form:
            return redirect(url_for('empresas_socnet_csv', **data))

    return render_template('empresa/buscar_socnet.html', form=form)

@app.route('/empresas-socnet')
@login_required
def empresas_socnet():
    data = get_data_from_args(prev_form=FormBuscarEmpresaSOCNET(), data=request.args)
    query = EmpresaSOCNET.buscar_empresas(**data)

    page_num = request.args.get(key='page', type=int, default=1)
    query_pagination = query.paginate(page=page_num, per_page=RESULTS_PER_PAGE)

    pagination_url_args = get_pagination_url_args(data=request.args)

    return render_template(
        'empresa/listar_empresas_socnet.html',
        page_title='Empresas SOCNET',
        query=query_pagination,
        total=query.count(),
        results_per_page=RESULTS_PER_PAGE,
        pagination_url_args=pagination_url_args,
        pagination_endpoint='empresas_socnet',
        return_endpoint='buscar_empresas_socnet',
        socnet=True
    )

@app.route('/empresas-socnet/csv')
@login_required
def empresas_socnet_csv():
    data = get_data_from_args(prev_form=FormBuscarEmpresaSOCNET(), data=request.args)
    query = EmpresaSOCNET.buscar_empresas(**data)

    df = pd.read_sql(sql=query.statement, con=database.session.bind)

    timestamp = int(datetime.now().timestamp())
    nome_arqv = f'Empresas_SOCNET_{timestamp}.csv'
    camihno_arqv = f'{UPLOAD_FOLDER}/{nome_arqv}'
    df.to_csv(
        camihno_arqv,
        sep=';',
        index=False,
        encoding='iso-8859-1'
    )

    return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=nome_arqv)

@app.route('/empresas-socnet/criar', methods=['GET', 'POST'])
@login_required
def criar_empresa_socnet():
    form: FormEmpresaSOCNET = FormEmpresaSOCNET()
    form.title = 'Criar Empresa SOCNET'
    form.socnet = True

    form.load_choices()

    if form.validate_on_submit():
        empresa = EmpresaSOCNET(
            cod_empresa_principal=form.cod_empresa_principal.data,
            cod_empresa_referencia=form.cod_empresa_referencia.data,
            cod_empresa=form.cod_empresa.data,
            nome_empresa=form.nome_empresa.data,
            ativo=form.ativo.data,
            data_inclusao=datetime.now(tz=TIMEZONE_SAO_PAULO),
            incluido_por=current_user.username
        )

        database.session.add(empresa)
        database.session.commit()

        flash(f'Empresa criada com sucesso! {empresa.id_empresa} - {empresa.nome_empresa}', 'alert-success')

        return redirect(url_for('buscar_empresas_socnet'))

    return render_template('empresa/editar_socnet.html', form=form)

@app.route('/empresas-socnet/editar/<int:id_empresa>', methods=['GET', 'POST'])
@login_required
def editar_empresa_socnet(id_empresa):
    empresa: EmpresaSOCNET = EmpresaSOCNET.query.get(id_empresa)

    form: FormEmpresaSOCNET = FormEmpresaSOCNET(
        modo=2,
        id_empresa=id_empresa,
        cod_empresa_principal=empresa.cod_empresa_principal,
        cod_empresa_referencia=empresa.cod_empresa_referencia,
        cod_empresa=empresa.cod_empresa,
        nome_empresa=empresa.nome_empresa,
        ativo=empresa.ativo
    )
    form.title = 'Editar Empresa SOCNET'
    form.socnet = True

    form.load_choices()

    if form.validate_on_submit():
        empresa.cod_empresa_principal = form.cod_empresa_principal.data
        empresa.cod_empresa_referencia = form.cod_empresa_referencia.data

        empresa.cod_empresa = form.cod_empresa.data
        empresa.nome_empresa = form.nome_empresa.data

        empresa.ativo = form.ativo.data

        empresa.data_alteracao = datetime.now(tz=TIMEZONE_SAO_PAULO)
        empresa.alterado_por = current_user.username

        database.session.commit()

        flash(f'Empresa atualizada com sucesso!', 'alert-success')

        return redirect(url_for('editar_empresa_socnet', id_empresa=empresa.id_empresa))

    return render_template('empresa/editar_socnet.html', empresa=empresa, form=form)

@app.route('/empresas_socnet/excluir/<int:id_empresa>', methods=['GET', 'POST'])
@login_required
def excluir_empresa_socnet(id_empresa):
    empresa = EmpresaSOCNET.query.get(id_empresa)

    try:
        database.session.delete(empresa)
        database.session.commit()

        flash(f'Empresa excluída! {empresa.id_empresa} - {empresa.nome_empresa}', 'alert-danger')

        return redirect(url_for('buscar_empresas_socnet'))

    except IntegrityError:
        database.session.rollback()

        flash(f'A empresa {empresa.id_empresa} - {empresa.nome_empresa} não pode ser excluída, pois há outros registros associados a ela', 'alert-info')

        return redirect(url_for('editar_empresa_socnet', id_empresa=id_empresa))

