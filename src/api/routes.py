from datetime import datetime, timedelta

import jwt
import numpy as np
import pandas as pd
from flask import jsonify, request
from flask_sqlalchemy import BaseQuery
from pytz import timezone
from sqlalchemy import and_, func, or_

from src import app, bcrypt, database
from src.main.conv_exames.models import ConvExames, PedidoProcessamento
from src.main.empresa.empresa import Empresa
from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
from src.main.exame.exame import Exame
from src.main.funcionario.funcionario import Funcionario
from src.main.licenca.models import Licenca
from src.main.log_acoes.log_acoes import LogAcoes
from src.main.pedido.pedido import Pedido
from src.main.pedido_socnet.pedido_socnet import PedidoSOCNET
from src.main.status.status import Status
from src.main.unidade.unidade import Unidade
from src.main.usuario.usuario import Usuario
from src.utils import token_required


def organizar_grupos(pedido: object):
    '''
    Retorna lista que contem apenas os grupos que batem entre \
    Prestador e Empresa

    Args:
        pedido: um Pedido dentro de uma Query
    
    Returns:
        list[objeto sqlalchemy]

    Obs: helper function, usada nas routes de API
    '''
    grupos_prestador = pedido.prestador.grupo
    grupos_empresa = pedido.empresa.grupo

    return [grupo for grupo in grupos_prestador if grupo in grupos_empresa]


# GET TOKEN-----------------------------------------------------
@app.route('/get_token')
def get_token():
    auth_username = request.args.get(key='username', type=str) # id usuario
    auth_password = request.args.get(key='password', type=str)

    if auth_username and auth_password:
        usuario =  Usuario.query.get(int(auth_username))
        if usuario and usuario.chave_api and bcrypt.check_password_hash(
            usuario.chave_api.encode('utf-8'),
            auth_password
        ) and usuario.is_active:
            # unix timestamp como int (data_atual + 1 dia)
            timestamp_exp = int((datetime.utcnow() + timedelta(hours=12)).timestamp())
            # gerar token
            token = jwt.encode(
                payload={
                    'username': auth_username,
                    'password': auth_password,
                    'expires': timestamp_exp
                },
                key=app.config['SECRET_KEY'],
                algorithm='HS256'
            )
            return {'token': token}, 200
        else:
            return {"message": "Username ou password invalido"}, 200
    else:
        return {"message": "Providencie username e password"}, 200


# GET PEDIDO-----------------------------------------------------
@app.route('/get_pedido')
@token_required
def get_pedido():
    seq_ficha = request.args.get(key='seq_ficha', type=int)

    if not seq_ficha:
        return {"message": "Providencie seq_ficha (Integer)"}, 400 # bad request

    pedido = Pedido.query.filter_by(seq_ficha=seq_ficha).first()

    if pedido:
        if pedido.prestador:
            grupos = organizar_grupos(pedido)
            ids_grupos = [gp.id_grupo for gp in grupos]
            nomes_grupos = [gp.nome_grupo for gp in grupos]
        else:
            ids_grupos = None
            nomes_grupos = None

        return jsonify({
            "seq_ficha": pedido.seq_ficha,
            "cod_funcionario": pedido.cod_funcionario,
            "nome_funcionario": pedido.nome_funcionario,
            "data_ficha": str(pedido.data_ficha),
            "cod_tipo_exame": pedido.cod_tipo_exame,
            "nome_tipo_exame": pedido.tipo_exame.nome_tipo_exame,
            "cod_prestador": getattr(pedido.prestador, 'cod_prestador', None),
            "nome_prestador": getattr(pedido.prestador, 'nome_prestador', None),
            "cod_empresa": pedido.empresa.cod_empresa,
            "nome_empresa": pedido.empresa.razao_social,
            "cod_unidade": pedido.Unidade.cod_unidade,
            "nome_unidade": pedido.Unidade.nome_unidade,
            "id_status": pedido.id_status,
            "nome_status": pedido.status.nome_status,
            "id_grupos": ids_grupos,
            "nome_grupos": nomes_grupos,
            "data_recebido": str(pedido.data_recebido) if pedido.data_recebido else None,
            "obs": getattr(pedido, 'obs', None),
            "data_inclusao": str(pedido.data_inclusao) if pedido.data_inclusao else None,
            "data_alteracao": str(pedido.data_alteracao) if pedido.data_alteracao else None,
        }), 200
    else:
        return {"message": f"Pedido {seq_ficha} nao encontrado"}, 404 # not found


# PATCH PEDIDO-----------------------------------------------------
@app.route('/patch_pedido', methods=['PATCH'])
@token_required
def patch_pedido():
    seq_ficha = request.args.get(key='seq_ficha', type=int)
    id_status = request.args.get(key='id_status', type=int)
    data_recebido = request.args.get(key='data_recebido', type=str)
    obs = request.args.get(key='obs', type=str)

    if not seq_ficha:
        return {"message": "seq_ficha é obrigatório (Integer)"}, 400 # bad request
    if not id_status:
        return {"message": "id_status é obrigatório (Integer)"}, 400 # bad request

    pedido = Pedido.query.filter_by(seq_ficha=seq_ficha).first()

    if pedido:
        # validar status
        if id_status in [stt.id_status for stt in Status.query.all()]:

            log_acoes = {
                'status_1': pedido.id_status,
                'status_2': id_status
            }

            msg_retorno = {
                'message': 'Status atualizado com sucesso',
                'seq_ficha': seq_ficha,
                'id_status': id_status
            }

            if obs:
                log_acoes['obs_1'] = pedido.obs
                log_acoes['obs_2'] = obs
                msg_retorno['obs'] = obs
                pedido.obs = obs

            if data_recebido:
                try:
                    # validar formato da data
                    data_recebido = datetime.strptime(data_recebido, '%d-%m-%Y').date()
                    log_acoes['data_recebido_1'] = str(pedido.data_recebido)
                    log_acoes['data_recebido_2'] = str(data_recebido)
                    msg_retorno['data_recebido'] = str(data_recebido)
                    pedido.data_recebido = data_recebido
                except ValueError:
                    return {"message": "Formato de data invalido, utilize dd-mm-yyyy"}, 400 # bad request

            # atualizar tag do pedido
            status = Status.query.get(id_status)
            if status.finaliza_processo:
                pedido.id_status_lib = 2 # ok
            else:
                pedido.id_status_lib = Pedido.calcular_tag_prev_lib(data_prev=pedido.prev_liberacao)

            # registrar alterador
            dados = jwt.decode(
                jwt=request.args.get(key='token', type=str),
                key=app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            usuario = Usuario.query.get(int(dados['username']))
            pedido.alterado_por = usuario.username
            pedido.data_alteracao = datetime.now(tz=timezone('America/Sao_Paulo'))

            # atualizar status
            pedido.id_status = id_status
            database.session.commit()

            LogAcoes.registrar_acao_api(
                token = request.args.get('token'),
                nome_tabela = 'Pedido',
                tipo_acao = 'Atualizar Status (API)',
                id_registro = seq_ficha,
                nome_registro = pedido.nome_funcionario,
                observacao = str(log_acoes)
            )
            return msg_retorno, 200
        else:
            return {"message": "Indique uma Id de Status valida"}, 400
    else:
        return {"message": f"Pedido {seq_ficha} não encontrado"}, 404 # not found


# GET STATUS-----------------------------------------------------
@app.route('/get_status')
@token_required
def get_status():
    return {stt.id_status: stt.nome_status for stt in Status.query.all()}, 200


# GET PEDIDOS POR DATA-----------------------------------------------------
@app.route('/get_pedidos_data')
@token_required
def get_pedidos_data():
    data_inicio = request.args.get(key='data_inicio', type=str)
    data_fim = request.args.get(key='data_fim', type=str)
    if data_inicio and data_fim:
        try:
            inicio = datetime.strptime(data_inicio, '%d-%m-%Y').date()
            fim = datetime.strptime(data_fim, '%d-%m-%Y').date()
        except ValueError:
            return {"message": "Formato de data invalido, utilize dd-mm-yyyy"}, 400

        query = (
            database.session.query(Pedido)
            .filter(Pedido.data_ficha >= inicio)
            .filter(Pedido.data_ficha <= fim)
            .order_by(Pedido.data_ficha, Pedido.nome_funcionario)
            .all()
        )

        dados = []
        for pedido in query:
            if pedido.prestador:
                grupos = organizar_grupos(pedido)
                ids_grupos = [gp.id_grupo for gp in grupos]
                nomes_grupos = [gp.nome_grupo for gp in grupos]
            else:
                ids_grupos = None
                nomes_grupos = None

            dados.append({
                "seq_ficha": pedido.seq_ficha,
                "cod_funcionario": pedido.cod_funcionario,
                "nome_funcionario": pedido.nome_funcionario,
                "data_ficha": str(pedido.data_ficha),
                "cod_tipo_exame": pedido.cod_tipo_exame,
                "nome_tipo_exame": pedido.tipo_exame.nome_tipo_exame,
                "cod_prestador": getattr(pedido.prestador, 'cod_prestador', None),
                "nome_prestador": getattr(pedido.prestador, 'nome_prestador', None),
                "cod_empresa": pedido.empresa.cod_empresa,
                "nome_empresa": pedido.empresa.razao_social,
                "cod_unidade": pedido.Unidade.cod_unidade,
                "nome_unidade": pedido.Unidade.nome_unidade,
                "id_status": pedido.id_status,
                "nome_status": pedido.status.nome_status,
                "id_status_lib": pedido.status_lib.id_status_lib,
                "nome_status_lib": pedido.status_lib.nome_status_lib,
                "prev_liberacao": str(pedido.prev_liberacao) if pedido.prev_liberacao else None,
                "id_grupos": ids_grupos,
                "nome_grupos": nomes_grupos,
                "data_recebido": str(pedido.data_recebido) if pedido.data_recebido else None,
                "obs": getattr(pedido, 'obs', None),
                "data_inclusao": str(pedido.data_inclusao) if pedido.data_inclusao else None,
                "data_alteracao": str(pedido.data_alteracao) if pedido.data_alteracao else None,
            })

        return jsonify(dados), 200

    else:
        return {"message": "Indique data_inicio e data_fim"}, 400


# GET PEDIDOS POR DATA SOCNET-----------------------------------------------------
@app.route('/get_pedidos_data_socnet')
@token_required
def get_pedidos_data_socnet():
    data_inicio = request.args.get(key='data_inicio', type=str)
    data_fim = request.args.get(key='data_fim', type=str)
    if data_inicio and data_fim:
        try:
            inicio = datetime.strptime(data_inicio, '%d-%m-%Y').date()
            fim = datetime.strptime(data_fim, '%d-%m-%Y').date()
        except ValueError:
            return {"message": "Formato de data invalido, utilize dd-mm-yyyy"}, 400

        query = (
            database.session.query(PedidoSOCNET)
            .filter(PedidoSOCNET.data_ficha >= inicio)
            .filter(PedidoSOCNET.data_ficha <= fim)
            .order_by(PedidoSOCNET.data_ficha, PedidoSOCNET.nome_funcionario)
            .all()
        )

        dados = []
        for pedido in query:
            if pedido.prestador:
                grupos = organizar_grupos(pedido)
                ids_grupos = [gp.id_grupo for gp in grupos]
                nomes_grupos = [gp.nome_grupo for gp in grupos]
            else:
                ids_grupos = None
                nomes_grupos = None

            dados.append({
                "seq_ficha": pedido.seq_ficha,
                "cod_funcionario": pedido.cod_funcionario,
                "nome_funcionario": pedido.nome_funcionario,
                "data_ficha": str(pedido.data_ficha),
                "cod_tipo_exame": pedido.cod_tipo_exame,
                "nome_tipo_exame": pedido.tipo_exame.nome_tipo_exame,
                "cod_prestador": getattr(pedido.prestador, 'cod_prestador', None),
                "nome_prestador": getattr(pedido.prestador, 'nome_prestador', None),
                "cod_empresa": pedido.empresa.cod_empresa,
                "nome_empresa": pedido.empresa.nome_empresa,
                "id_status": pedido.id_status,
                "nome_status": pedido.status.nome_status,
                "id_grupos": ids_grupos,
                "nome_grupos": nomes_grupos,
                "data_recebido": str(pedido.data_recebido) if pedido.data_recebido else None,
                "obs": getattr(pedido, 'obs', None),
                "data_inclusao": str(pedido.data_inclusao) if pedido.data_inclusao else None,
                "data_alteracao": str(pedido.data_alteracao) if pedido.data_alteracao else None,
            })

        return jsonify(dados), 200

    else:
        return {"message": "Indique data_inicio e data_fim"}, 400


# GET LICENCAS-----------------------------------------------------
@app.route('/get_licencas')
@token_required
def get_licencas():
    id_empresa = request.args.get(key='id_empresa', type=int)
    data_inicio = request.args.get(key='data_inicio', type=str)
    data_fim = request.args.get(key='data_fim', type=str)

    if not id_empresa or not data_inicio or not data_fim:
        return {"message": "Os campos id_empresa (int), data_inicio e data_fim (str) sao obrigatorios"}, 400

    try:
        inicio = datetime.strptime(data_inicio, '%d-%m-%Y').date()
        fim = datetime.strptime(data_fim, '%d-%m-%Y').date()
    except ValueError:
        return {"message": "Formato de data invalido, utilize dd-mm-yyyy"}, 400
    
    query: BaseQuery = (
        database.session.query(
            Licenca,
            EmpresaPrincipal.nome,
            Empresa.cod_empresa,
            Empresa.razao_social,
            Unidade.cod_unidade,
            Unidade.nome_unidade,
            Funcionario.nome_setor,
            Funcionario.nome_cargo,
            Funcionario.id_funcionario,
            Funcionario.cod_funcionario,
            Funcionario.nome_funcionario,
            Funcionario.situacao
        )
        .join(EmpresaPrincipal, Licenca.cod_empresa_principal == EmpresaPrincipal.cod)
        .join(Empresa, Licenca.id_empresa == Empresa.id_empresa)
        .join(Unidade, Licenca.id_unidade == Unidade.id_unidade)
        .join(Funcionario, Licenca.id_funcionario == Funcionario.id_funcionario)
        .filter(Empresa.id_empresa == id_empresa)
        .filter(Licenca.data_inicio_licenca >= inicio)
        .filter(or_(
            Licenca.data_fim_licenca <= fim,
            Licenca.data_fim_licenca == None
        ))
    )

    dados: pd.DataFrame = pd.read_sql(sql=query.statement, con=database.session.bind)
    dados = dados[[
            'cod_empresa_principal',
            'nome',
            'cod_empresa',
            'razao_social',
            'cod_unidade',
            'nome_unidade',
            'nome_setor',
            'nome_cargo',
            'cod_funcionario',
            'nome_funcionario',
            'situacao',
            'tipo_licenca',
            'motivo_licenca',
            'cod_cid',
            'cid_contestado',
            'cid',
            'tipo_cid',
            'cod_medico',
            'nome_medico',
            'solicitante',
            'data_inclusao_licenca',
            'data_ficha',
            'data_inicio_licenca',
            'data_fim_licenca',
            'dias_afastado',
            'afast_horas',
            'periodo_afastado',
            'hora_inicio_licenca',
            'hora_fim_licenca',
            'abonado'
    ]]

    for col in ['data_inclusao_licenca','data_ficha', 'data_inicio_licenca', 'data_fim_licenca']:
        dados[col] = dados[col].astype(str).replace('None', None)

    dados_json: list[dict[str, any]] = dados.to_dict(orient='records')

    return jsonify(dados_json), 200

@app.route('/get_licencas_v2')
@token_required
def get_licencas2():
    cod_empresa_principal = request.args.get(key='cod_empresa_principal', type=int)
    subgrupo = request.args.get(key='subgrupo', type=str)

    if not cod_empresa_principal:
        return {"message": "cod_empresa_principal e obrigatorio"}

    query: BaseQuery = (
        database.session.query(
            Licenca,
            EmpresaPrincipal.nome,
            Empresa.cod_empresa,
            Empresa.razao_social,
            Unidade.cod_unidade,
            Unidade.nome_unidade,
            Funcionario.nome_setor,
            Funcionario.nome_cargo,
            Funcionario.id_funcionario,
            Funcionario.cod_funcionario,
            Funcionario.nome_funcionario,
            Funcionario.situacao
        )
        .join(EmpresaPrincipal, Licenca.cod_empresa_principal == EmpresaPrincipal.cod)
        .join(Empresa, Licenca.id_empresa == Empresa.id_empresa)
        .join(Unidade, Licenca.id_unidade == Unidade.id_unidade)
        .join(Funcionario, Licenca.id_funcionario == Funcionario.id_funcionario)
        .filter(Licenca.cod_empresa_principal == cod_empresa_principal)
    )

    if subgrupo == '0':
        query = query.filter(Empresa.subgrupo == None)
    elif subgrupo is not None:
        query = query.filter(Empresa.subgrupo == subgrupo)

    dados: pd.DataFrame = pd.read_sql(sql=query.statement, con=database.session.bind)
    dados = dados[[
            'cod_empresa_principal',
            'nome',
            'cod_empresa',
            'razao_social',
            'cod_unidade',
            'nome_unidade',
            'nome_setor',
            'nome_cargo',
            'cod_funcionario',
            'nome_funcionario',
            'situacao',
            'tipo_licenca',
            'motivo_licenca',
            'cod_cid',
            'cid_contestado',
            'cid',
            'tipo_cid',
            'cod_medico',
            'nome_medico',
            'solicitante',
            'data_inclusao_licenca',
            'data_ficha',
            'data_inicio_licenca',
            'data_fim_licenca',
            'dias_afastado',
            'afast_horas',
            'periodo_afastado',
            'hora_inicio_licenca',
            'hora_fim_licenca',
            'abonado'
    ]]

    for col in ['data_inclusao_licenca','data_ficha', 'data_inicio_licenca', 'data_fim_licenca']:
        dados[col] = dados[col].astype(str).replace('None', None)

    dados_json: list[dict[str, any]] = dados.to_dict(orient='records')

    return jsonify(dados_json)


# GET CONV EXAMES-----------------------------------------------------
@app.route('/get_conv_exames')
@token_required
def get_conv_exames():
    id_empresa = request.args.get(key='id_empresa', type=int)

    if not id_empresa:
        return {"message": "Indique id_empresa"}, 200

    models = [
        (ConvExames),
        (PedidoProcessamento),
        (Empresa),
        (Unidade),
        (Funcionario),
        (Exame)
    ]

    joins = [
        (PedidoProcessamento, ConvExames.id_proc == PedidoProcessamento.id_proc),
        (Empresa, ConvExames.id_empresa == Empresa.id_empresa),
        (Unidade, ConvExames.id_unidade == Unidade.id_unidade),
        (Funcionario, ConvExames.id_funcionario == Funcionario.id_funcionario),
        (Exame, ConvExames.id_exame == Exame.id_exame),
    ]

    # buscar pedido proc mais recente da empresa
    pedido_proc: PedidoProcessamento = (
        database.session.query(PedidoProcessamento.id_proc)
        .filter(PedidoProcessamento.id_empresa == id_empresa)
        .filter(PedidoProcessamento.resultado_importado == True)
        .order_by(PedidoProcessamento.id_proc.desc())
        .first()
    )

    if pedido_proc:
        query_conv_exames = (
            database.session.query(*models)
            .join(*joins)
            .filter(ConvExames.id_proc == pedido_proc.id_proc)
        )
    else:
        return jsonify([]), 200

    # usar o pandas e mais rapido do que iterar sobre as colunas /
    # da query para tranformar em dict
    dados = pd.read_sql(query_conv_exames.statement, con=database.session.bind)

    dados = dados[[
        'cod_empresa_principal',
        'id_proc',
        'cod_solicitacao',
        'data_criacao',
        'id_empresa',
        'cod_empresa',
        'razao_social',
        'cod_unidade',
        'nome_unidade',
        'nome_setor',
        'nome_cargo',
        'id_funcionario',
        'cod_funcionario',
        'nome_funcionario',
        'situacao',
        'data_adm',
        'nome_exame',
        'ult_pedido',
        'data_res',
        'refazer'
    ]]

    for col in ['data_criacao', 'data_adm','ult_pedido','data_res','refazer']:
        dados[col] = pd.to_datetime(dados[col]).dt.strftime('%Y-%m-%d')
    
    dados.replace({np.nan: None}, inplace=True)

    dados = dados.to_dict(orient='records')
    
    return jsonify(dados), 200


# GET EMPRESAS-----------------------------------------------------
@app.route('/get_empresas')
@token_required
def get_empresas():

    query = database.session.query(Empresa.cod_empresa_principal, Empresa.id_empresa, Empresa.razao_social)

    df = pd.read_sql(sql=query.statement, con=database.session.bind)

    return jsonify(df.to_dict(orient='records')), 200

@app.route('/get_ped_proc')
@token_required
def get_ped_proc():
    sub_query = (
        database.session.query(PedidoProcessamento.id_empresa, func.max(PedidoProcessamento.data_criacao).label('max_date'))
        .filter(PedidoProcessamento.resultado_importado == True)
        .group_by(PedidoProcessamento.id_empresa)
        .subquery()
    )

    query = (
        database.session.query(PedidoProcessamento)
        .join(
            sub_query, and_(
                sub_query.c.id_empresa == PedidoProcessamento.id_empresa,
                sub_query.c.max_date == PedidoProcessamento.data_criacao
            )
        )
    )

    df = pd.read_sql(sql=query.statement, con=database.session.bind)

    df.drop(columns=['relatorio_enviado', 'id_empresa'], inplace=True)
    df['data_criacao'] = pd.to_datetime(df['data_criacao']).dt.strftime('%d/%m/%Y')

    return jsonify(df.to_dict(orient='records')), 200

