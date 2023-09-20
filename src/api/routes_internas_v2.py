import pandas as pd
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from src.extensions import database as db

from ..main.empresa.empresa import Empresa
from ..main.grupo.grupo import Grupo, grupo_empresa, grupo_prestador
from ..main.prestador.prestador import Prestador
from ..main.unidade.unidade import Unidade

internal_api_bp_v2 = Blueprint(
    name="internal-api-v2",
    import_name=__name__,
    url_prefix="/api/internal/",
    template_folder=None,
)


@internal_api_bp_v2.route("/empresa")
@login_required
def empresas():
    cod_emp_princ = request.args.get("cod_emp_princ", type=int)
    ativo = request.args.get("ativo", type=int, default=None)
    filtro_grupos = request.args.get("filtro_grupos", type=str, default=None)

    if not cod_emp_princ:
        return jsonify("cod_empresa_principal é obrigatorio"), 400

    filtros = [(Empresa.cod_empresa_principal == int(cod_emp_princ))]
    joins = []

    if ativo is not None:
        filtros.append((Empresa.ativo == ativo))

    if filtro_grupos:
        filtro_grupos = Grupo.handle_group_filter(
            id_usuario=current_user.id_usuario,  # type: ignore
            tabela=grupo_empresa,
            grupo=filtro_grupos,  # type: ignore
        )
        if filtro_grupos:
            filtros.append(filtro_grupos)

        joins.append((grupo_empresa, grupo_empresa.c.id_empresa == Empresa.id_empresa))

    query = (
        db.session.query(  # type: ignore
            Empresa.id_empresa, Empresa.razao_social, Empresa.ativo
        )
        .filter(*filtros)
        .order_by(Empresa.razao_social)
    )

    for arg in joins:
        query = query.join(arg)

    df = pd.read_sql(query.statement, db.session.bind)  # type: ignore

    df.rename(columns={"id_empresa": "id", "razao_social": "nome"}, inplace=True)

    dados_json = df.to_dict(orient="records")

    return jsonify(dados_json)


@internal_api_bp_v2.route("/prestador")
@login_required
def prestadores():
    cod_emp_princ = request.args.get("cod_emp_princ", type=int)
    ativo = request.args.get("ativo", type=int, default=None)
    filtro_grupos = request.args.get("filtro_grupos", type=str, default=None)

    if not cod_emp_princ:
        return jsonify("cod_empresa_principal é obrigatorio"), 400

    filtros = [(Prestador.cod_empresa_principal == int(cod_emp_princ))]
    joins = []

    if ativo is not None:
        filtros.append((Prestador.ativo == ativo))

    if filtro_grupos:
        filtro_grupos = Grupo.handle_group_filter(
            id_usuario=current_user.id_usuario,  # type: ignore
            tabela=grupo_prestador,
            grupo=filtro_grupos,  # type: ignore
        )
        if filtro_grupos:
            filtros.append(filtro_grupos)

        joins.append(
            (grupo_prestador, grupo_prestador.c.id_prestador == Prestador.id_prestador)
        )

    query = (
        db.session.query(  # type: ignore
            Prestador.id_prestador, Prestador.nome_prestador, Prestador.ativo
        )
        .filter(*filtros)
        .order_by(Prestador.nome_prestador)
    )

    for arg in joins:
        query = query.join(arg)

    df = pd.read_sql(query.statement, db.session.bind)  # type: ignore

    df.rename(columns={"id_prestador": "id", "nome_prestador": "nome"}, inplace=True)

    dados_json = df.to_dict(orient="records")

    return jsonify(dados_json)


@internal_api_bp_v2.route("/unidade")
@login_required
def unidades():
    id_empresa = request.args.get("id_empresa", type=int)
    ativo = request.args.get("ativo", type=int, default=None)

    if not id_empresa:
        return jsonify("id_empresa é obrigatorio"), 400

    filtros = [(Unidade.id_empresa == int(id_empresa))]
    joins = []

    if ativo is not None:
        filtros.append((Unidade.ativo == ativo))

    query = (
        db.session.query(  # type: ignore
            Unidade.id_unidade, Unidade.nome_unidade, Unidade.ativo
        )
        .filter(*filtros)
        .order_by(Unidade.nome_unidade)
    )

    for arg in joins:
        query = query.join(arg)

    df = pd.read_sql(query.statement, db.session.bind)  # type: ignore

    df.rename(columns={"id_unidade": "id", "nome_unidade": "nome"}, inplace=True)

    dados_json = df.to_dict(orient="records")

    return jsonify(dados_json)
