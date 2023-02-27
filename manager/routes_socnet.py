import datetime as dt
import os
from sys import getsizeof

import numpy as np
import pandas as pd
from flask import (flash, redirect, render_template, request,
                   send_from_directory, session, url_for)
from flask_login import current_user, login_required
from flask_mail import Attachment, Message
from pytz import timezone
from sqlalchemy import delete, insert
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from manager import (DOWNLOAD_FOLDER, TIMEZONE_SAO_PAULO, UPLOAD_FOLDER, app,
                     database, mail)
from manager.email import corpo_email_padrao
from manager.forms import (FormAtualizarStatus, FormEnviarEmails,
                           FormGrupoPrestadores)
from manager.forms_socnet import (FormBuscarASOSOCNET,
                                  FormCarregarPedidosSOCNET,
                                  FormCriarEmpresaSOCNET,
                                  FormEditarEmpresaSOCNET,
                                  FormEditarPedidoSOCNET, FormUpload)
from manager.models import (EmpresaPrincipal, Grupo, LogAcoes, Prestador,
                            Status, StatusLiberacao, StatusRAC, TipoExame)
from manager.models_socnet import (EmpresaSOCNET, PedidoSOCNET,
                                   grupo_empresa_socnet)
from manager.utils import admin_required

# NOTE: ainda nao e possivel implantar as funcoes de prvisao de liberacao e tag_prev_liberacao \
# para isso, e necessario ter acesso aos codigos dos exames da base de cada cliente SOCNET

@app.route('/busca_socnet', methods=['GET', 'POST'])
@login_required
def busca_socnet():
    form = FormBuscarASOSOCNET()
    # opcoes dinamicas de busca, como empresa, unidade \
    # prestador etc, sao incluidas via fetch no javascript
    
    # opcoes emp principal
    form.cod_empresa_principal.choices = (
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )
    # opcoes status
    form.id_status.choices = (
        [('', 'Selecione')] +
        [(i.id_status, i.nome_status) for i in Status.query.all()]
    )
    form.id_status_rac.choices = (
        [('', 'Selecione')] +
        [(i.id_status, i.nome_status) for i in StatusRAC.query.all()]
    )

    if form.validate_on_submit():
        parametros:  dict[str, any] = {
            'pesquisa_geral': int(form.pesquisa_geral.data),
            'cod_empresa_principal': form.cod_empresa_principal.data,
            'data_inicio': form.data_inicio.data,
            'data_fim': form.data_fim.data,
            'id_status': form.id_status.data,
            'id_status_rac': form.id_status_rac.data,
            'seq_ficha': form.seq_ficha.data,
            'id_empresa': form.id_empresa.data,
            'id_prestador': form.id_prestador.data,
            'nome_funcionario': form.nome_funcionario.data,
            'obs': form.obs.data
        }

        parametros2: dict[str, any] = {}
        for chave, valor in parametros.items():
            if valor not in (None, ''):
                parametros2[chave] = valor

        if 'btn_buscar' in request.form:
            return redirect(url_for('atualizar_status_socnet', **parametros2))

        elif 'btn_emails' in request.form:
            return redirect(url_for('enviar_emails_socnet', **parametros2))

        elif 'btn_csv' in request.form:
            query = PedidoSOCNET.buscar_pedidos(**parametros2)
            
            df = pd.read_sql(sql=query.statement, con=database.session.bind)
            df = df[PedidoSOCNET.colunas_planilha]
            
            nome_arqv = f'Pedidos_exames_SOCNET_{int(dt.datetime.now().timestamp())}'
            camihno_arqv = f'{UPLOAD_FOLDER}/{nome_arqv}'
            df.to_csv(
                f'{camihno_arqv}.zip',
                sep=';',
                index=False,
                encoding='iso-8859-1',
                compression={'method': 'zip', 'archive_name': f'{nome_arqv}.csv'}
            )
            return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=f'{nome_arqv}.zip')

    return render_template('busca/busca_socnet.html', form=form, title='GRS+Connect')


# ATUALIZAR STATUS------------------------------------------
@app.route('/atualizar_status_socnet', methods=['GET', 'POST'])
@login_required
def atualizar_status_socnet():
    form = FormAtualizarStatus()
    form.status_aso.choices = (
        [('', 'Selecione')] + 
        [(status.id_status, status.nome_status) for status in Status.query.all()]
    )
    form.status_rac.choices = (
        [('', 'Selecione')] + 
        [(status.id_status, status.nome_status) for status in StatusRAC.query.all()]
    )

    datas = {
        'data_inicio': request.args.get('data_inicio', type=str, default=None),
        'data_fim': request.args.get('data_fim', type=str, default=None)
    }
    for chave, valor in datas.items():
        if valor:
            datas[chave] = dt.datetime.strptime(valor, '%Y-%m-%d').date()

    query_pedidos = PedidoSOCNET.buscar_pedidos(
        pesquisa_geral=request.args.get('pesquisa_geral', type=int, default=None),
        cod_empresa_principal=request.args.get('cod_empresa_principal', type=int, default=None),
        data_inicio=datas['data_inicio'],
        data_fim=datas['data_fim'],
        id_status=request.args.get('id_status', type=int, default=None),
        id_status_rac=request.args.get('id_status_rac', type=int, default=None),
        id_empresa=request.args.get('id_empresa', type=int, default=None),
        id_prestador=request.args.get('id_prestador', type=int, default=None),
        seq_ficha=request.args.get('seq_ficha', type=int, default=None),
        nome_funcionario=request.args.get('nome_funcionario', type=str, default=None),
        obs=request.args.get('obs', type=str, default=None)
    )

    # total de resultados na query
    total = query_pedidos.count()

    # ATUALIZAR STATUS-----------------------------------------------
    if form.validate_on_submit():
        lista_atualizar = request.form.getlist('checkItem', type=int)

        # dados antigos------------------------------------------
        query_dados_antigos = (
            database.session.query(
                PedidoSOCNET.id_ficha,
                PedidoSOCNET.nome_funcionario
            )
            .filter(PedidoSOCNET.id_ficha.in_(lista_atualizar))
            .all()
        )

        # dados novos---------------------------------------------
        hoje = dt.datetime.now(tz=TIMEZONE_SAO_PAULO)

        dados_novos = [
            {
                'id_ficha': pedido.id_ficha,
                'id_status': int(form.status_aso.data),
                'data_alteracao': hoje,
                'alterado_por': current_user.username
            } for pedido in query_dados_antigos
        ]

        if form.status_rac.data:
            for pedido in dados_novos:
                pedido['id_status_rac'] = int(form.status_rac.data)
        if form.data_recebido.data:
            for pedido in dados_novos:
                pedido['data_recebido'] = form.data_recebido.data
        if form.data_comparecimento.data:
            for pedido in dados_novos:
                pedido['data_comparecimento'] = form.data_comparecimento.data
        if form.obs.data:
            for pedido in dados_novos:
                pedido['obs'] = form.obs.data

        database.session.bulk_update_mappings(PedidoSOCNET, dados_novos)
        database.session.commit()

        # log acoes---------------------------------------------------
        status_novo = Status.query.get(int(form.status_aso.data))
        logs_acoes = [
            {
                'id_usuario': current_user.id_usuario,
                'username': current_user.username,
                'tabela': 'PedidoSOCNET',
                'acao': 'Atualizar Status',
                'id_registro': pedido.id_ficha,
                'nome_registro': pedido.nome_funcionario,
                'obs': f'status_novo: {status_novo.id_status}-{status_novo.nome_status}, obs: {form.obs.data}, data_recebido: {form.data_recebido.data}',
                'data': hoje.date(),
                'hora': hoje.time()
            } for pedido in query_dados_antigos
        ]

        database.session.bulk_insert_mappings(LogAcoes, logs_acoes)
        database.session.commit()

        flash(f'Status atualizados com sucesso! Qtd: {len(lista_atualizar)}', 'alert-success')
        return redirect(url_for('busca_socnet'))

    return render_template(
        'busca/busca_atualizar_status_socnet.html',
        title='GRS+Connect',
        form=form,
        busca=query_pedidos,
        total=total
    )


@app.route('/enviar_emails_socnet', methods=['GET', 'POST'])
@login_required
def enviar_emails_socnet():
    form = FormEnviarEmails()

    datas = {
        'data_inicio': request.args.get('data_inicio', type=str, default=None),
        'data_fim': request.args.get('data_fim', type=str, default=None)
    }
    for chave, valor in datas.items():
        if valor:
            datas[chave] = dt.datetime.strptime(valor, '%Y-%m-%d').date()

    query_pedidos = PedidoSOCNET.buscar_pedidos(
        pesquisa_geral=request.args.get('pesquisa_geral', type=int, default=None),
        cod_empresa_principal=request.args.get('cod_empresa_principal', type=int, default=None),
        data_inicio=datas['data_inicio'],
        data_fim=datas['data_fim'],
        id_status=request.args.get('id_status', type=int, default=None),
        id_status_rac=request.args.get('id_status_rac', type=int, default=None),
        id_empresa=request.args.get('id_empresa', type=int, default=None),
        id_prestador=request.args.get('id_prestador', type=int, default=None),
        seq_ficha=request.args.get('seq_ficha', type=int, default=None),
        nome_funcionario=request.args.get('nome_funcionario', type=str, default=None),
        obs=request.args.get('obs', type=str, default=None)
    )

    # total de resultados na query
    total = query_pedidos.count()

    if form.validate_on_submit():
        lista_enviar = request.form.getlist('checkItem', type=int)
        
        query_pedidos = (
            database.session.query(
                PedidoSOCNET,
                Prestador.nome_prestador,
                Prestador.emails,
                Prestador.solicitar_asos,
                EmpresaSOCNET.nome_empresa,
                TipoExame.nome_tipo_exame,
            )
            .outerjoin(Prestador, EmpresaSOCNET, TipoExame)
            .filter(PedidoSOCNET.id_ficha.in_(lista_enviar))
        )

        df = pd.read_sql(sql=query_pedidos.statement, con=database.session.bind)
        df = df.replace({np.nan: None})
        
        with mail.connect() as conn:
            qtd_envios = 0
            qtd_pedidos = 0
            erros_envio = [] # registrar erros de envio
            for id_prestador, solicitar_asos in df[['id_prestador', 'solicitar_asos']].drop_duplicates(subset='id_prestador').values:
                # se o pedido tem prestador
                if id_prestador and solicitar_asos:
                    # filtrar tabela
                    tab_aux = df[df['id_prestador'] == id_prestador]

                    # pegar nome do prestador
                    nome_prestador = tab_aux['nome_prestador'].values[0]
                    # pegar lista de emails do prestador
                    emails_prestador = tab_aux['emails'].values[0]

                    if emails_prestador and "@" in emails_prestador:
                        try:
                            # selecionar colunas
                            tab_aux = tab_aux[PedidoSOCNET.colunas_tab_email]
                            # renomear colunas
                            tab_aux = tab_aux.rename(
                                columns = dict(
                                    zip(
                                        PedidoSOCNET.colunas_tab_email,
                                        PedidoSOCNET.colunas_tab_email2
                                    )
                                )
                            )

                            # formatar datas
                            tab_aux['Data Ficha'] = (
                                pd.to_datetime(
                                    tab_aux['Data Ficha'],
                                    format='%Y-%m-%d'
                                ).dt.strftime('%d/%m/%Y')
                            )

                            # enviar email
                            destinatario = (
                                emails_prestador
                                .replace(" ", "")
                                .replace(",", ";")
                            ).split(';')
                            assinatura = r'static/images/ass_bot_liberacao.png'
                            anexo = Attachment(
                                filename=assinatura,
                                content_type='image/png',
                                data=app.open_resource(assinatura).read(),
                                disposition='inline',
                                headers=[['Content-ID','<AssEmail>']]
                            )

                            if form.obs_email.data:
                                email_body = corpo_email_padrao(
                                    tabela=tab_aux,
                                    observacoes=form.obs_email.data,
                                    nome_usuario=current_user.nome_usuario,
                                    email_usuario=current_user.email,
                                    telefone_usuario=current_user.telefone,
                                    celular_usuario=current_user.celular
                                )
                            else:
                                email_body = corpo_email_padrao(
                                    tabela=tab_aux,
                                    nome_usuario=current_user.nome_usuario,
                                    email_usuario=current_user.email,
                                    telefone_usuario=current_user.telefone,
                                    celular_usuario=current_user.celular
                                )

                            if form.assunto_email.data:
                                assunto_email = f'{form.assunto_email.data} - {nome_prestador}'
                            else:
                                assunto_email = f'ASO GRS - {nome_prestador}'
                            
                            emails_cc = [current_user.email]
                            if form.email_copia.data:
                                emails_cc.extend(form.email_copia.data.replace(',', ';').split(';'))

                            msg = Message(
                                reply_to=current_user.email,
                                subject=assunto_email,
                                recipients=destinatario,
                                cc=emails_cc,
                                html=email_body,
                                attachments=[anexo]
                            )
                            conn.send(msg)

                            # resgistrar envio
                            qtd_envios = qtd_envios + 1
                            qtd_pedidos = qtd_pedidos + len(tab_aux)
                        except:
                            # registrar erro
                            erros_envio.append(nome_prestador)
                    else:
                        # registrar erro
                        erros_envio.append(nome_prestador)

        # registrar costumizacoes feitas no email
        costumizacoes = {}
        for campo in ['assunto_email', 'email_copia', 'obs_email']:
            if form.data[campo]:
                costumizacoes[campo] = form.data[campo]
        
        if costumizacoes:
            LogAcoes.registrar_acao(
                username=current_user.username,
                nome_tabela='Email',
                tipo_acao='Enviar Email',
                id_registro=0,
                nome_registro=0,
                observacao=f'Detalhes adicionados ao Email: {str(costumizacoes)}'
            )


        if qtd_envios:
            flash(f'Emails enviados com sucesso! Qtd Emails: {qtd_envios} Qtd Pedidos: {qtd_pedidos}', 'alert-success')
        if erros_envio:
            erros_envio = '; '.join(erros_envio)
            flash(f'Erros: {erros_envio}', 'alert-danger')
        return redirect(url_for('busca_socnet'))

    return render_template(
        'busca/busca_enviar_emails_socnet.html',
        title='GRS+Connect',
        form=form,
        busca=query_pedidos,
        total=total
    )


# PEDIDO EDITAR----------------------------------------
@app.route('/pedidos_socnet/editar', methods=['GET', 'POST'])
@login_required
def pedido_socnet_editar():
    pedido = PedidoSOCNET.query.get(request.args.get('id_ficha', type=int))
    
    # criar form com opcoes pre selecionadas
    form = FormEditarPedidoSOCNET(
        cod_empresa_principal=pedido.cod_empresa_principal,
        seq_ficha=pedido.seq_ficha,
        cod_funcionario=pedido.cod_funcionario,
        cpf=pedido.cpf,
        nome_funcionario=pedido.nome_funcionario,
        data_ficha=pedido.data_ficha,
        tipo_exame=pedido.cod_tipo_exame,
        prestador=pedido.id_prestador,
        empresa=pedido.id_empresa,
        status=pedido.id_status,
        data_recebido=pedido.data_recebido,
        obs=pedido.obs,
        data_inclusao=pedido.data_inclusao,
        data_alteracao=pedido.data_alteracao,
        incluido_por=pedido.incluido_por,
        alterado_por=pedido.alterado_por
    )

    # opcoes
    form.cod_empresa_principal.choices = (
        [   (i.cod, i.nome)
            for i in EmpresaPrincipal.query.filter_by(cod=423)
        ]
    )
    form.tipo_exame.choices = [
        (i.cod_tipo_exame, i.nome_tipo_exame)
        for i in TipoExame.query.order_by(TipoExame.nome_tipo_exame).all()
    ]
    
    form.prestador.choices = [
        (i.id_prestador, i.nome_prestador)
        for i in Prestador.query.order_by(Prestador.nome_prestador).all()
    ]

    form.empresa.choices = [
        (i.id_empresa, i.nome_empresa)
        for i in EmpresaSOCNET.query
        .filter_by(cod_empresa_principal=pedido.cod_empresa_principal)
        .order_by(EmpresaSOCNET.nome_empresa)
    ]

    form.status.choices = [
        (i.id_status, i.nome_status)
        for i in Status.query.all()
    ]

    # form.unidade.choices = [
    #     (i.id_unidade, i.nome_unidade)
    #     for i in Unidade.query.filter_by(id_empresa=pedido.id_empresa)
    #     .order_by(Unidade.nome_unidade)
    #     .all()
    # ]

    if form.validate_on_submit():        
        pedido.data_ficha = form.data_ficha.data
        pedido.prazo = form.prazo.data
        pedido.prev_liberacao = form.prev_liberacao.data
        pedido.cod_tipo_exame = form.tipo_exame.data
        pedido.id_prestador = form.prestador.data
        pedido.id_empresa = form.empresa.data
        # pedido.id_unidade = form.unidade.data
        pedido.id_status = form.status.data
        pedido.data_recebido = form.data_recebido.data
        pedido.obs = form.obs.data

        status_novo = Status.query.get(form.status.data)

        if status_novo.finaliza_processo:
            pedido.id_status_lib = 2
        else:
            pedido.id_status_lib = 1
        #     pedido.id_status_lib = PedidoSOCNET.calcular_tag_prev_lib(form.prev_liberacao.data)

        # atualizar data alteracao
        pedido.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
        pedido.alterado_por = current_user.username
        database.session.commit()

        # registar acao
        LogAcoes.registrar_acao(
            nome_tabela = 'PedidoSOCNET',
            tipo_acao = 'Alteração',
            id_registro = pedido.id_ficha,
            nome_registro = pedido.nome_funcionario
        )
        flash('Pedido atualizado com sucesso!', 'alert-success')
        return redirect(url_for('pedido_socnet_editar', id_ficha=pedido.id_ficha))

    return render_template(
        'pedido/pedido_socnet_editar.html',
        title='GRS+Connect',
        form=form,
        pedido=pedido
    )


# PEDIDO EXCLUIR----------------------------------------
@app.route('/pedidos_socnet/excluir', methods=['GET', 'POST'])
@login_required
@admin_required
def pedido_socnet_excluir():
    pedido = PedidoSOCNET.query.get(request.args.get('id_ficha', type=int))

    database.session.delete(pedido)
    database.session.commit()

    LogAcoes.registrar_acao(
        nome_tabela = 'Pedido SOCNET',
        tipo_acao = 'Exclusão',
        id_registro = pedido.id_ficha,
        nome_registro = pedido.nome_funcionario
    )

    flash(f'Pedido excluído! Seq. Ficha: {pedido.seq_ficha}', 'alert-danger')
    return redirect(url_for('busca_socnet'))


# EMPRESAS----------------------------------------
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


# EMPRESAS GERAR CSV----------------------------------------
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


# CRIAR EMPRESA ----------------------------------------
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


# EDITAR EMPRESA-----------------------------------------------------------
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


# EXCLUIR EMPRESA-----------------------------------------------------------
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


# GRUPO EDITAR EMPRESAS----------------------------------------------------
@app.route('/grupos/empresas_socnet',  methods=['GET', 'POST'])
@login_required
def grupos_empresas_socnet():
    grupo = Grupo.query.get(request.args.get('id_grupo', type=int))
    
    # already in group
    pre_selected = [i.id_empresa for i in grupo.empresas_socnet]
    
    # create form with pre selected values
    form = FormGrupoPrestadores(select=pre_selected)
    form.select.choices = [
        (i.id_empresa, i.nome_empresa)
        for i in EmpresaSOCNET.query.all()
    ]
    # sort choices by name, ascending
    form.select.choices.sort(key=lambda tup: tup[1], reverse=False)
    
    if form.validate_on_submit():
        # reset current group
        delete_query = database.session.execute(
            delete(grupo_empresa_socnet).
            where(grupo_empresa_socnet.c.id_grupo == grupo.id_grupo)
        )

        # insert all the selected objects
        insert_items = [
            {'id_grupo': grupo.id_grupo, 'id_empresa': i}
            for i in request.form.getlist(key='select', type=int)
        ]
        insert_query = database.session.execute(
            insert(grupo_empresa_socnet).
            values(insert_items)
        )

        grupo.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
        grupo.alterado_por = current_user.username
        database.session.commit()

        # registrar acao
        LogAcoes.registrar_acao(
            nome_tabela='Grupo',
            tipo_acao='Editar Empresas SOCNET',
            id_registro=int(grupo.id_grupo),
            nome_registro=grupo.nome_grupo
        )
    
        return redirect(url_for('grupos'))
    
    return render_template(
        'grupo/grupo_empresas_socnet.html',
        title='GRS+Connect',
        form=form,
        grupo=grupo
    )


# UPLOAD PEDIDOS SOCNET----------------------------------------------------
@app.route('/pedidos_socnet/upload',  methods=['GET', 'POST'])
@login_required
def upload_pedidos_socnet():
    form = FormUpload()

    if form.validate_on_submit():
        # ler arquivo
        arqv = request.files['csv']
        data = arqv.read().decode('iso-8859-1')

        # tamnho maximo
        max_size_mb = app.config['MAX_UPLOAD_SIZE_MB']
        max_bytes = max_size_mb * 1024 * 1024

        if getsizeof(data) > max_bytes:
            flash(f'O arquivo deve ser menor que {max_size_mb} MB', 'alert-danger')
            return redirect(url_for('upload_pedidos_socnet'))
        
        else:            
            # criar novo arquivo com os dados
            filename = secure_filename(arqv.filename)
            timestamp = int(dt.datetime.now().timestamp())
            new_filename = f"{filename.split('.')[0]}_{timestamp}.csv"
            new_file_path = os.path.join(DOWNLOAD_FOLDER, new_filename)
            
            try:
                df = PedidoSOCNET.tratar_pedidos_socnet(file_contents=data)
                df.to_csv(new_file_path, index=False, sep=';', encoding='iso-8859-1')
                
                flash('Arquivo importado com sucesso!', 'alert-success')
                flash('Agora selecione o arquivo para carregar no banco de dados', 'alert-info')
                return redirect(url_for('carregar_pedidos_socnet'))
            except KeyError:
                # raise error se o arquivo for incompativel (faltar colunas ou nao der pra processar etc)
                flash(f'O arquivo não contém as colunas ou cabeçalho necessários!', 'alert-danger')
                return redirect(url_for('upload_pedidos_socnet'))

    return render_template('pedido/pedidos_socnet_upload.html', title='GRS+Connect', form=form)


# CARREGAR PEDIDOS SOCNET----------------------------------------------------
@app.route('/pedidos_socnet/carregar',  methods=['GET', 'POST'])
@login_required
def carregar_pedidos_socnet():
    form = FormCarregarPedidosSOCNET()

    # checar se pasta existe
    dir = DOWNLOAD_FOLDER
    
    files = [os.path.join(dir, f) for f in os.listdir(dir)]
    
    # sort by last modified, descending
    files.sort(key=lambda x: os.path.getctime(x), reverse=True)
    
    # opcoes de arquivos
    opcoes = [('', 'Selecione')]
    for f in files:
        file_name = os.path.split(os.path.join(dir, f))[1]

        file_size = int(os.path.getsize(os.path.join(dir, f))/1000)
        
        date_time = dt.datetime.fromtimestamp(
            os.path.getctime(os.path.join(dir, f)),
            tz=timezone('America/Sao_Paulo')
        ).strftime('%d-%m-%Y | %H:%M:%S')

        opcoes.append((file_name, f'{file_name} | {file_size} Kb | {date_time}'))
    
    form.arquivos.choices = opcoes
    
    if form.validate_on_submit():
        try:
            path = os.path.join(
                DOWNLOAD_FOLDER,
                form.arquivos.data
            )
            # ler arquivo
            df = pd.read_csv(path, sep=';', encoding='iso-8859-1')
            df['incluido_por'] = current_user.username
            df['data_inclusao'] = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
            
            # inserir na database
            df.to_sql(name='PedidoSOCNET', con=database.session.bind, index=False, if_exists='append')
            database.session.commit()
            
            os.remove(path=path)

            # registrar acao
            LogAcoes.registrar_acao(
                nome_tabela='PedidoSOCNET',
                id_registro=1,
                nome_registro=1,
                tipo_acao='Importação',
                observacao=f'Pedidos importados: {len(df)}'
            )
            
            flash(f'Pedidos importados com sucesso! Qtd: {len(df)}', 'alert-success')
            return redirect(url_for('home'))
        except IntegrityError:
            os.remove(path=path)

            flash('Este arquivo contém pedidos que já existem no banco de dados. Realize upload novamente.', 'alert-danger')
            return redirect(url_for('upload_pedidos_socnet'))
        
    return render_template('pedido/pedidos_socnet_carregar.html', title='GRS+Connect', form=form)

