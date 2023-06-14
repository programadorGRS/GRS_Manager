import os
from datetime import datetime

import pandas as pd
from flask import (flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import login_required
from sqlalchemy import update
from werkzeug.utils import secure_filename

from src import UPLOAD_FOLDER, app, database
from src.main.empresa.empresa import Empresa
from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
from src.main.exame.exame import Exame
from src.main.funcionario.funcionario import Funcionario
from src.main.log_acoes.log_acoes import LogAcoes
from src.main.unidade.unidade import Unidade
from src.utils import admin_required, get_data_from_form, zipar_arquivos

from .forms import (FormAtivarConvExames, FormBuscarConvEXames,
                    FormBuscarPedidoProcessamento, FormConfigurarsConvExames,
                    FormGerarRelatorios)
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

@app.route('/convocacao_exames/pedidos_proc/busca', methods=['GET', 'POST'])
@login_required
def buscar_pedidos_proc():
    form = FormBuscarPedidoProcessamento()
    form.load_choices()
    form.title = 'Buscar Pedidos de Processamento'

    if form.validate_on_submit():
        params = get_data_from_form(form.data)

        if 'botao_buscar' in request.form:
            return redirect(url_for('listar_pedidos_proc', **params))

        elif 'botao_csv' in request.form:
            return redirect(url_for('csv_pedidos_proc', **params))

    return render_template('conv_exames/busca_ped_proc.html', form=form)

@app.route('/convocacao_exames/pedidos_proc/busca/resultados', methods=['GET', 'POST'])
@login_required
def listar_pedidos_proc():
    prev_form = FormBuscarPedidoProcessamento()
    args = prev_form.get_url_args(data=request.args)

    query = PedidoProcessamento.buscar_pedidos_proc(**args)

    total = query.count()

    return render_template('conv_exames/pedidos_proc.html', query=query, total=total)

@app.route('/convocacao_exames/pedidos_proc/busca/csv')
@login_required
def csv_pedidos_proc():
        prev_form = FormBuscarPedidoProcessamento()
        args = prev_form.get_url_args(data=request.args)

        query = PedidoProcessamento.buscar_pedidos_proc(**args)

        query = (
            query
            .join(EmpresaPrincipal, PedidoProcessamento.cod_empresa_principal == EmpresaPrincipal.cod)
            .add_columns(Empresa.razao_social, EmpresaPrincipal.nome, Empresa.ativo)
        )

        df = pd.read_sql(sql=query.statement, con=database.session.bind)
        df = df[PedidoProcessamento.COLUNAS_CSV]

        timestamp = int(datetime.now().timestamp())
        nome_arqv = f'PedidosProcessamento_{timestamp}.csv'
        camihno_arqv = f'{UPLOAD_FOLDER}/{nome_arqv}'
        df.to_csv(
            camihno_arqv,
            sep=';',
            index=False,
            encoding='iso-8859-1'
        )

        return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=nome_arqv)

@app.route('/convocacao_exames/pedidos_proc/<int:id_proc>', methods=['GET', 'POST'])
@login_required
def pag_pedido_proc(id_proc):
    ped_proc = PedidoProcessamento.query.get(id_proc)

    form: FormGerarRelatorios = FormGerarRelatorios()
    form.form_action = url_for('ped_proc_gerar_reports', id_proc=id_proc)
    form.load_choices(id_empresa=ped_proc.id_empresa)

    form.title = f'Pedido de Processamento #{ped_proc.id_proc}'
    form.sub_title = 'Gerar Relatórios'

    if form.validate_on_submit():
        return redirect(url_for('ped_proc_gerar_reports', id_proc=id_proc))

    return render_template('conv_exames/gerar_relatorios.html', form=form, ped_proc=ped_proc, ppt_trigger=ConvExames.PPT_TRIGGER)

@app.route('/convocacao_exames/pedidos_proc/<int:id_proc>/gerar_relatorios', methods=['GET', 'POST'])
@login_required
def ped_proc_gerar_reports(id_proc):
    ped_proc: PedidoProcessamento = PedidoProcessamento.query.get(id_proc)

    empresa: Empresa = Empresa.query.get(ped_proc.id_empresa)

    prev_form = FormGerarRelatorios()
    args: dict[str, any] = prev_form.get_request_form_data(data=request.form)

    query = (
        database.session.query(
            ConvExames,
            Empresa.razao_social,
            Unidade.nome_unidade,
            Funcionario.cpf_funcionario,
            Funcionario.nome_funcionario,
            Funcionario.cod_setor,
            Funcionario.nome_setor,
            Funcionario.cod_cargo,
            Funcionario.nome_cargo,
            Exame.nome_exame
        )
        .join(Empresa, ConvExames.id_empresa == Empresa.id_empresa)
        .join(Unidade, ConvExames.id_unidade == Unidade.id_unidade)
        .join(Funcionario, ConvExames.id_funcionario == Funcionario.id_funcionario)
        .join(Exame, ConvExames.id_exame == Exame.id_exame)
        .filter(ConvExames.id_proc  == ped_proc.id_proc)
    )

    nome_unidade = 'Todas'
    unidades: list[int] = args.get('unidades')
    if unidades:
        query = query.filter(ConvExames.id_unidade.in_(unidades))

        if len(unidades) == 1:
            nome_unidade = Unidade.query.get(unidades[0]).nome_unidade
        elif len(unidades) > 1:
            nome_unidade = 'Várias'

    arquivos = ConvExames.criar_relatorios2(
        query=query,
        nome_empresa=empresa.razao_social,
        gerar_ppt=args.get('gerar_ppt'),
        nome_unidade=nome_unidade,
        data_origem=ped_proc.data_criacao,
        filtro_status=args.get('status'),
        filtro_a_vencer=args.get('a_vencer')
    )

    if arquivos:
        nome_empresa = secure_filename(empresa.razao_social).replace('.', '_').upper()
        timestamp = int(datetime.now().timestamp())
        nome_pasta = os.path.join(UPLOAD_FOLDER, f'ConvExames_{nome_empresa}_{timestamp}.zip')

        pasta_zip = zipar_arquivos(
            caminhos_arquivos=list(arquivos.values()),
            caminho_pasta_zip=nome_pasta
        )
        return send_from_directory(
            directory=UPLOAD_FOLDER,
            path='/',
            filename=pasta_zip.split('/')[-1]
        )
    else:
        flash('Sem resultados', 'alert-info')
        return redirect(url_for('pag_pedido_proc', id_proc=ped_proc.id_proc))


