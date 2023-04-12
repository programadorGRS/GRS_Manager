import datetime as dt

import pandas as pd
from flask import (flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import login_required
from werkzeug.utils import secure_filename

from src import UPLOAD_FOLDER, app, database
from src.main.empresa.empresa import Empresa
from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
from src.main.unidade.unidade import Unidade
from src.modules.exames_realizados.forms import FormBuscarExamesRealizados
from src.modules.exames_realizados.models import ExamesRealizados
from src.utils import zipar_arquivos


# EXAMES REALIZADOS BUSCA---------------------------------------------
@app.route('/exames_realizados/busca', methods=['GET', 'POST'])
@login_required
def exames_realizados_busca():
    form = FormBuscarExamesRealizados()

    form.cod_empresa_principal.choices = [('', 'Selecione')] + [
        (i.cod, i.nome)
        for i in EmpresaPrincipal.query.order_by(EmpresaPrincipal.nome).all()
    ]

    if form.validate_on_submit():
        return redirect(
            url_for(
                'exames_realizados_relatorios',
                cod_empresa_principal=form.cod_empresa_principal.data,
                id_empresa=form.cod_empresa.data,
                id_unidade=form.cod_unidade.data,
                id_exame=form.cod_exame.data,
                data_inicio=form.data_inicio.data,
                data_fim=form.data_fim.data
                )
        )

    return render_template(
        'exames_realizados/busca.html',
        title='Manager',
        form=form
    )


# EXAMES REALIZADOS RELATORIOS---------------------------------------------
@app.route('/exames_realizados/relatorios', methods=['GET', 'POST'])
@login_required
def exames_realizados_relatorios():
    query = ExamesRealizados.buscar_exames_realizados(
        cod_empresa_principal=request.args.get(key='cod_empresa_principal', default=None, type=int),
        id_empresa=request.args.get(key='id_empresa', default=None, type=int),
        id_unidade=request.args.get(key='id_unidade', default=None, type=int),
        id_exame=request.args.get(key='id_exame', default=None, type=int),
        data_inicio=request.args.get(key='data_inicio', default=None),
        data_fim=request.args.get(key='data_fim', default=None)
    )

    df = pd.read_sql(sql=query.statement, con=database.session.bind)
    if not df.empty:
        id_empresa = request.args.get(key='id_empresa', default=None, type=int)
        if id_empresa:
            nome_empresa = Empresa.query.get(id_empresa).razao_social
        else:
            nome_empresa = EmpresaPrincipal.query.get(
                request.args.get(key='cod_empresa_principal', default=None, type=int)
            ).nome

        timestamp = int(dt.datetime.now().timestamp())
        secure_nome = secure_filename(nome_empresa).replace('.','_')
        caminho_arqvs = f"{UPLOAD_FOLDER}/ExamesRealizados_{secure_nome}_{timestamp}"
        
        id_unidade = request.args.get(key='id_unidade', default=None, type=int)
        if id_unidade:
            nome_unidade = Unidade.query.get(id_unidade).nome_unidade
            secure_nome = secure_filename(nome_unidade).replace('.','_')
            caminho_arqvs = f"{UPLOAD_FOLDER}/ExamesRealizados_{secure_nome}_{timestamp}"
        else:
            nome_unidade = None

        nome_excel = f'{caminho_arqvs}.xlsx'
        df2 = df[ExamesRealizados.colunas_planilha]
        df2.to_excel(nome_excel, index=False, freeze_panes=(1, 0))

        arquivos_zipar = [nome_excel]

        if len(df) >= 50:
            nome_ppt = f'{caminho_arqvs}.pptx'
            ExamesRealizados.criar_ppt(
                df=df,
                nome_arquivo=nome_ppt,
                nome_empresa=nome_empresa,
                nome_unidade=nome_unidade
            )
            arquivos_zipar.append(nome_ppt)

        pasta_zip = zipar_arquivos(
            caminhos_arquivos=arquivos_zipar,
            caminho_pasta_zip=f'{caminho_arqvs}.zip'
        )
        
        return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=pasta_zip.split('/')[-1])
    else:
        flash('A pesquisa não gerou dados', 'alert-info')
        return(redirect(url_for('exames_realizados_busca')))
