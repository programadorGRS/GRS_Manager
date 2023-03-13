import datetime as dt
from io import StringIO
from sys import getsizeof

import numpy as np
import pandas as pd
from flask import (flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required
from flask_mail import Attachment, Message
from pandas.errors import IntCastingNaNError
from pytz import timezone
from sqlalchemy.exc import IntegrityError

from manager import TIMEZONE_SAO_PAULO, UPLOAD_FOLDER, app, database, mail
from manager.email_connect import EmailConnect
from manager.forms import (FormAtualizarStatus, FormBuscarASO,
                           FormBuscarEmpresa, FormBuscarExames,
                           FormBuscarPrestador, FormBuscarUnidade,
                           FormCarregarPedidos, FormCriarEmpresa,
                           FormCriarExame, FormCriarPrestador,
                           FormCriarUnidade, FormEditarEmpresa,
                           FormEditarExame, FormEditarPedido,
                           FormEditarPrestador, FormEditarUnidade,
                           FormEnviarEmails, FormImportarDados,
                           FormManservAtualiza, FormPedidoBulkUpdate)
from manager.models import (Empresa, EmpresaPrincipal, Exame, LogAcoes, Pedido,
                            Prestador, Status, StatusLiberacao, StatusRAC,
                            TipoExame, Unidade)
from manager.utils import admin_required, tratar_emails


# TODO: incluir funcoes de atualizar status em massa (csv) para RAC e os outros campos novos


# BUSCA ----------------------------------------
@app.route('/busca', methods=['GET', 'POST'])
@login_required
def busca():
    form = FormBuscarASO()
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

    # opcoes tag
    form.id_tag.choices = (
        [('', 'Selecione')] +
        [
            (i.id_status_lib, i.nome_status_lib)
            for i in StatusLiberacao.query
            .order_by(StatusLiberacao.nome_status_lib)
            .all()
        ]
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
            'id_tag': form.id_tag.data,
            'id_empresa': form.id_empresa.data,
            'id_unidade': form.id_unidade.data,
            'id_prestador': form.id_prestador.data,
            'nome_funcionario': form.nome_funcionario.data,
            'obs': form.obs.data
        }

        parametros2: dict[str, any] = {}
        for chave, valor in parametros.items():
            if valor not in (None, ''):
                parametros2[chave] = valor

        if 'btn_buscar' in request.form:
            return redirect(url_for('atualizar_status', **parametros2))

        elif 'btn_emails' in request.form:
            return redirect(url_for('enviar_emails', **parametros2))

        elif 'btn_csv' in request.form:
            query = Pedido.buscar_pedidos(**parametros2)
            
            df = pd.read_sql(sql=query.statement, con=database.session.bind)
            df = df[Pedido.colunas_planilha]
            
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


# ATUALIZAR STATUS------------------------------------------
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
        pesquisa_geral=request.args.get('pesquisa_geral', type=int, default=None),
        cod_empresa_principal=request.args.get('cod_empresa_principal', type=int, default=None),
        data_inicio=datas['data_inicio'],
        data_fim=datas['data_fim'],
        id_status=request.args.get('id_status', type=int, default=None),
        id_status_rac=request.args.get('id_status_rac', type=int, default=None),
        id_tag=request.args.get('id_tag', type=int, default=None),
        id_empresa=request.args.get('id_empresa', type=int, default=None),
        id_unidade=request.args.get('id_unidade', type=int, default=None),
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
        busca=query_pedidos,
        total=total
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
        pesquisa_geral=request.args.get('pesquisa_geral', type=int, default=None),
        cod_empresa_principal=request.args.get('cod_empresa_principal', type=int, default=None),
        data_inicio=datas['data_inicio'],
        data_fim=datas['data_fim'],
        id_status=request.args.get('id_status', type=int, default=None),
        id_status_rac=request.args.get('id_status_rac', type=int, default=None),
        id_tag=request.args.get('id_tag', type=int, default=None),
        id_empresa=request.args.get('id_empresa', type=int, default=None),
        id_unidade=request.args.get('id_unidade', type=int, default=None),
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
                    tab_aux = df[df['id_prestador'] == id_prestador]

                    # pegar nome do prestador
                    nome_prestador = tab_aux['nome_prestador'].values[0]
                    # pegar lista de emails do prestador
                    emails_prestador = tab_aux['emails'].values[0]

                    if emails_prestador and "@" in emails_prestador:
                        try:
                            # selecionar colunas
                            tab_aux = tab_aux[Pedido.colunas_tab_email]
                            # renomear colunas
                            tab_aux = tab_aux.rename(
                                columns = dict(
                                    zip(
                                        Pedido.colunas_tab_email,
                                        Pedido.colunas_tab_email2
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
                                email_body = EmailConnect.create_email_body(
                                    email_template_path='manager/email_templates/email_aso.html',
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
                                    email_template_path='manager/email_templates/email_aso.html',
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
        busca=query_pedidos,
        total=total
    )


# PEDIDO EDITAR----------------------------------------
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


# PEDIDO EXCLUIR----------------------------------------
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


# PEDIDOS CARREGAR-----------------------------------------------------
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


# BUSCA EMPRESAS----------------------------------------
@app.route('/buscar_empresas', methods=['GET', 'POST'])
@login_required
def buscar_empresas():
    form = FormBuscarEmpresa()

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )

    if form.validate_on_submit() and 'botao_buscar' in request.form:
        return redirect(
            url_for(
                'empresas',
                cod_empresa_principal=form.cod_empresa_principal.data,
                id_empresa=form.id.data,
                cod=form.cod.data,
                nome=form.nome.data,
                ativo=form.ativo.data
            )
        )
    elif form.validate_on_submit() and 'botao_csv' in request.form:
        return redirect(
            url_for(
                'empresas_csv',
                cod_empresa_principal=form.cod_empresa_principal.data,
                id_empresa=form.id.data,
                cod=form.cod.data,
                nome=form.nome.data,
                ativo=form.ativo.data
            )
        )

    return render_template(
        'empresa/busca.html',
        title='GRS+Connect',
        form=form
    )


# EMPRESAS----------------------------------------
@app.route('/empresas')
@login_required
def empresas():

    query = Empresa.buscar_empresas(
        cod_empresa_principal=request.args.get(key='cod_empresa_principal', default=None, type=int),
        id_empresa=request.args.get(key='id_empresa', default=None, type=int),
        cod_empresa=request.args.get(key='cod', default=None, type=int),
        nome=request.args.get(key='nome', default=None, type=str),
        ativo=request.args.get(key='ativo', default=None, type=int)
    ).all()
    
    return render_template(
        'empresa/empresas.html',
        title='GRS+Connect',
        lista_empresas=query,
        qtd=len(query)
    )


# EMPRESAS GERAR CSV----------------------------------------
@app.route('/empresas/csv')
@login_required
def empresas_csv():
    query = Empresa.buscar_empresas(
        cod_empresa_principal=request.args.get(key='cod_empresa_principal', default=None, type=int),
        id_empresa=request.args.get(key='id_empresa', default=None, type=int),
        cod_empresa=request.args.get(key='cod', default=None, type=int),
        nome=request.args.get(key='nome', default=None, type=str),
        ativo=request.args.get(key='ativo', default=None, type=int)
    )
    
    df = pd.read_sql(sql=query.statement, con=database.session.bind)
    
    # criar arquivo dentro da pasta
    nome_arqv = f'Empresas_{int(dt.datetime.now().timestamp())}.csv'
    camihno_arqv = f'{UPLOAD_FOLDER}/{nome_arqv}'
    df.to_csv(
        camihno_arqv,
        sep=';',
        index=False,
        encoding='iso-8859-1'
    )
    
    return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=nome_arqv)


# CRIAR EMPRESA ----------------------------------------
@app.route('/empresas/criar', methods=['GET', 'POST'])
@login_required
def criar_empresa():
    form = FormCriarEmpresa()

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )

    if form.validate_on_submit():
        empresa = Empresa(
            cod_empresa_principal=form.cod_empresa_principal.data,
            cod_empresa=form.cod_empresa.data,
            razao_social_inicial=form.razao_social_inicial.data,
            razao_social=form.razao_social.data,
            nome_abrev=form.nome_abrev.data,
            cnpj=form.cnpj.data,
            uf=form.uf.data,
            emails=form.emails.data,
            conv_exames_emails=form.emails_conv_exames.data,
            absenteismo_emails=form.emails_absenteismo.data,
            exames_realizados_emails=form.emails_exames_realizados.data,
            conv_exames=form.conv_exames.data,
            ativo=form.ativo.data,
            data_inclusao=dt.datetime.now(tz=timezone('America/Sao_Paulo')),
            incluido_por=current_user.username
        )
        database.session.add(empresa)
        database.session.commit()
        
        LogAcoes.registrar_acao(
            nome_tabela = 'Empresa',
            tipo_acao = 'Inclusão',
            id_registro = int(form.cod_empresa.data),
            nome_registro = form.razao_social.data
        )
        
        flash('Empresa criada com sucesso!', 'alert-success')
        return redirect(url_for('editar_empresa', id_empresa=empresa.id_empresa))
    
    return render_template('empresa/empresa_criar.html', form=form, title='GRS+Connect')


# EDITAR EMPRESA-----------------------------------------------------------
@app.route('/empresas/editar', methods=['GET', 'POST'])
@login_required
def editar_empresa():
    # query empresa da pag atual
    empresa: Empresa = Empresa.query.get(request.args.get(key='id_empresa', type=int))

    form = FormEditarEmpresa(
        cod_empresa_principal = empresa.cod_empresa_principal,
        cod_empresa = empresa.cod_empresa,
        razao_social = empresa.razao_social,
        razao_social_inicial = empresa.razao_social_inicial,
        nome_abrev = empresa.nome_abrev,
        cnpj = empresa.cnpj,
        uf = empresa.uf,
        emails = empresa.emails,
        emails_conv_exames = empresa.conv_exames_emails,
        emails_absenteismo = empresa.absenteismo_emails,
        emails_exames_realizados = empresa.exames_realizados_emails,
        ativo = empresa.ativo,
        conv_exames = empresa.conv_exames,
        data_inclusao = empresa.data_inclusao,
        data_alteracao = empresa.data_alteracao,
        incluido_por = empresa.incluido_por,
        alterado_por = empresa.alterado_por
    )

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )

    if form.validate_on_submit():
        empresa.cod_empresa_principal = form.cod_empresa_principal.data
        empresa.cod_empresa = form.cod_empresa.data
        empresa.razao_social = form.razao_social.data
        empresa.razao_social_inicial = form.razao_social_inicial.data
        empresa.nome_abrev = form.nome_abrev.data
        empresa.cnpj = form.cnpj.data
        empresa.uf = form.uf.data
        empresa.emails = form.emails.data
        empresa.conv_exames_emails = form.emails_conv_exames.data
        empresa.absenteismo_emails = form.emails_absenteismo.data
        empresa.exames_realizados_emails = form.emails_exames_realizados.data
        empresa.ativo = form.ativo.data
        empresa.conv_exames = form.conv_exames.data

        empresa.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
        empresa.alterado_por = current_user.username
        
        database.session.commit()
    
        LogAcoes.registrar_acao(
            nome_tabela = 'Empresa',
            tipo_acao = 'Alteração',
            id_registro = empresa.cod_empresa,
            nome_registro = empresa.razao_social
        )
        
        flash(f'Empresa atualizada com sucesso!', 'alert-success')

        return redirect(url_for('editar_empresa', id_empresa=empresa.id_empresa))
    
    return render_template(
        'empresa/empresa_editar.html',
        title='GRS+Connect',
        empresa=empresa,
        form=form,
        qtd_unidades=len(empresa.unidades)
    )


# EXCLUIR EMPRESA-----------------------------------------------------------
@app.route('/empresas/excluir', methods=['GET', 'POST'])
@login_required
@admin_required
def excluir_empresa():
    empresa = Empresa.query.get(request.args.get('id_empresa', type=int))
    
    # excluir empresa
    try:
        database.session.delete(empresa)
        database.session.commit()

        LogAcoes.registrar_acao(
            nome_tabela = 'Empresa',
            tipo_acao = 'Exclusão',
            id_registro = int(empresa.id_empresa),
            nome_registro = empresa.razao_social,
        )

        flash(f'Empresa excluída! Empresa: {empresa.id_empresa} - {empresa.razao_social}', 'alert-danger')
        return redirect(url_for('buscar_empresas'))
    except IntegrityError:
        database.session.rollback()
        flash(f'A empresa: {empresa.id_empresa} - {empresa.razao_social} não pode ser excluída, pois há outros registros associados a ela', 'alert-danger')
        return redirect(url_for('buscar_empresas'))


# BUSCA UNIDADES----------------------------------------
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


# UNIDADES----------------------------------------
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


# UNIDADES GERAR CSV----------------------------------------
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


# CRIAR UNIDADE ----------------------------------------
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


# EDITAR UNIDADE-----------------------------------------------------------
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


# EXCLUIR UNIDADE-----------------------------------------------------------
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


# EXTERNO - ATUALIZAR EMAILS UNIDADES ---------------------------------------------
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


# BUSCA PRESTADORES----------------------------------------
@app.route('/buscar_prestadores', methods=['GET', 'POST'])
@login_required
def buscar_prestadores():
    form = FormBuscarPrestador()

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )

    if form.validate_on_submit() and 'botao_buscar' in request.form:
        return redirect(
            url_for(
                'prestadores',
                cod_empresa_principal=form.cod_empresa_principal.data,
                id_prestador=form.id.data,
                cod=form.cod.data,
                nome=form.nome.data,
                ativo=form.ativo.data
            )
        )
    elif form.validate_on_submit() and 'botao_csv' in request.form:
        return redirect(
            url_for(
                'prestadores_csv',
                cod_empresa_principal=form.cod_empresa_principal.data,
                id_prestador=form.id.data,
                cod=form.cod.data,
                nome=form.nome.data,
                ativo=form.ativo.data
            )
        )

    return render_template(
        'prestador/busca.html',
        title='GRS+Connect',
        form=form
    )


# PRESTADORES----------------------------------------
@app.route('/prestadores')
@login_required
def prestadores():
    query = Prestador.buscar_prestadores(
        cod_empresa_principal=request.args.get(key='cod_empresa_principal', default=None, type=int),
        id_prestador=request.args.get(key='id_prestador', default=None, type=int),
        cod_prestador=request.args.get(key='cod', default=None, type=int),
        nome=request.args.get(key='nome', default=None, type=str),
        ativo=request.args.get(key='ativo', default=None, type=int)
    ).all()
    
    return render_template(
        'prestador/prestadores.html',
        title='GRS+Connect',
        lista_prestadores=query,
        qtd=len(query)
    )


# PRESTADORES GERAR CSV----------------------------------------
@app.route('/prestadores/csv')
@login_required
def prestadores_csv():
    query = Prestador.buscar_prestadores(
        cod_empresa_principal=request.args.get(key='cod_empresa_principal', default=None, type=int),
        id_prestador=request.args.get(key='id_prestador', default=None, type=int),
        cod_prestador=request.args.get(key='cod', default=None, type=int),
        nome=request.args.get(key='nome', default=None, type=str),
        ativo=request.args.get(key='ativo', default=None, type=int)
    )

    df = pd.read_sql(sql=query.statement, con=database.session.bind)

    # criar arquivo dentro da pasta
    nome_arqv = f'Prestadores_{int(dt.datetime.now().timestamp())}.csv'
    camihno_arqv = f'{UPLOAD_FOLDER}/{nome_arqv}'
    df.to_csv(
        camihno_arqv,
        sep=';',
        index=False,
        encoding='iso-8859-1'
    )

    return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=nome_arqv)


# CRIAR PRESTADOR-----------------------------
@app.route('/prestadores/criar', methods=['GET', 'POST'])
@login_required
def criar_prestador():
    form = FormCriarPrestador()

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )

    if form.validate_on_submit():
        prestador = Prestador(
            cod_empresa_principal=form.cod_empresa_principal.data,
            cod_prestador=form.cod_prestador.data,
            nome_prestador=form.nome_prestador.data,
            emails=form.emails.data,
            ativo=form.ativo.data,
            solicitar_asos=form.solicitar_asos.data,
            cnpj=form.cnpj.data,
            uf=form.uf.data,
            razao_social=form.razao_social.data,
            data_inclusao=dt.datetime.now(tz=timezone('America/Sao_Paulo')),
            incluido_por=current_user.username
        )
        database.session.add(prestador)
        database.session.commit()
        
        LogAcoes.registrar_acao(
            nome_tabela='Prestador',
            tipo_acao='Inclusão',
            id_registro=prestador.id_prestador,
            nome_registro=prestador.nome_prestador
        )
        
        flash('Prestador criado com sucesso!', 'alert-success')
        return redirect(url_for('editar_prestador', id_prestador=prestador.id_prestador))
    return render_template('prestador/prestador_criar.html', form=form, title='GRS+Connect')


# EDITAR PRESTADOR-----------------------------------------------------------
@app.route('/prestadores/editar', methods=['GET', 'POST'])
@login_required
def editar_prestador():    
    prestador = Prestador.query.get(request.args.get(key='id_prestador', type=int))

    form = FormEditarPrestador(
        cod_empresa_principal=prestador.cod_empresa_principal,
        cod_prestador=prestador.cod_prestador,
        nome_prestador=prestador.nome_prestador,
        emails=prestador.emails,
        ativo=prestador.ativo,
        solicitar_asos=prestador.solicitar_asos,
        cnpj=prestador.cnpj,
        uf=prestador.uf,
        razao_social=prestador.razao_social,
        data_inclusao=prestador.data_inclusao,
        data_alteracao=prestador.data_alteracao,
        incluido_por=prestador.incluido_por,
        alterado_por=prestador.alterado_por
    )

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )
   
    if form.validate_on_submit():
        prestador.cod_empresa_principal = form.cod_empresa_principal.data
        prestador.cod_prestador = form.cod_prestador.data
        prestador.nome_prestador = form.nome_prestador.data
        prestador.emails = form.emails.data
        prestador.ativo = form.ativo.data
        prestador.solicitar_asos = form.solicitar_asos.data
        prestador.cnpj = form.cnpj.data
        prestador.uf = form.uf.data
        prestador.razao_social = form.razao_social.data

        prestador.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
        prestador.alterado_por = current_user.username
        
        database.session.commit()
        
        LogAcoes.registrar_acao(
            nome_tabela = 'Prestador',
            tipo_acao = 'Alteração',
            id_registro = prestador.id_prestador,
            nome_registro = prestador.nome_prestador
        )
        
        flash(f'Prestador atualizado com sucesso!', 'alert-success')
        return redirect(url_for('editar_prestador', id_prestador=prestador.id_prestador))
        
    return render_template(
        'prestador/prestador_editar.html',
        title='GRS+Connect',
        prestador=prestador,
        form=form
    )


# EXCLUIR PRESTADOR-----------------------------------------------------------
@app.route('/prestadores/excluir', methods=['GET', 'POST'])
@login_required
@admin_required
def excluir_prestador():
    prestador = Prestador.query.get(request.args.get(key='id_prestador', type=int))

    if not prestador.pedidos:
        database.session.delete(prestador)
        database.session.commit()

        LogAcoes.registrar_acao(
            nome_tabela = 'Prestador',
            tipo_acao = 'Exclusão',
            id_registro = prestador.id_prestador,
            nome_registro = prestador.nome_prestador,
        )
        
        flash(f'Prestador excluído! Prestador: {prestador.id_prestador} - {prestador.nome_prestador}', 'alert-danger')
        return redirect(url_for('buscar_prestadores'))
    else:
        flash(f'O Prestador: {prestador.id_prestador} - {prestador.nome_prestador} não pode ser excluído, pois há outros registros associados a ele', 'alert-danger')
        return redirect(url_for('buscar_prestadores'))


# BUSCA EXAMES----------------------------------------
@app.route('/buscar_exames', methods=['GET', 'POST'])
@login_required
def busca_exames():
    form = FormBuscarExames()

    form.cod_empresa_principal.choices = (
        [('', 'Selecione')] +
        [(i.cod, i.nome) for i in EmpresaPrincipal.query.all()]
    )

    if form.validate_on_submit() and 'botao_buscar' in request.form:
        return redirect(
            url_for(
                'exames',
                cod_empresa_principal=form.cod_empresa_principal.data,
                id_exame=form.id.data,
                cod=form.cod.data,
                nome=form.nome.data,
                prazo=form.prazo.data
            )
        )

    elif form.validate_on_submit() and 'botao_csv' in request.form:
        return redirect(
            url_for(
                'exames_csv',
                cod_empresa_principal=form.cod_empresa_principal.data,
                id_exame=form.id.data,
                cod=form.cod.data,
                nome=form.nome.data,
                prazo=form.prazo.data
            )
        )

    return render_template(
        'exame/busca.html',
        title='GRS+Connect',
        form=form
    )


# EXAMES----------------------------------------
@app.route('/exames')
@login_required
def exames():
    query = Exame.buscar_exames(
        cod_empresa_principal=request.args.get(key='cod_empresa_principal', default=None, type=str),
        id_exame=request.args.get(key='id_exame', default=None, type=str),
        cod_exame=request.args.get(key='cod', default=None, type=str),
        nome=request.args.get(key='nome', default=None, type=str),
        prazo=request.args.get(key='prazo', default=None, type=int)
    ).all()

    qtd = len(query)

    return render_template(
        'exame/exames.html',
        title='GRS+Connect',
        lista_exames=query,
        qtd=qtd
    )


# EXAMES GERAR CSV----------------------------------------
@app.route('/exames_csv')
@login_required
def exames_csv():
    query = Exame.buscar_exames(
        cod_empresa_principal=request.args.get(key='cod_empresa_principal', default=None, type=str),
        id_exame=request.args.get(key='id_exame', default=None, type=str),
        cod_exame=request.args.get(key='cod', default=None, type=str),
        nome=request.args.get(key='nome', default=None, type=str),
        prazo=request.args.get(key='prazo', default=None, type=int)
    )
    
    df = pd.read_sql(sql=query.statement, con=database.session.bind)
    
    # criar arquivo dentro da pasta
    timestamp = int(dt.datetime.now().timestamp())
    nome_arqv = f'Exames_{timestamp}.csv'
    camihno_arqv = f'{UPLOAD_FOLDER}/{nome_arqv}'
    df.to_csv(
        camihno_arqv,
        sep=';',
        index=False,
        encoding='iso-8859-1'
    )
    
    return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=nome_arqv)


# CRIAR EXAME ----------------------------------------
@app.route('/exames/criar', methods=['GET', 'POST'])
@login_required
def criar_exame():
    form = FormCriarExame()

    if form.validate_on_submit():
        exame = Exame(
            cod_empresa_principal=form.cod_empresa_principal.data,
            cod_exame=form.cod_exame.data,
            nome_exame=form.nome_exame.data,
            prazo=form.prazo.data,
            data_inclusao=dt.datetime.now(tz=timezone('America/Sao_Paulo')),
            incluido_por=current_user.username
        )
        database.session.add(exame)
        database.session.commit()
        
        LogAcoes.registrar_acao(
            nome_tabela = 'Exame',
            tipo_acao = 'Inclusão',
            id_registro = exame.id_exame,
            nome_registro = exame.nome_exame
        )
        
        flash('Exame criado com sucesso!', 'alert-success')
        return redirect(url_for('editar_exame', id_exame=exame.id_exame))
    
    return render_template('exame/exame_criar.html', form=form, title='GRS+Connect')


# EDITAR EXAME-----------------------------------------------------------
@app.route('/exames/editar', methods=['GET', 'POST'])
@login_required
def editar_exame():
    exame = Exame.query.get(request.args.get(key='id_exame', type=int))

    form = FormEditarExame(
        cod_empresa_principal=exame.cod_empresa_principal,
        cod_exame=exame.cod_exame,
        nome_exame=exame.nome_exame,
        prazo=exame.prazo,
        data_inclusao=exame.data_inclusao,
        data_alteracao=exame.data_alteracao,
        incluido_por=exame.incluido_por,
        alterado_por=exame.alterado_por
    )

    if form.validate_on_submit():
        exame.cod_empresa_principal = form.cod_empresa_principal.data
        exame.cod_exame = form.cod_exame.data
        exame.nome_exame = form.nome_exame.data
        exame.prazo = form.prazo.data

        exame.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
        exame.alterado_por = current_user.username
        
        database.session.commit()
    
        LogAcoes.registrar_acao(
            nome_tabela = 'Exame',
            tipo_acao = 'Alteração',
            id_registro = exame.id_exame,
            nome_registro = exame.nome_exame
        )
        
        flash(f'Exame atualizado com sucesso!', 'alert-success')
        return redirect(url_for('editar_exame', id_exame=exame.id_exame))
    
    return render_template(
        'exame/exame_editar.html',
        title='GRS+Connect',
        exame=exame,
        form=form
    )


# EXCLUIR EXAME-----------------------------------------------------------
@app.route('/exames/excluir', methods=['GET', 'POST'])
@login_required
@admin_required
def excluir_exame():
    exame = Exame.query.get(request.args.get('id_exame', type=int))
    
    try:
        database.session.delete(exame)
        database.session.commit()

        LogAcoes.registrar_acao(
            nome_tabela = 'Exame',
            tipo_acao = 'Exclusão',
            id_registro = exame.id_exame,
            nome_registro = exame.nome_exame,
        )

        flash(f'Exame excluído! Exame: {exame.id_exame} - {exame.nome_exame}', 'alert-danger')
        return redirect(url_for('buscar_exames'))
    except IntegrityError:
        database.session.rollback()
        flash(f'O Exame: {exame.id_exame} - {exame.nome_exame} não pode ser excluído, pois há outros registros associados a ele', 'alert-danger')
        return redirect(url_for('buscar_exames'))


# IMPORTAR DADOS-----------------------------------------------------------
@app.route('/importar_dados/atualizar', methods=['GET', 'POST'])
@login_required
@admin_required
def importar_dados_atualizar():
    form = FormImportarDados()

    if form.validate_on_submit():
        # ler arquivo
        arqv = request.files['csv']
        data = arqv.read().decode('iso-8859-1')

        # tamnho maximo
        max_size_mb = app.config['MAX_UPLOAD_SIZE_MB']
        max_bytes = max_size_mb * 1024 * 1024

        if getsizeof(data) > max_bytes:
            flash(f'O arquivo deve ser menor que {max_size_mb} MB', 'alert-danger')
            return redirect(url_for('importar_dados_atualizar'))
        
        else:
            # ler string como objeto para csv
            df = pd.read_csv(
                filepath_or_buffer=StringIO(data),
                sep=';',
                encoding='iso-8859-1',
            )

            tabela = int(form.tabela.data)
            
            match tabela:
                case 1: # Empresa
                    colunas = ['id_empresa', 'emails']
                    if list(df.columns) == colunas:
                        colunas_atualizadas = list(df.columns[1:])
                        df.drop_duplicates(subset='id_empresa', inplace=True, ignore_index=True)
                        if 'emails' in df.columns:
                            df['emails'] = list(map(tratar_emails, df['emails']))
                        df = df.to_dict(orient='records')
                        database.session.bulk_update_mappings(Empresa, df)
                        database.session.commit()
                        flash(f'Empresas atualizadas com sucesso! Linhas: {len(df)}, Colunas: {colunas_atualizadas}', 'alert-success')
                        return redirect(url_for('importar_dados_atualizar'))
                    else:
                        flash('Erro ao validar as Colunas do Arquivo', 'alert-danger')
                        return redirect(url_for('importar_dados_atualizar'))

                case 2: # Unidade
                    colunas = ['id_unidade', 'emails']
                    if list(df.columns) == colunas:
                        colunas_atualizadas = list(df.columns[1:])
                        df.drop_duplicates(subset='id_unidade', inplace=True, ignore_index=True)
                        if 'emails' in df.columns:
                            df['emails'] = list(map(tratar_emails, df['emails']))
                        df = df.to_dict(orient='records')
                        database.session.bulk_update_mappings(Unidade, df)
                        database.session.commit()
                        flash(f'Unidades atualizadas com sucesso! Linhas: {len(df)}, Colunas: {colunas_atualizadas}', 'alert-success')
                        return redirect(url_for('importar_dados_atualizar'))
                    else:
                        flash('Erro ao validar as Colunas do Arquivo', 'alert-danger')
                        return redirect(url_for('importar_dados_atualizar'))

                case 3: # Exame
                    colunas = ['id_exame', 'prazo']
                    if list(df.columns) == colunas:
                        colunas_atualizadas = list(df.columns[1:])
                        df.drop_duplicates(subset='id_exame', inplace=True, ignore_index=True)
                        df = df.to_dict(orient='records')
                        database.session.bulk_update_mappings(Exame, df)
                        database.session.commit()
                        flash(f'Exames atualizados com sucesso! Linhas: {len(df)}, Colunas: {colunas_atualizadas}', 'alert-success')
                        return redirect(url_for('importar_dados_atualizar'))
                    else:
                        flash('Erro ao validar as Colunas do Arquivo', 'alert-danger')
                        return redirect(url_for('importar_dados_atualizar'))

    return render_template('/importar_dados.html', title='GRS+Connect', form=form)


# ATUALIZAR STATUS EM MASSA-----------------------------------------------------------
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

