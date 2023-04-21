import datetime as dt

import pandas as pd
from flask import (flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import login_required
from sqlalchemy import update

from src import UPLOAD_FOLDER, app, database
from src.main.empresa.empresa import Empresa
from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
from src.main.exame.exame import Exame
from src.main.funcionario.funcionario import Funcionario
from src.main.log_acoes.log_acoes import LogAcoes
from src.main.unidade.unidade import Unidade
from src.utils import admin_required

from .forms import (FormAtivarConvExames, FormBuscarConvEXames,
                    FormBuscarPedidoProcessamento, FormConfigurarsConvExames)
from .models import ConvExames, PedidoProcessamento


# BUSCA EMPRESAS----------------------------------------
@app.route('/convocacao_exames/empresas/buscar', methods=['GET', 'POST'])
@login_required
@admin_required
def buscar_conv_empresas():
    form = FormBuscarConvEXames()

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )

    if form.validate_on_submit():
        return redirect(
            url_for(
                'ativar_conv_empresas',
                cod_empresa_principal=form.cod_empresa_principal.data
            )
        )

    return render_template(
        'conv_exames/busca_configs.html',
        title='Manager',
        form=form
    )


# CONVOCACAO DE EXAMES EMPRESAS-----------------------------------------------------
@app.route('/convocacao_exames/empresas/ativar', methods=['GET', 'POST'])
@login_required
@admin_required
def ativar_conv_empresas():
    cod_empresa_principal = request.args.get('cod_empresa_principal', type=int)

    busca = (
        database.session.query(Empresa)
        .filter(Empresa.cod_empresa_principal == cod_empresa_principal)
        .order_by(Empresa.razao_social)
        .all()
    )

    form = FormAtivarConvExames()

    # filtrar conv exames sim e nao
    conv_exames_sim = [i for i in busca if i.conv_exames]
    conv_exames_nao = [i for i in busca if not i.conv_exames]
    
    if form.validate_on_submit():
        lista_atualizar = request.form.getlist('checkItem', type=int)

        q = database.session.execute(
            update(Empresa).
            where(Empresa.id_empresa.in_(lista_atualizar)).
            values(conv_exames=bool(int(form.conv_exames.data)))
        )
        database.session.commit()

        LogAcoes.registrar_acao(
            nome_tabela='Empresa',
            tipo_acao='Ativar/Desativar Conv Exames',
            id_registro=0,
            nome_registro='N/a',
            observacao=f'Qtd: {q.rowcount}'
        )

        # filtrar conv exames sim e nao
        conv_exames_sim = [i for i in busca if i.conv_exames]
        conv_exames_nao = [i for i in busca if not i.conv_exames]

        flash(f'Conv. de Exames atualizada com sucesso! Atualizados: {q.rowcount}', 'alert-success')
        redirect(url_for('ativar_conv_empresas', cod_empresa_principal=cod_empresa_principal))
    
    return render_template(
        'conv_exames/ativar_empresas.html',
        title='Manager',
        busca=busca,
        form=form,
        total=len(busca),
        sim=len(conv_exames_sim),
        nao=len(conv_exames_nao)
    )


# BUSCA UNIDADES----------------------------------------
@app.route('/convocacao_exames/unidades/buscar', methods=['GET', 'POST'])
@login_required
@admin_required
def buscar_conv_unidades():
    form = FormBuscarConvEXames()

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )

    if form.validate_on_submit():
        return redirect(
            url_for(
                'ativar_conv_unidades',
                cod_empresa_principal=form.cod_empresa_principal.data,
                id_empresa=form.id_empresa.data
            )
        )

    return render_template(
        'conv_exames/busca_configs.html',
        title='Manager',
        form=form,
        unidades=True
    )


# CONVOCACAO DE EXAMES UNIDADES-----------------------------------------------------
@app.route('/convocacao_exames/unidades/ativar', methods=['GET', 'POST'])
@login_required
@admin_required
def ativar_conv_unidades():
    cod_empresa_principal = request.args.get('cod_empresa_principal', type=int)
    id_empresa = request.args.get('id_empresa', default=None, type=int)

    busca = Unidade.buscar_unidades(
        cod_empresa_principal=cod_empresa_principal,
        id_empresa=id_empresa
    ).all()

    form = FormAtivarConvExames()

    # filtrar conv exames sim e nao
    conv_exames_sim = [i for i in busca if i.conv_exames]
    conv_exames_nao = [i for i in busca if not i.conv_exames]
    
    if form.validate_on_submit():
        lista_atualizar = request.form.getlist('checkItem', type=int)

        q = database.session.execute(
            update(Unidade).
            where(Unidade.id_unidade.in_(lista_atualizar)).
            values(conv_exames=bool(int(form.conv_exames.data)))
        )
        database.session.commit()

        LogAcoes.registrar_acao(
            nome_tabela='Empresa',
            tipo_acao='Ativar/Desativar Conv Exames',
            id_registro=0,
            nome_registro='N/a',
            observacao=f'Qtd: {q.rowcount}'
        )

        # filtrar conv exames sim e nao
        conv_exames_sim = [i for i in busca if i.conv_exames]
        conv_exames_nao = [i for i in busca if not i.conv_exames]

        flash(f'Conv. de Exames Unidades atualizada com sucesso! Atualizados: {q.rowcount}', 'alert-success')
        redirect(url_for('ativar_conv_unidades', cod_empresa_principal=cod_empresa_principal, id_empresa=id_empresa))
    
    return render_template(
        'conv_exames/ativar_unidades.html',
        title='Manager',
        busca=busca,
        form=form,
        total=len(busca),
        sim=len(conv_exames_sim),
        nao=len(conv_exames_nao)
    )


# BUSCA CONFIGS----------------------------------------
@app.route('/convocacao_exames/buscar_configuracoes', methods=['GET', 'POST'])
@login_required
@admin_required
def buscar_conv_exames_configs():
    form = FormBuscarConvEXames()

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )

    if form.validate_on_submit():
        return redirect(
            url_for(
                'conv_exames_configs',
                cod_empresa_principal=form.cod_empresa_principal.data
            )
        )

    return render_template(
        'conv_exames/busca_configs.html',
        title='Manager',
        form=form,
        configs=True
    )


# CONVOCACAO DE EXAMES CONFIGS-----------------------------------------------------
@app.route('/convocacao_exames/configuracoes', methods=['GET', 'POST'])
@login_required
@admin_required
def conv_exames_configs():
    form = FormConfigurarsConvExames()

    cod_empresa_principal = request.args.get('cod_empresa_principal', type=int)

    empresas = Empresa.buscar_empresas(
        cod_empresa_principal=cod_empresa_principal
    ).all()

    if form.validate_on_submit():
        lista_atualizar = request.form.getlist('checkItem', type=int)

        traduzir_vals = {1: True, 2: False}

        valores = {'conv_exames_selecao': form.selecao.data}

        if form.convocar_clinico.data:
            valores['conv_exames_convocar_clinico'] = traduzir_vals[form.convocar_clinico.data]
        if form.exames_pendentes.data:
            valores['conv_exames_pendentes'] = traduzir_vals[form.exames_pendentes.data]
        if form.conv_pendentes_pcmso.data:
            valores['conv_exames_pendentes_pcmso'] = traduzir_vals[form.conv_pendentes_pcmso.data]

        # nunca realizados
        if form.nunca_realizados.data == 1:
            valores['conv_exames_nunca_realizados'] = False
            valores['conv_exames_per_nunca_realizados'] = False            
        elif form.nunca_realizados.data == 2:
            valores['conv_exames_nunca_realizados'] = True
            valores['conv_exames_per_nunca_realizados'] = False
        elif form.nunca_realizados.data == 3:
            valores['conv_exames_nunca_realizados'] = False
            valores['conv_exames_per_nunca_realizados'] = True

        q = database.session.execute(
            update(Empresa).
            where(Empresa.id_empresa.in_(lista_atualizar)).
            values(valores)
        )
        database.session.commit()

        # registrar acao
        LogAcoes.registrar_acao(
            nome_tabela='Empresa',
            tipo_acao='Conv. Exames Alteração Configs.',
            id_registro=1,
            nome_registro=1,
            observacao=f'Qtd: {q.rowcount}'
        )
    
        flash(f'Configurações atualizadas com sucesso! Atualizados {q.rowcount}', 'alert-success')
        return redirect(url_for('conv_exames_configs', cod_empresa_principal=cod_empresa_principal))
    
    return render_template(
        'conv_exames/configs.html',
        title='Manager',
        form=form,
        busca=empresas
    )


# BUSCA PEDIDOS DE PROCESSAMENTO---------------------------------------------
@app.route('/convocacao_exames/pedidos_proc/busca', methods=['GET', 'POST'])
@login_required
def buscar_pedidos_proc():
    form: FormBuscarPedidoProcessamento = FormBuscarPedidoProcessamento()

    empresas_principais = (
        [('', 'Selecione')] +
        [(emp.cod, emp.nome) for emp in EmpresaPrincipal.query.all()]
    )
    
    form.cod_empresa_principal.choices = empresas_principais

    if form.validate_on_submit():
        parametros = {
            'cod_empresa_principal': form.cod_empresa_principal.data,
            'id_empresa': form.id_empresa.data,
            'data_inicio': form.data_inicio.data,
            'data_fim': form.data_fim.data,
            'cod_solicitacao': form.cod_solicitacao.data,
            'resultado_importado': form.resultado_importado.data,
            'obs': form.obs.data
        }

        parametros2: dict[str, any] = {}
        for chave, valor in parametros.items():
            if valor not in (None, ''):
                parametros2[chave] = valor

        # BUSCAR -----------------------------------
        if 'botao_buscar' in request.form:
            return redirect(url_for('pedidos_proc', **parametros2))

        # CRIAR CSV-----------------------------------------------
        elif 'botao_csv' in request.form:
            query = PedidoProcessamento.buscar_pedidos_proc(**parametros2)
            query = (
                query
                .join(EmpresaPrincipal, PedidoProcessamento.cod_empresa_principal == EmpresaPrincipal.cod)
                .join(Empresa, PedidoProcessamento.id_empresa == Empresa.id_empresa)
                .add_columns(Empresa.razao_social, EmpresaPrincipal.nome)
            )
            df = pd.read_sql(sql=query.statement, con=database.session.bind)
            df = df[PedidoProcessamento.COLUNAS_CSV]
            
            timestamp = int(dt.datetime.now().timestamp())
            nome_arqv = f'PedidosProcessamento_{timestamp}.csv'
            camihno_arqv = f'{UPLOAD_FOLDER}/{nome_arqv}'
            df.to_csv(
                camihno_arqv,
                sep=';',
                index=False,
                encoding='iso-8859-1'
            )
            return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=nome_arqv)

    return render_template(
        'conv_exames/busca_ped_proc.html',
        form=form,
        title='Manager'
    )


# PEDIDOS DE PROCESSAMENTO-----------------------------------------------------
@app.route('/convocacao_exames/pedidos_proc/busca/resultados', methods=['GET', 'POST'])
@login_required
def pedidos_proc():
    datas = {
        'data_inicio': request.args.get('data_inicio', type=str, default=None),
        'data_fim': request.args.get('data_fim', type=str, default=None)
    }
    for chave, valor in datas.items():
        if valor:
            datas[chave] = dt.datetime.strptime(valor, '%Y-%m-%d').date()

    query = PedidoProcessamento.buscar_pedidos_proc(
        cod_empresa_principal=request.args.get(key='cod_empresa_principal', type=int, default=None),
        data_inicio=datas['data_inicio'],
        data_fim=datas['data_fim'],
        id_empresa=request.args.get(key='id_empresa', default=None, type=int),
        cod_solicitacao=request.args.get(key='cod_solicitacao', default=None, type=int),
        resultado_importado=request.args.get(key='resultado_importado', default=None, type=int),
        obs=request.args.get(key='obs', default=None, type=str)
    ).all()

    qtd = len(query)

    return render_template(
        'conv_exames/pedidos_proc.html',
        title='Manager',
        lista_pedidos_proc=query,
        qtd=qtd
    )


@app.route('/convocacao_exames/pedidos_proc/gerar_relatorio', methods=['GET', 'POST'])
@login_required
def ped_proc_gerar_relatorio():
    ped_proc: PedidoProcessamento = PedidoProcessamento.query.get(request.args.get(key='id_proc', type=int))
    empresa: Empresa = Empresa.query.get(ped_proc.id_empresa)

    df = pd.read_sql(
        sql=(
            database.session.query(
                ConvExames,
                Empresa,
                Unidade,
                Funcionario,
                Exame
            )
            .join(Empresa, ConvExames.id_empresa == Empresa.id_empresa)
            .join(Unidade, ConvExames.id_unidade == Unidade.id_unidade)
            .join(Funcionario, ConvExames.id_funcionario == Funcionario.id_funcionario)
            .join(Exame, ConvExames.id_exame == Exame.id_exame)
            .filter(ConvExames.id_proc  == ped_proc.id_proc)
        ).statement,
        con=database.session.bind
    )
    
    pasta_zip = ConvExames.criar_relatorios(
        df=df,
        nome_empresa=empresa.razao_social,
        data_origem=ped_proc.data_criacao,
        gerar_ppt=True
    )

    if pasta_zip:
        return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=pasta_zip.split('/')[-1])
    else:
        flash('Sem resultado', 'alert-info')
        return redirect(url_for('buscar_pedidos_proc'))

