from flask import jsonify
from flask_login import current_user, login_required

from src import app, database
from src.main.empresa.empresa import Empresa
from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
from src.main.empresa_socnet.empresa_socnet import EmpresaSOCNET
from src.main.exame.exame import Exame
from src.main.funcionario.funcionario import Funcionario
from src.main.grupo.grupo import (grupo_empresa, grupo_empresa_socnet,
                                  grupo_prestador)
from src.main.prestador.prestador import Prestador
from src.main.tipo_exame.tipo_exame import TipoExame
from src.main.unidade.unidade import Unidade


# FETCH EMPRESAS-----------------------------------------------------------
@app.route('/fetch_empresas/<int:cod_empresa_principal>/<int:todos>')
@login_required
def fetch_empresas(cod_empresa_principal, todos):
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


# FETCH EMPRESAS SOCNET-----------------------------------------------------------
@app.route('/fetch_empresas_socnet/<int:cod_empresa_principal>/<int:todos>')
@login_required
def fetch_empresas_socnet(cod_empresa_principal, todos):
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


# FETCH UNIDADES -----------------------------------------------------------
@app.route('/fetch_unidades/<int:cod_empresa_principal>/<int:id_empresa>')
@login_required
def fetch_unidades(cod_empresa_principal, id_empresa):
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
@login_required
def fetch_prestadores(cod_empresa_principal, todos):
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


# FETCH EXAMES-----------------------------------------------------------
@app.route('/fetch_exames/<int:cod_empresa_principal>')
@login_required
def fetch_exames(cod_empresa_principal):
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

