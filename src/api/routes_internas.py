import pandas as pd
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from src import database
from src.main.empresa.empresa import Empresa
from src.main.empresa_socnet.empresa_socnet import EmpresaSOCNET
from src.main.exame.exame import Exame
from src.main.grupo.grupo import (Grupo, grupo_empresa, grupo_empresa_socnet,
                                  grupo_prestador)
from src.main.prestador.prestador import Prestador
from src.main.unidade.unidade import Unidade


internal_api = Blueprint(
    name="internal_api",
    import_name=__name__,
    url_prefix=None,
    template_folder=None
)


# FETCH EMPRESAS-----------------------------------------------------------
@internal_api.route("/fetch_empresas/<int:cod_empresa_principal>/<int:todos>")
@login_required
def fetch_empresas(cod_empresa_principal, todos):
    filtros = [(Empresa.cod_empresa_principal == int(cod_empresa_principal))]
    joins = []

    if not todos:
        # query empresas do usuario atual
        subquery_grupos = [grupo.id_grupo for grupo in current_user.grupo]  # type: ignore
        filtros.append((grupo_empresa.columns.id_grupo.in_(subquery_grupos)))
        joins.append(
            (grupo_empresa, grupo_empresa.columns.id_empresa == Empresa.id_empresa)
        )

    query = database.session.query(Empresa.id_empresa, Empresa.razao_social).order_by(
        Empresa.razao_social
    )

    for arg in filtros:
        query = query.filter(*filtros)

    for arg in joins:
        query = query.outerjoin(*joins)

    opcoes = []
    for empresa in query:
        dic = {}
        dic["id"] = empresa.id_empresa
        dic["nome"] = empresa.razao_social
        opcoes.append(dic)

    return jsonify({"dados": opcoes})


# FETCH EMPRESAS-----------------------------------------------------------
@internal_api.route("/fetch_empresas_v2")
@login_required
def fetch_empresas2():
    cod_empresa_principal = request.args.get("cod_empresa_principal", type=int)
    status_empresas = request.args.get("status_empresas", type=int, default=None)
    filtro_grupos = request.args.get("filtro_grupos", type=str, default=None)

    if not cod_empresa_principal:
        return jsonify("cod_empresa_principal e obrigatorio"), 400

    filtros = [(Empresa.cod_empresa_principal == int(cod_empresa_principal))]
    joins = []

    if status_empresas is not None:
        filtros.append((Empresa.ativo == status_empresas))

    if filtro_grupos:
        filtro_grupos = Grupo.handle_group_filter(
            id_usuario=current_user.id_usuario,  # type: ignore
            tabela=grupo_empresa,
            grupo=filtro_grupos  # type: ignore
        )
        if filtro_grupos:
            filtros.append(filtro_grupos)

        joins.append((grupo_empresa, grupo_empresa.c.id_empresa == Empresa.id_empresa))

    query = database.session.query(
        Empresa.id_empresa, Empresa.razao_social, Empresa.ativo
    ).order_by(Empresa.razao_social)

    for arg in joins:
        query = query.join(arg)

    for arg in filtros:
        query = query.filter(arg)

    df = pd.read_sql(query.statement, database.session.bind)
    df.rename(columns={"id_empresa": "id", "razao_social": "nome"}, inplace=True)

    dados_json = df.to_dict(orient="records")

    return jsonify(dados_json)


# FETCH EMPRESAS SOCNET-----------------------------------------------------------
@internal_api.route("/fetch_empresas_socnet/<int:cod_empresa_principal>/<int:todos>")
@login_required
def fetch_empresas_socnet(cod_empresa_principal, todos):
    filtros = [(EmpresaSOCNET.cod_empresa_principal == int(cod_empresa_principal))]
    joins = []

    if not todos:
        # query empresas do usuario atual
        subquery_grupos = [grupo.id_grupo for grupo in current_user.grupo]  # type: ignore
        filtros.append((grupo_empresa_socnet.columns.id_grupo.in_(subquery_grupos)))
        joins.append(
            (
                grupo_empresa_socnet,
                grupo_empresa_socnet.columns.id_empresa == EmpresaSOCNET.id_empresa,
            )
        )

    query = database.session.query(
        EmpresaSOCNET.id_empresa, EmpresaSOCNET.nome_empresa
    ).order_by(EmpresaSOCNET.nome_empresa)

    for arg in filtros:
        query = query.filter(*filtros)

    for arg in joins:
        query = query.outerjoin(*joins)

    opcoes = []
    for empresa in query:
        dic = {}
        dic["id"] = empresa.id_empresa
        dic["nome"] = empresa.nome_empresa
        opcoes.append(dic)

    return jsonify({"dados": opcoes})


# FETCH UNIDADES -----------------------------------------------------------
@internal_api.route("/fetch_unidades/<int:cod_empresa_principal>/<int:id_empresa>")
@login_required
def fetch_unidades(cod_empresa_principal, id_empresa):
    unidades = (
        Unidade.query.filter_by(cod_empresa_principal=int(cod_empresa_principal))
        .filter_by(id_empresa=int(id_empresa))
        .order_by(Unidade.nome_unidade)
        .all()
    )
    opcoes = []
    for unidade in unidades:
        unidadeObj = {}
        unidadeObj["id"] = unidade.id_unidade
        unidadeObj["nome"] = unidade.nome_unidade
        opcoes.append(unidadeObj)

    return jsonify({"dados": opcoes})


# FETCH UNIDADES -----------------------------------------------------------
@internal_api.route(
    "/fetch_unidades_public/<int:cod_empresa_principal>/<int:id_empresa>"
)
def fetch_unidades_public(cod_empresa_principal, id_empresa):
    unidades = (
        Unidade.query.filter_by(cod_empresa_principal=int(cod_empresa_principal))
        .filter_by(id_empresa=int(id_empresa))
        .order_by(Unidade.nome_unidade)
        .all()
    )
    opcoes = []
    for unidade in unidades:
        unidadeObj = {}
        unidadeObj["id"] = unidade.id_unidade
        unidadeObj["nome"] = unidade.nome_unidade
        opcoes.append(unidadeObj)

    return jsonify({"dados": opcoes})


# FETCH PRESTADORES-----------------------------------------------------------
@internal_api.route("/fetch_prestadores/<int:cod_empresa_principal>/<int:todos>")
@login_required
def fetch_prestadores(cod_empresa_principal, todos):
    filtros = [(Prestador.cod_empresa_principal == cod_empresa_principal)]
    joins = []

    if not todos:
        subquery_grupos = [grupo.id_grupo for grupo in current_user.grupo]  # type: ignore
        filtros.append((grupo_prestador.columns.id_grupo.in_(subquery_grupos)))
        joins.append(
            (
                grupo_prestador,
                grupo_prestador.columns.id_prestador == Prestador.id_prestador,
            )
        )

    query = database.session.query(
        Prestador.id_prestador, Prestador.nome_prestador
    ).order_by(Prestador.nome_prestador)

    for arg in filtros:
        query = query.filter(*filtros)

    for arg in joins:
        query = query.outerjoin(*joins)

    opcoes = []
    for prestador in query:
        dic = {}
        dic["id"] = prestador.id_prestador
        dic["nome"] = prestador.nome_prestador
        opcoes.append(dic)

    return jsonify({"dados": opcoes})


# FETCH EXAMES-----------------------------------------------------------
@internal_api.route("/fetch_exames/<int:cod_empresa_principal>")
@login_required
def fetch_exames(cod_empresa_principal):
    query = (
        Exame.query.filter_by(cod_empresa_principal=int(cod_empresa_principal))
        .order_by(Exame.nome_exame)
        .all()
    )
    opcoes = []
    for i in query:
        obj = {}
        obj["id"] = i.id_exame
        obj["nome"] = i.nome_exame
        opcoes.append(obj)

    return jsonify({"dados": opcoes})
