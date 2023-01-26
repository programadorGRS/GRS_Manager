from os import abort

from flask import abort, jsonify
from flask_login import current_user

from manager import app, database
from manager.models import (Empresa, Exame, Prestador, Unidade,
                            grupo_empresa,
                            grupo_prestador)
from manager.models_socnet import EmpresaSOCNET, grupo_empresa_socnet


# FETCH EMPRESAS-----------------------------------------------------------
@app.route('/fetch_empresas/<int:cod_empresa_principal>/<int:todos>')
def fetch_empresas(cod_empresa_principal, todos):
    # se usuario esta logado
    if current_user.is_authenticated:
        
        filtros = [(Empresa.cod_empresa_principal == int(cod_empresa_principal))]
        joins = []
        
        if not todos:
            # query empresas do usuario atual
            subquery_grupos = [grupo.id_grupo for grupo in current_user.grupo]
            filtros.append((grupo_empresa.columns.id_grupo.in_(subquery_grupos)))
            joins.append((grupo_empresa, grupo_empresa.columns.id_empresa == Empresa.id_empresa))
        
        query = (
            database.session.query(
                Empresa.id_empresa,
                Empresa.razao_social
            )
            .order_by(Empresa.razao_social)
        )

        for arg in filtros:
            query = query.filter(*filtros)
        
        for arg in joins:
            query = query.outerjoin(*joins)

        opcoes = []
        for empresa in query:
            dic = {}
            dic['id'] = empresa.id_empresa
            dic['nome'] = empresa.razao_social
            opcoes.append(dic)
        
        return jsonify({'dados': opcoes})
    else:
        abort(404)


# FETCH EMPRESAS SOCNET-----------------------------------------------------------
@app.route('/fetch_empresas_socnet/<int:cod_empresa_principal>/<int:todos>')
def fetch_empresas_socnet(cod_empresa_principal, todos):
    # se usuario esta logado
    if current_user.is_authenticated:
        
        filtros = [(EmpresaSOCNET.cod_empresa_principal == int(cod_empresa_principal))]
        joins = []
        
        if not todos:
            # query empresas do usuario atual
            subquery_grupos = [grupo.id_grupo for grupo in current_user.grupo]
            filtros.append((grupo_empresa_socnet.columns.id_grupo.in_(subquery_grupos)))
            joins.append((grupo_empresa_socnet, grupo_empresa_socnet.columns.id_empresa == EmpresaSOCNET.id_empresa))
        
        query = (
            database.session.query(
                EmpresaSOCNET.id_empresa,
                EmpresaSOCNET.nome_empresa
            )
            .order_by(EmpresaSOCNET.nome_empresa)
        )

        for arg in filtros:
            query = query.filter(*filtros)
        
        for arg in joins:
            query = query.outerjoin(*joins)

        opcoes = []
        for empresa in query:
            dic = {}
            dic['id'] = empresa.id_empresa
            dic['nome'] = empresa.nome_empresa
            opcoes.append(dic)
        
        return jsonify({'dados': opcoes})
    else:
        abort(404)


# FETCH UNIDADES -----------------------------------------------------------
@app.route('/fetch_unidades/<int:cod_empresa_principal>/<int:id_empresa>')
def fetch_unidades(cod_empresa_principal, id_empresa):
    # se usuario esta logado
    if current_user.is_authenticated:
        unidades = (
            Unidade.query
            .filter_by(cod_empresa_principal=int(cod_empresa_principal))
            .filter_by(id_empresa=int(id_empresa))
            .order_by(Unidade.nome_unidade)
            .all()
        )
        opcoes = []
        for unidade in unidades:
            unidadeObj = {}
            unidadeObj['id'] = unidade.id_unidade
            unidadeObj['nome'] = unidade.nome_unidade
            opcoes.append(unidadeObj)
        
        return jsonify({'dados': opcoes})
    else:
        abort(404)


# FETCH UNIDADES -----------------------------------------------------------
@app.route('/fetch_unidades_public/<int:cod_empresa_principal>/<int:id_empresa>')
def fetch_unidades_public(cod_empresa_principal, id_empresa):
    unidades = (
        Unidade.query
        .filter_by(cod_empresa_principal=int(cod_empresa_principal))
        .filter_by(id_empresa=int(id_empresa))
        .order_by(Unidade.nome_unidade)
        .all()
    )
    opcoes = []
    for unidade in unidades:
        unidadeObj = {}
        unidadeObj['id'] = unidade.id_unidade
        unidadeObj['nome'] = unidade.nome_unidade
        opcoes.append(unidadeObj)
    
    return jsonify({'dados': opcoes})


# FETCH PRESTADORES-----------------------------------------------------------
@app.route('/fetch_prestadores/<int:cod_empresa_principal>/<int:todos>')
def fetch_prestadores(cod_empresa_principal, todos):
    # se usuario esta logado
    if current_user.is_authenticated:
        
        filtros = [(Prestador.cod_empresa_principal == cod_empresa_principal)]
        joins = []
        
        if not todos:
            subquery_grupos = [grupo.id_grupo for grupo in current_user.grupo]
            filtros.append((grupo_prestador.columns.id_grupo.in_(subquery_grupos)))
            joins.append((grupo_prestador, grupo_prestador.columns.id_prestador == Prestador.id_prestador))

        query = (
            database.session.query(
                Prestador.id_prestador,
                Prestador.nome_prestador
            )
            .order_by(Prestador.nome_prestador)
        )

        for arg in filtros:
            query = query.filter(*filtros)
        
        for arg in joins:
            query = query.outerjoin(*joins)

        opcoes = []
        for prestador in query:
            dic = {}
            dic['id'] = prestador.id_prestador
            dic['nome'] = prestador.nome_prestador
            opcoes.append(dic)
        
        return jsonify({'dados': opcoes})
    else:
        abort(404)


# FETCH EXAMES-----------------------------------------------------------
@app.route('/fetch_exames/<int:cod_empresa_principal>')
def fetch_exames(cod_empresa_principal):
    # se usuario esta logado
    if current_user.is_authenticated:
        query = (
            Exame.query
            .filter_by(cod_empresa_principal=int(cod_empresa_principal))
            .order_by(Exame.nome_exame)
            .all()
        )
        opcoes = []
        for i in query:
            obj = {}
            obj['id'] = i.id_exame
            obj['nome'] = i.nome_exame
            opcoes.append(obj)
        
        return jsonify({'dados': opcoes})
    else:
        abort(404)

