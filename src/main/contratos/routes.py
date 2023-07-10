import pandas as pd
from flask import (flash, redirect, render_template, send_from_directory,
                   url_for)
from flask_login import login_required
from flask_sqlalchemy import BaseQuery
from sqlalchemy import and_

from manager import UPLOAD_FOLDER, app, database
from manager.models import Empresa, Unidade, EmpresaPrincipal
from manager.modules.contratos.forms import FormBuscarContratos
from manager.modules.contratos.models import Contrato


@app.route('/contratos/busca', methods=['GET', 'POST'])
@login_required
def busca_contratos():
    form = FormBuscarContratos()

    if form.validate_on_submit():
        query_contratos: BaseQuery = Contrato.buscar_contratos(
            cod_empresa_principal=form.cod_empresa_principal.data,
            data_vencimento_inicio=form.data_vencimento_inicio.data,
            data_vencimento_fim=form.data_vencimento_fim.data,
            data_realizado_inicio=form.data_realizado_inicio.data,
            data_realizado_fim=form.data_realizado_fim.data,
            id_empresa=form.id_empresa.data,
            id_unidade=getattr(form, ''),
            cod_produto=form.cod_produto.data,
            nome_produto=form.nome_produto.data,
            situacao=form.situacao.data
        )

        query_contratos = (
            query_contratos.add_columns(
                EmpresaPrincipal.nome,
                Empresa.razao_social,
                Unidade.nome_unidade
            )
            .join(EmpresaPrincipal, Contrato.cod_empresa_principal == EmpresaPrincipal.cod)
            .join(Empresa, Contrato.id_empresa == Empresa.id_empresa)
            .outerjoin(Unidade, Contrato.id_unidade == Unidade.id_unidade)
        )

        df = pd.read_sql(sql=query_contratos.statement, con=database.session.bind)

        if not df.empty:
            empresa: Empresa = Empresa.query.get(form.id_empresa.data)
            pasta_zip: str = Contrato.criar_relatorios(df=df, nome_empresa=getattr(empresa, 'id_empresa', 'Todas'))

            return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=pasta_zip.split('/')[-1])
        else:
            flash('Pesquisa sem Resultado', 'alert-info')
            redirect(url_for('busca_contratos'))

    return render_template('contratos/busca.html', title='GRS+Connect', form=form)