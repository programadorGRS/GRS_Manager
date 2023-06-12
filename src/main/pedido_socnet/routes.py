import datetime as dt
import os
from sys import getsizeof

import numpy as np
import pandas as pd
from flask import (current_app, flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required
from flask_mail import Attachment, Message
from pytz import timezone
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from src import (DOWNLOAD_FOLDER, TIMEZONE_SAO_PAULO, UPLOAD_FOLDER, app,
                 database, mail)
from src.email_connect import EmailConnect
from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
from src.main.empresa_socnet.empresa_socnet import EmpresaSOCNET
from src.main.log_acoes.log_acoes import LogAcoes
from src.main.pedido.forms import FormAtualizarStatus, FormEnviarEmails
from src.main.pedido_socnet.pedido_socnet import PedidoSOCNET
from src.main.prestador.prestador import Prestador
from src.main.status.status import Status
from src.main.status.status_rac import StatusRAC
from src.main.tipo_exame.tipo_exame import TipoExame
from src.utils import admin_required, get_data_from_form

from .forms import (FormBuscarASOSOCNET, FormCarregarPedidosSOCNET,
                    FormEditarPedidoSOCNET, FormUpload)


@app.route('/busca_socnet', methods=['GET', 'POST'])
@login_required
def busca_socnet():
    form = FormBuscarASOSOCNET()
    # opcoes dinamicas de busca, como empresa, unidade \
    # prestador etc, sao incluidas via fetch no javascript

    form.load_choices()

    if form.validate_on_submit():
        parametros = get_data_from_form(data=form.data, ignore_keys=['pesquisa_geral'])

        if 'btn_buscar' in request.form:
            return redirect(url_for('atualizar_status_socnet', **parametros))

        elif 'btn_emails' in request.form:
            return redirect(url_for('enviar_emails_socnet', **parametros))

        elif 'btn_csv' in request.form:
            parametros['id_grupos'] = PedidoSOCNET.handle_group_choice(choice=parametros['id_grupos'])

            query = PedidoSOCNET.buscar_pedidos(**parametros)
            query = PedidoSOCNET.add_csv_cols(query=query)

            df = pd.read_sql(sql=query.statement, con=database.session.bind)

            df = df[PedidoSOCNET.COLS_CSV]

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
        id_grupos=PedidoSOCNET.handle_group_choice(choice=request.args.get('id_grupos')),
        cod_empresa_principal=request.args.get('cod_empresa_principal', type=int, default=None),
        data_inicio=datas['data_inicio'],
        data_fim=datas['data_fim'],
        id_status=request.args.get('id_status', type=int, default=None),
        id_status_rac=request.args.get('id_status_rac', type=int, default=None),
        id_empresa=request.args.get('id_empresa', type=int, default=None),
        id_prestador=request.args.get('id_prestador', type=int, default=None),
        cod_tipo_exame=request.args.get('cod_tipo_exame', type=int, default=None),
        seq_ficha=request.args.get('seq_ficha', type=int, default=None),
        nome_funcionario=request.args.get('nome_funcionario', type=str, default=None),
        obs=request.args.get('obs', type=str, default=None)
    )

    total = PedidoSOCNET.get_total_busca(query=query_pedidos)

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
        id_grupos=PedidoSOCNET.handle_group_choice(choice=request.args.get('id_grupos')),
        cod_empresa_principal=request.args.get('cod_empresa_principal', type=int, default=None),
        data_inicio=datas['data_inicio'],
        data_fim=datas['data_fim'],
        id_status=request.args.get('id_status', type=int, default=None),
        id_status_rac=request.args.get('id_status_rac', type=int, default=None),
        id_empresa=request.args.get('id_empresa', type=int, default=None),
        id_prestador=request.args.get('id_prestador', type=int, default=None),
        cod_tipo_exame=request.args.get('cod_tipo_exame', type=int, default=None),
        seq_ficha=request.args.get('seq_ficha', type=int, default=None),
        nome_funcionario=request.args.get('nome_funcionario', type=str, default=None),
        obs=request.args.get('obs', type=str, default=None)
    )

    total = PedidoSOCNET.get_total_busca(query=query_pedidos)

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
                            tab_aux = tab_aux[list(PedidoSOCNET.COLS_EMAIL.keys())]
                            # renomear colunas
                            tab_aux.rename(columns=PedidoSOCNET.COLS_EMAIL, inplace=True)

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
        return redirect(url_for('busca_socnet'))

    return render_template(
        'busca/busca_enviar_emails_socnet.html',
        form=form,
        busca=query_pedidos,
        total=total
    )

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

