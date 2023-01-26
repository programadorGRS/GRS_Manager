import datetime as dt

import pandas as pd
from flask import (flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import login_required

from manager import UPLOAD_FOLDER, app, database
from manager.models import Empresa, EmpresaPrincipal, Unidade, Funcionario
from manager.modules.absenteismo.forms import FormBuscarAbsenteismo
from manager.modules.absenteismo.models import Licenca
from manager.utils import zipar_arquivos
from werkzeug.utils import secure_filename


# ABSENTEISMO BUSCA---------------------------------------------
@app.route('/absenteismo/busca', methods=['GET', 'POST'])
@login_required
def absenteismo_busca():
    form = FormBuscarAbsenteismo()

    form.cod_empresa_principal.choices = [('', 'Selecione')] + [
        (i.cod, i.nome)
        for i in EmpresaPrincipal.query.order_by(EmpresaPrincipal.nome).all()
    ]

    if form.validate_on_submit():
        return redirect(
            url_for(
                'absenteismo_relatorios',
                cod_empresa_principal=form.cod_empresa_principal.data,
                id_empresa=form.cod_empresa.data,
                id_unidade=form.cod_unidade.data,
                data_inicio=form.data_inicio.data,
                data_fim=form.data_fim.data
                )
        )

    return render_template(
        'absenteismo/busca.html',
        title='Manager',
        form=form
    )


# ABSENTEISMO RELATORIOS---------------------------------------------
@app.route('/absenteismo/relatorios', methods=['GET', 'POST'])
@login_required
def absenteismo_relatorios():
    query = Licenca.buscar_licencas(
        cod_empresa_principal=request.args.get(key='cod_empresa_principal', default=None, type=int),
        id_empresa=request.args.get(key='id_empresa', default=None, type=int),
        id_unidade=request.args.get(key='id_unidade', default=None, type=int),
        data_inicio=request.args.get(key='data_inicio', default=None),
        data_fim=request.args.get(key='data_fim', default=None)
    )

    df = pd.read_sql(sql=query.statement, con=database.session.bind)
    if not df.empty:
        nome_empresa = EmpresaPrincipal.query.get(request.args.get(key='cod_empresa_principal', type=int)).nome
        nome_unidade = None
        qtd_ativos = (
            database.session.query(Funcionario)
            .filter(Funcionario.situacao == 'Ativo')
            .filter(Funcionario.cod_empresa_principal == request.args.get(key='cod_empresa_principal', default=None, type=int))
            .count()
        )

        id_empresa = request.args.get(key='id_empresa', default=None, type=int)
        if id_empresa:
            nome_empresa = Empresa.query.get(id_empresa).razao_social
            qtd_ativos = (
                database.session.query(Funcionario)
                .filter(Funcionario.situacao == 'Ativo')
                .filter(Funcionario.id_empresa == id_empresa)
                .count()
            )

            id_unidade = request.args.get(key='id_unidade', default=None, type=int)
            if id_unidade:
                nome_unidade = Unidade.query.get(id_unidade).nome_unidade
                qtd_ativos = (
                    database.session.query(Funcionario)
                    .filter(Funcionario.situacao == 'Ativo')
                    .filter(Funcionario.id_unidade == id_unidade)
                    .count()
                )

        caminho_arqvs = f'{UPLOAD_FOLDER}/Absenteismo_{secure_filename(nome_empresa).replace("/", "")}_{int(dt.datetime.now().timestamp())}'
        nome_excel = f'{caminho_arqvs}.xlsx'
        df2 = df[Licenca.COLUNAS_PLANILHA]
        df2.to_excel(nome_excel, index=False, freeze_panes=(1, 0))

        nome_ppt = f'{caminho_arqvs}.pptx'
        Licenca.criar_ppt(
            df=df,
            funcionarios_ativos=qtd_ativos,
            nome_arquivo=nome_ppt,
            nome_empresa=nome_empresa,
            nome_unidade=nome_unidade
        )

        pasta_zip = zipar_arquivos(
            caminhos_arquivos=[nome_excel, nome_ppt],
            caminho_pasta_zip=f'{caminho_arqvs}.zip'
        )
        
        return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=pasta_zip.split('/')[-1])
    
    else:
        flash('A pesquisa não gerou dados', 'alert-info')
        return(redirect(url_for('absenteismo_busca')))
