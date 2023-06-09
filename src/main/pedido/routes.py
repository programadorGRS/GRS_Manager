import datetime as dt
import os
from io import StringIO
from sys import getsizeof

import numpy as np
import pandas as pd
from flask import (current_app, flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required
from flask_mail import Attachment, Message
from pandas.errors import IntCastingNaNError
from pytz import timezone

from src import TIMEZONE_SAO_PAULO, UPLOAD_FOLDER, app, database, mail
from src.email_connect import EmailConnect
from src.main.empresa.empresa import Empresa
from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
from src.main.log_acoes.log_acoes import LogAcoes
from src.main.pedido.pedido import Pedido
from src.main.prestador.prestador import Prestador
from src.main.status.status import Status
from src.main.status.status_lib import StatusLiberacao
from src.main.status.status_rac import StatusRAC
from src.main.tipo_exame.tipo_exame import TipoExame
from src.main.unidade.unidade import Unidade
from src.utils import admin_required, get_data_from_form

from .forms import (FormAtualizarStatus, FormBuscarASO, FormCarregarPedidos,
                    FormEditarPedido, FormEnviarEmails, FormPedidoBulkUpdate)


@app.route('/busca', methods=['GET', 'POST'])
@login_required
def busca():
    form = FormBuscarASO()
    # opcoes dinamicas de busca, como empresa, unidade \
    # prestador etc, sao incluidas via fetch no javascript

    form.load_choices()

    if form.validate_on_submit():
        parametros = get_data_from_form(data=form.data, ignore_keys=['pesquisa_geral'])

        if 'btn_buscar' in request.form:
            return redirect(url_for('atualizar_status', **parametros))

        elif 'btn_emails' in request.form:
            return redirect(url_for('enviar_emails', **parametros))

        elif 'btn_csv' in request.form:
            parametros['id_grupos'] = Pedido.handle_group_choice(choice=parametros['id_grupos'])
            query = Pedido.buscar_pedidos(**parametros)
            query = Pedido.add_csv_cols(query=query)
            
            df = pd.read_sql(sql=query.statement, con=database.session.bind)

            df = df[Pedido.COLS_CSV]
            
            nome_arqv = f'Pedidos_exames_{int(dt.datetime.now().timestamp())}'
            camihno_arqv = f'{UPLOAD_FOLDER}/{nome_arqv}'
            df.to_csv(
                f'{camihno_arqv}.zip',
                sep=';',
                index=False,
                encoding='iso-8859-1',
                compression={'method': 'zip', 'archive_name': f'{nome_arqv}.csv'}
            )
            return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=f'{nome_arqv}.zip')

    return render_template('busca/busca.html', form=form, title='GRS+Connect')


@app.route('/atualizar_status', methods=['GET', 'POST'])
@login_required
def atualizar_status():
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

    query_pedidos = Pedido.buscar_pedidos(
        id_grupos=Pedido.handle_group_choice(choice=request.args.get('id_grupos')),
        cod_empresa_principal=request.args.get('cod_empresa_principal', type=int, default=None),
        data_inicio=datas['data_inicio'],
        data_fim=datas['data_fim'],
        id_status=request.args.get('id_status', type=int, default=None),
        id_status_rac=request.args.get('id_status_rac', type=int, default=None),
        id_tag=request.args.get('id_tag', type=int, default=None),
        id_empresa=request.args.get('id_empresa', type=int, default=None),
        id_unidade=request.args.get('id_unidade', type=int, default=None),
        id_prestador=request.args.get('id_prestador', type=int, default=None),
        cod_tipo_exame=request.args.get('cod_tipo_exame', type=int, default=None),
        seq_ficha=request.args.get('seq_ficha', type=int, default=None),
        nome_funcionario=request.args.get('nome_funcionario', type=str, default=None),
        obs=request.args.get('obs', type=str, default=None)
    )

    total = Pedido.get_total_busca(query=query_pedidos)

    page_num = request.args.get(key='page', type=int, default=1)
    results_per_page = 500
    query_pagination = query_pedidos.paginate(page=page_num, per_page=results_per_page)

    # remove page argument, because it is defined by the link in the template
    url_args = request.args.copy()
    if 'page' in url_args.keys():
        url_args.pop('page')

    # ATUALIZAR STATUS-----------------------------------------------
    if form.validate_on_submit():
        lista_atualizar = request.form.getlist('checkItem', type=int)

        # dados antigos------------------------------------------
        query_dados_antigos = (
            database.session.query(
                Pedido.id_ficha,
                Pedido.prev_liberacao,
                Pedido.id_status_lib,
                Pedido.nome_funcionario
            )
            .filter(Pedido.id_ficha.in_(lista_atualizar))
            .all()
        )

        # dados novos---------------------------------------------
        hoje = dt.datetime.now(tz=TIMEZONE_SAO_PAULO)

        dados_novos = [
            {
                'id_ficha': pedido.id_ficha,
                'id_status': int(form.status_aso.data),
                'data_alteracao': hoje,
                'alterado_por': current_user.username,
                'id_status_lib': pedido.id_status_lib
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
        
        # se status novo finaliza processo, mudar tag para ok (2)
        # se nao, calcular a nova tag
        status_novo = Status.query.get(int(form.status_aso.data))
        if status_novo.finaliza_processo:
            for pedido in dados_novos:
                pedido['id_status_lib'] = 2
        else:
            for i, dados_antigos in enumerate(query_dados_antigos):
                dados_novos[i]['id_status_lib'] = Pedido.calcular_tag_prev_lib(dados_antigos.prev_liberacao)

        database.session.bulk_update_mappings(Pedido, dados_novos)
        database.session.commit()

        # log acoes---------------------------------------------------
        logs_acoes = [
            {
                'id_usuario': current_user.id_usuario,
                'username': current_user.username,
                'tabela': 'Pedido',
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
        return redirect(url_for('busca'))

    return render_template(
        'busca/busca_atualizar_status.html',
        title='GRS+Connect',
        form=form,
        busca=query_pagination,
        total=total,
        url_args=url_args,
        results_per_page=results_per_page
    )


@app.route('/enviar_emails', methods=['GET', 'POST'])
@login_required
def enviar_emails():
    form = FormEnviarEmails()

    datas = {
        'data_inicio': request.args.get('data_inicio', type=str, default=None),
        'data_fim': request.args.get('data_fim', type=str, default=None)
    }
    for chave, valor in datas.items():
        if valor:
            datas[chave] = dt.datetime.strptime(valor, '%Y-%m-%d').date()

    query_pedidos = Pedido.buscar_pedidos(
        id_grupos=Pedido.handle_group_choice(choice=request.args.get('id_grupos')),
        cod_empresa_principal=request.args.get('cod_empresa_principal', type=int, default=None),
        data_inicio=datas['data_inicio'],
        data_fim=datas['data_fim'],
        id_status=request.args.get('id_status', type=int, default=None),
        id_status_rac=request.args.get('id_status_rac', type=int, default=None),
        id_tag=request.args.get('id_tag', type=int, default=None),
        id_empresa=request.args.get('id_empresa', type=int, default=None),
        id_unidade=request.args.get('id_unidade', type=int, default=None),
        id_prestador=request.args.get('id_prestador', type=int, default=None),
        cod_tipo_exame=request.args.get('cod_tipo_exame', type=int, default=None),
        seq_ficha=request.args.get('seq_ficha', type=int, default=None),
        nome_funcionario=request.args.get('nome_funcionario', type=str, default=None),
        obs=request.args.get('obs', type=str, default=None)
    )

    total = Pedido.get_total_busca(query=query_pedidos)

    page_num = request.args.get(key='page', type=int, default=1)
    results_per_page = 500
    query_pagination = query_pedidos.paginate(page=page_num, per_page=results_per_page)

    # remove page argument, because it is defined by the link in the template
    url_args = request.args.copy()
    if 'page' in url_args.keys():
        url_args.pop('page')

    if form.validate_on_submit():
        lista_enviar = request.form.getlist('checkItem', type=int)
        
        query_pedidos = (
            database.session.query(
                Pedido,
                Prestador.nome_prestador,
                Prestador.emails,
                Prestador.solicitar_asos,
                Empresa.razao_social,
                TipoExame.nome_tipo_exame,
                StatusLiberacao.nome_status_lib
            )
            .outerjoin(Prestador, Empresa, TipoExame, StatusLiberacao)
            .filter(Pedido.id_ficha.in_(lista_enviar))
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
                    tab_aux: pd.DataFrame = df[df['id_prestador'] == id_prestador]

                    # pegar nome do prestador
                    nome_prestador = tab_aux['nome_prestador'].values[0]
                    # pegar lista de emails do prestador
                    emails_prestador = tab_aux['emails'].values[0]

                    if emails_prestador and "@" in emails_prestador:
                        try:
                            # selecionar colunas
                            tab_aux = tab_aux[list(Pedido.COLS_EMAIL.keys())]
                            # renomear colunas
                            tab_aux.rename(columns=Pedido.COLS_EMAIL, inplace=True)

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
                            assinatura = EmailConnect.ASSINATURA_BOT.get('img_path')
                            anexo = Attachment(
                                filename=assinatura,
                                content_type='image/png',
                                data=app.open_resource(assinatura).read(),
                                disposition='inline',
                                headers=[['Content-ID','<AssEmail>']]
                            )


                            if form.obs_email.data:
                                email_body = EmailConnect.create_email_body(
                                    email_template_path='src/email_templates/email_aso.html',
                                    replacements={
                                        'DATAFRAME_ASO': tab_aux.to_html(index=False),
                                        'USER_OBS': form.obs_email.data,
                                        'USER_NAME': current_user.nome_usuario,
                                        'USER_EMAIL': current_user.email,
                                        'USER_TEL': current_user.telefone,
                                        'USER_CEL': current_user.celular
                                    }
                                )
                            else:
                                email_body = EmailConnect.create_email_body(
                                    email_template_path='src/email_templates/email_aso.html',
                                    replacements={
                                        'DATAFRAME_ASO': tab_aux.to_html(index=False),
                                        'USER_OBS': 'Sinalizar se o funcionário não compareceu.',
                                        'USER_NAME': current_user.nome_usuario,
                                        'USER_EMAIL': current_user.email,
                                        'USER_TEL': current_user.telefone,
                                        'USER_CEL': current_user.celular
                                    }
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
        return(redirect(url_for('busca')))

    return render_template(
        'busca/busca_enviar_emails.html',
        title='GRS+Connect',
        form=form,
        busca=query_pagination,
        total=total,
        url_args=url_args,
        results_per_page=results_per_page
    )


@app.route('/pedidos/editar', methods=['GET', 'POST'])
@login_required
def pedido_editar():
    pedido = Pedido.query.get(request.args.get('id_ficha', type=int))
    
    # criar form com opcoes pre selecionadas
    form = FormEditarPedido(
        cod_empresa_principal=pedido.cod_empresa_principal,
        seq_ficha=pedido.seq_ficha,
        cod_funcionario=pedido.cod_funcionario,
        cpf=pedido.cpf,
        nome_funcionario=pedido.nome_funcionario,
        data_ficha=pedido.data_ficha,
        tipo_exame=pedido.cod_tipo_exame,
        prestador=pedido.id_prestador,
        empresa=pedido.id_empresa,
        unidade=pedido.id_unidade,
        status=pedido.id_status,
        prazo=pedido.prazo,
        prev_liberacao=pedido.prev_liberacao,
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
        (i.id_empresa, i.razao_social)
        for i in Empresa.query
        .filter_by(cod_empresa_principal=pedido.cod_empresa_principal)
        .order_by(Empresa.razao_social)
    ]

    form.status.choices = [
        (i.id_status, i.nome_status)
        for i in Status.query.all()
    ]

    form.unidade.choices = [
        (i.id_unidade, i.nome_unidade)
        for i in Unidade.query.filter_by(id_empresa=pedido.id_empresa)
        .order_by(Unidade.nome_unidade)
        .all()
    ]

    if form.validate_on_submit():        
        pedido.data_ficha = form.data_ficha.data
        pedido.prazo = form.prazo.data
        pedido.prev_liberacao = form.prev_liberacao.data
        pedido.cod_tipo_exame = form.tipo_exame.data
        pedido.id_prestador = form.prestador.data
        pedido.id_empresa = form.empresa.data
        pedido.id_unidade = form.unidade.data
        pedido.id_status = form.status.data
        pedido.data_recebido = form.data_recebido.data
        pedido.obs = form.obs.data

        status_novo = Status.query.get(form.status.data)

        if status_novo.finaliza_processo:
            pedido.id_status_lib = 2
        else:
            pedido.id_status_lib = Pedido.calcular_tag_prev_lib(form.prev_liberacao.data)

        # atualizar data alteracao
        pedido.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
        pedido.alterado_por = current_user.username
        database.session.commit()

        # registar acao
        LogAcoes.registrar_acao(
            nome_tabela = 'Pedido',
            tipo_acao = 'Alteração',
            id_registro = pedido.id_ficha,
            nome_registro = pedido.nome_funcionario
        )
        flash('Pedido atualizado com sucesso!', 'alert-success')
        return redirect(url_for('pedido_editar', id_ficha=pedido.id_ficha))

    return render_template(
        'pedido/pedido_editar.html',
        title='GRS+Connect',
        form=form,
        pedido=pedido
    )


@app.route('/pedidos/excluir', methods=['GET', 'POST'])
@login_required
@admin_required
def pedido_excluir():
    pedido = Pedido.query.get(request.args.get('id_ficha', type=int))

    database.session.delete(pedido)
    database.session.commit()

    LogAcoes.registrar_acao(
        nome_tabela = 'Pedido',
        tipo_acao = 'Exclusão',
        id_registro = pedido.id_ficha,
        nome_registro = pedido.nome_funcionario
    )

    flash(f'Pedido excluído! Seq. Ficha: {pedido.seq_ficha}', 'alert-danger')
    return redirect(url_for('busca'))


@app.route('/pedidos/carregar', methods=['GET', 'POST'])
@login_required
@admin_required
def carregar_pedidos():
    form = FormCarregarPedidos(cod_empresa_principal=423)

    form.cod_empresa_principal.choices = (
        [   (i.cod, i.nome)
            for i in 
            EmpresaPrincipal.query.filter_by(cod=423)
        ]
    )
    
    # if form.validate_on_submit():
    #     try:
    #         qtd_pedidos = Pedido.inserir_pedidos(
    #             cod_empresa_principal=form.cod_empresa_principal.data,
    #             dataInicio=form.data_inicio.data.strftime('%d/%m/%Y'),
    #             dataFim=form.data_fim.data.strftime('%d/%m/%Y')
    #         )

    #         LogAcoes.registrar_acao(
    #             nome_tabela='Pedido',
    #             tipo_acao='Importação',
    #             id_registro=1,
    #             nome_registro=1,
    #             observacao=f'Pedidos importdados: {qtd_pedidos}'
    #         )
        
    #         flash(f'Pedidos importados com sucesso! Qtd: {qtd_pedidos}', 'alert-success')
            
    #         return redirect(url_for('carregar_pedidos'))
    #     except ExpatError:
    #         flash('Erro de comunicação com o SOC. Tente novamente mais tarde', 'alert-danger')
    flash('Função temporariamente desativada', 'alert-danger')

    return render_template('pedido/pedidos_carregar.html', title='GRS+Connect', form=form)


@app.route('/pedidos/bulk_update', methods=['GET', 'POST'])
@login_required
def pedidos_bulk_update():
    form = FormPedidoBulkUpdate()

    lista_status: list[Status] = (
        database.session.query(
            Status.id_status, Status.nome_status
        )
        .all()
    )

    if form.validate_on_submit():
        # ler arquivo
        arqv = request.files['csv']
        data = arqv.read().decode('iso-8859-1')

        # tamnho maximo
        max_size_mb = app.config['MAX_UPLOAD_SIZE_MB']
        max_bytes = max_size_mb * 1024 * 1024

        if getsizeof(data) <= max_bytes:
            # ler string como objeto para csv
            df: pd.DataFrame = pd.read_csv(
                filepath_or_buffer=StringIO(data),
                sep=';',
                encoding='iso-8859-1',
            )

            colunas_permitidas = ['id_ficha', 'id_status', 'data_recebido', 'obs']
            colunas_obrigatorias = ['id_ficha', 'id_status'] # integer not null
            
            # remover colunas inuteis
            for col in df.columns:
                if col not in colunas_permitidas:
                    df.drop(columns=col, inplace=True)

            # validar colunas obrigatorias
            for col in colunas_obrigatorias:
                if col in df.columns:
                    try:
                        df[col] = df[col].astype(int)
                    except (IntCastingNaNError, ValueError):
                        flash(f'A coluna {col} deve conter apenas números inteiros', 'alert-danger')
                        return redirect(url_for('pedidos_bulk_update'))
                else:
                    flash(f'A coluna {col} é obrigatória', 'alert-danger')
                    return redirect(url_for('pedidos_bulk_update'))

            # validar status
            status_validos: list[int] = [stt.id_status for stt in Status.query.all()]
            status_invalidos: list[int] = []
            for stt in df['id_status'].drop_duplicates():
                if stt not in status_validos:
                    status_invalidos.append(str(stt))

            if status_invalidos:
                flash(f'A coluna id_status contém Status inválidos. id_status: {", ".join(status_invalidos)}', 'alert-danger')
                return redirect(url_for('pedidos_bulk_update'))

            df.drop_duplicates(subset='id_ficha', inplace=True, ignore_index=True)
            
            # tratar col de datas, se houver
            if 'data_recebido' in df.columns:
                try:
                    df['data_recebido'] = df['data_recebido'].astype(str)
                    df['data_recebido'] = pd.to_datetime(df['data_recebido'], dayfirst=True).dt.date
                    # remover pd.NaT, databases aceitam apenas None como valor nulo
                    df['data_recebido'] = df['data_recebido'].astype(object).replace(pd.NaT, None)
                except: # numero excessivo de exceptions para importar
                    flash(f'A coluna data_recebido contém valores inválidos. Utilize o formato dd/mm/yyyy', 'alert-danger')
                    return redirect(url_for('pedidos_bulk_update'))
            
            # tratar col str
            if 'obs' in df.columns:
                df['obs'] = df['obs'].astype(object).replace(np.nan, None)

            # validar se pedidos existem
            query_pedidos_db = (
                database.session.query(Pedido.id_ficha, Pedido.prev_liberacao)
                .filter(Pedido.id_ficha.in_(df['id_ficha']))
            )
            df_pedidos_db = pd.read_sql(query_pedidos_db.statement, con=database.session.bind)

            inexistentes: list[str] = (
                df[~df['id_ficha'].isin(df_pedidos_db['id_ficha'])]['id_ficha']
                .astype(str)
                .tolist()
            )

            df = df[df['id_ficha'].isin(df_pedidos_db['id_ficha'])]

            # calcular tags
            df = df.merge(df_pedidos_db, how='left', on='id_ficha')
            df['id_status_lib'] = list(map(Pedido.calcular_tag_prev_lib, df['prev_liberacao']))

            status_finaliza_processo: list[int] = (
                database.session.query(Status.id_status)
                .filter(Status.finaliza_processo == True)
                .all()
            )
            status_finaliza_processo = [status.id_status for status in status_finaliza_processo]

            df.loc[df['id_status'].isin(status_finaliza_processo), 'id_status_lib'] = 2 # tag ok

            # registrar alterador
            df['data_alteracao'] = dt.datetime.now(tz=TIMEZONE_SAO_PAULO)
            df['alterado_por'] = current_user.username

            # manter apenas colunas finais necessarias apos o tratamento do df
            cols_finais = [
                'id_ficha',
                'id_status',
                'id_status_lib',
                'data_recebido',
                'obs',
                'data_alteracao',
                'alterado_por'
            ]
            for col in df.columns:
                if col not in cols_finais:
                    df.drop(columns=col, inplace=True)

            # commit update
            df_dicts: list[dict[str, any]] = df.to_dict(orient='records')
            database.session.bulk_update_mappings(Pedido, df_dicts)
            database.session.commit()

            flash(f'Pedidos atualizados com sucesso! Total: {len(df)}, Colunas: {", ".join(list(df.columns))}', 'alert-success')
            if inexistentes:
                flash(f'Alguns pedidos na planilha não foram encontrados no banco de dados. Total: {len(inexistentes)}, Ex: {", ".join(inexistentes[:6])}', 'alert-danger')

            # logar acoes
            query_acoes: list[Pedido] = (
                database.session.query(
                    Pedido.id_ficha,
                    Pedido.nome_funcionario,
                    Pedido.data_recebido,
                    Pedido.obs,
                    Pedido.id_status,
                    Status.nome_status
                )
                .filter(Pedido.id_ficha.in_(df['id_ficha']))
                .join(Status, Pedido.id_status == Status.id_status)
                .all()
            )

            logs_acoes: list[dict[str, any]] = [
                {
                    'id_usuario': current_user.id_usuario,
                    'username': current_user.username,
                    'tabela': 'Pedido',
                    'acao': 'Atualizar Status em Massa',
                    'id_registro': pedido.id_ficha,
                    'nome_registro': pedido.nome_funcionario,
                    'obs': f'status_novo: {pedido.id_status}-{pedido.nome_status}, obs: {pedido.obs}, data_recebido: {pedido.data_recebido}',
                    'data': dt.datetime.now(tz=TIMEZONE_SAO_PAULO).date(),
                    'hora': dt.datetime.now(tz=TIMEZONE_SAO_PAULO).time()
                } for pedido in query_acoes
            ]

            database.session.bulk_insert_mappings(LogAcoes, logs_acoes)
            database.session.commit()

            return redirect(url_for('pedidos_bulk_update'))
        else:
            flash(f'O arquivo deve ser menor que {max_size_mb} MB', 'alert-danger')
            return redirect(url_for('pedidos_bulk_update'))

    return render_template(
        'pedido/bulk_update.html',
        title='GRS+Connect',
        form=form,
        lista_status=lista_status
    )
