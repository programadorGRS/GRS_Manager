import os
from datetime import datetime

import pandas as pd
from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required
from sqlalchemy.exc import DatabaseError, SQLAlchemyError

from src import TIMEZONE_SAO_PAULO, UPLOAD_FOLDER, app
from src.extensions import database as db
from src.utils import zipar_arquivos

from ..empresa.empresa import Empresa
from ..empresa_socnet.empresa_socnet import EmpresaSOCNET
from ..log_acoes.log_acoes import LogAcoes
from ..prestador.prestador import Prestador
from ..usuario.usuario import Usuario
from .forms import FormGrupo, FormGrupoMembros
from .grupo import (Grupo, grupo_empresa, grupo_empresa_socnet,
                    grupo_prestador, grupo_usuario)

grupo_bp = Blueprint(
    name="grupo",
    import_name=__name__,
    url_prefix="/grupo",
    template_folder="templates",
)


@grupo_bp.route("/")
@login_required
def get_grupos():
    lista_grupos = Grupo.query.order_by(Grupo.nome_grupo).all()
    return render_template("grupo/listar.html", lista_grupos=lista_grupos)


@grupo_bp.route("/criar", methods=["GET", "POST"])
@login_required
def create_grupo():
    form = FormGrupo()

    if form.validate_on_submit():
        try:
            grupo = Grupo(
                nome_grupo=form.nome_grupo.data,
                data_inclusao=datetime.now(TIMEZONE_SAO_PAULO),
                incluido_por=current_user.username,  # type: ignore
            )
            db.session.add(grupo)  # type: ignore
            db.session.commit()  # type: ignore
        except (SQLAlchemyError, DatabaseError) as err:
            db.session.rollback()  # type: ignore
            app.logger.error(msg=err, exc_info=True)
            flash("Erro interno ao criar Grupo", "alert-danger")
            return redirect(url_for("grupo.get_grupos"))

        LogAcoes.registrar_acao(
            nome_tabela="Grupo",
            tipo_acao="Inclusão",
            id_registro=grupo.id_grupo,
            nome_registro=grupo.nome_grupo,
        )

        flash("Grupo criado com sucesso!", "alert-success")
        return redirect(url_for("grupo.get_grupos"))
    return render_template("grupo/criar.html", form=form)


@grupo_bp.route("/<int:id_grupo>", methods=["GET", "POST"])
@login_required
def update_grupo(id_grupo):
    grupo = Grupo.query.get(id_grupo)

    if not grupo:
        return abort(404)

    form = FormGrupo(
        nome_grupo=grupo.nome_grupo,
        data_inclusao=grupo.data_inclusao,
        data_alteracao=grupo.data_alteracao,
        incluido_por=grupo.incluido_por,
        alterado_por=grupo.alterado_por,
    )

    if form.validate_on_submit():
        try:
            grupo.nome_grupo = form.nome_grupo.data

            grupo.data_alteracao = datetime.now(TIMEZONE_SAO_PAULO)
            grupo.alterado_por = current_user.username  # type: ignore

            db.session.commit()  # type: ignore
        except (SQLAlchemyError, DatabaseError) as err:
            db.session.rollback()  # type: ignore
            app.logger.error(msg=err, exc_info=True)
            flash("Erro interno ao editar Grupo", "alert-danger")
            return redirect(url_for("grupo.get_grupos"))

        LogAcoes.registrar_acao(
            nome_tabela="Grupo",
            tipo_acao="Alteração",
            id_registro=grupo.id_grupo,
            nome_registro=form.nome_grupo.data,  # type: ignore
        )

        flash("Grupo editado com sucesso!", "alert-success")
        return redirect(url_for("grupo.get_grupos"))

    return render_template("grupo/editar.html", grupo=grupo, form=form)


@grupo_bp.route("/<int:id_grupo>/usuarios", methods=["GET", "POST"])
@login_required
def update_usuarios(id_grupo):
    grupo: Grupo = Grupo.query.get(id_grupo)

    if not grupo:
        return abort(404)

    # already in group
    pre_selected = [i.id_usuario for i in grupo.usuarios]
    form = FormGrupoMembros(select=pre_selected)
    form.load_usuarios_choices()

    FORM_LEGEND = "Editar Usuários"

    if form.validate_on_submit():
        try:
            Grupo.set_usuarios(
                id_grupo=grupo.id_grupo,
                id_usuarios=request.form.getlist(key="select", type=int),
                alterado_por=current_user.username,  # type: ignore
            )
        except (SQLAlchemyError, DatabaseError) as e:
            db.session.rollback()  # type: ignore
            app.logger.error(msg=e, exc_info=True)
            flash("Erro interno ao atualizar o Grupo", "alert-danger")
            return redirect(url_for("grupo.get_grupos"))

        LogAcoes.registrar_acao(
            nome_tabela="Grupo",
            tipo_acao="Editar Usuários",
            id_registro=grupo.id_grupo,
            nome_registro=grupo.nome_grupo,
        )

        return redirect(url_for("grupo.get_grupos"))

    return render_template(
        "grupo/editar_membros.html", form=form, form_legend=FORM_LEGEND, grupo=grupo
    )


@grupo_bp.route("/<int:id_grupo>/prestadores", methods=["GET", "POST"])
@login_required
def update_prestadores(id_grupo):
    grupo: Grupo = Grupo.query.get(id_grupo)

    if not grupo:
        return abort(404)

    FORM_LEGEND = "Editar Prestadores"

    #  already in group
    pre_selected = [i.id_prestador for i in grupo.prestadores]
    form = FormGrupoMembros(select=pre_selected)
    form.load_prestador_choices()

    if form.validate_on_submit():
        try:
            Grupo.set_prestadores(
                id_grupo=grupo.id_grupo,
                id_prestadores=request.form.getlist(key="select", type=int),
                alterado_por=current_user.username,  # type: ignore
            )
        except (SQLAlchemyError, DatabaseError) as e:
            app.logger.error(msg=e, exc_info=True)
            db.session.rollback()  # type: ignore
            flash("Erro interno ao atualizar o Grupo", "alert-danger")
            return redirect(url_for("grupo.get_grupos"))

        LogAcoes.registrar_acao(
            nome_tabela="Grupo",
            tipo_acao="Editar Prestadores",
            id_registro=grupo.id_grupo,
            nome_registro=grupo.nome_grupo,
        )

        return redirect(url_for("grupo.get_grupos"))

    return render_template(
        "grupo/editar_membros.html", form=form, form_legend=FORM_LEGEND, grupo=grupo
    )


@grupo_bp.route("/<int:id_grupo>/empresas", methods=["GET", "POST"])
@login_required
def update_empresas(id_grupo):
    grupo: Grupo = Grupo.query.get(id_grupo)

    if not grupo:
        return abort(404)

    FORM_LEGEND = "Editar Empresas"

    # already in group
    pre_selected = [i.id_empresa for i in grupo.empresas]
    form = FormGrupoMembros(select=pre_selected)
    form.load_empresas_choices()

    if form.validate_on_submit():
        try:
            Grupo.set_empresas(
                id_grupo=grupo.id_grupo,
                id_empresas=request.form.getlist(key="select", type=int),
                alterado_por=current_user.username,  # type: ignore
            )
        except (SQLAlchemyError, DatabaseError) as e:
            app.logger.error(msg=e, exc_info=True)
            db.session.rollback()  # type: ignore
            flash("Erro interno ao atualizar o Grupo", "alert-danger")
            return redirect(url_for("grupo.get_grupos"))

        LogAcoes.registrar_acao(
            nome_tabela="Grupo",
            tipo_acao="Editar Empresas",
            id_registro=int(grupo.id_grupo),
            nome_registro=grupo.nome_grupo,
        )

        return redirect(url_for("grupo.get_grupos"))

    return render_template(
        "grupo/editar_membros.html", form=form, form_legend=FORM_LEGEND, grupo=grupo
    )


@grupo_bp.route("/<int:id_grupo>/empresas-socnet", methods=["GET", "POST"])
@login_required
def update_empresas_socnet(id_grupo):
    grupo: Grupo = Grupo.query.get(id_grupo)

    if not grupo:
        return abort(404)

    FORM_LEGEND = "Editar Empresas SOCNET"

    # already in group
    pre_selected = [i.id_empresa for i in grupo.empresas_socnet]
    form = FormGrupoMembros(select=pre_selected)
    form.load_empresas_socnet_choices()

    if form.validate_on_submit():
        try:
            Grupo.set_empresas_socnet(
                id_grupo=grupo.id_grupo,
                id_empresas=request.form.getlist(key="select", type=int),
                alterado_por=current_user.username,  # type: ignore
            )
        except (SQLAlchemyError, DatabaseError) as e:
            app.logger.error(msg=e, exc_info=True)
            db.session.rollback()  # type: ignore
            flash("Erro interno ao atualizar o Grupo", "alert-danger")
            return redirect(url_for("grupo.get_grupos"))

        LogAcoes.registrar_acao(
            nome_tabela="Grupo",
            tipo_acao="Editar Empresas SOCNET",
            id_registro=int(grupo.id_grupo),
            nome_registro=grupo.nome_grupo,
        )

        return redirect(url_for("grupo.get_grupos"))

    return render_template(
        "grupo/editar_membros.html", form=form, form_legend=FORM_LEGEND, grupo=grupo
    )


@grupo_bp.route("/csv")
@login_required
def get_grupos_csv():
    timestamp = int(datetime.now().timestamp())

    # empresas
    q = (
        db.session.query(  # type: ignore
            Empresa.id_empresa,
            Empresa.razao_social,
            grupo_empresa.columns.id_grupo,
            Grupo.nome_grupo,
        )
        .outerjoin(
            grupo_empresa, Empresa.id_empresa == grupo_empresa.columns.id_empresa
        )
        .outerjoin(Grupo, Grupo.id_grupo == grupo_empresa.columns.id_grupo)
        .order_by(Empresa.razao_social)
    )
    df = pd.read_sql(sql=q.statement, con=db.session.bind)  # type: ignore
    df.to_csv(
        path_or_buf=os.path.join(UPLOAD_FOLDER, f"grupo_empresas_{timestamp}.csv"),
        sep=";",
        index=False,
        encoding="iso-8859-1",
        float_format="%.0f",
    )

    # empresas SOCNET
    q = (
        db.session.query(  # type: ignore
            EmpresaSOCNET.id_empresa,
            EmpresaSOCNET.nome_empresa,
            grupo_empresa_socnet.columns.id_grupo,
            Grupo.nome_grupo,
        )
        .outerjoin(
            grupo_empresa_socnet,
            EmpresaSOCNET.id_empresa == grupo_empresa_socnet.columns.id_empresa,
        )
        .outerjoin(Grupo, Grupo.id_grupo == grupo_empresa_socnet.columns.id_grupo)
        .order_by(EmpresaSOCNET.nome_empresa)
    )
    df = pd.read_sql(sql=q.statement, con=db.session.bind)  # type: ignore
    df.to_csv(
        path_or_buf=os.path.join(
            UPLOAD_FOLDER, f"grupo_empresas_socnet_{timestamp}.csv"
        ),
        sep=";",
        index=False,
        encoding="iso-8859-1",
        float_format="%.0f",
    )

    # prestadores
    q = (
        db.session.query(  # type: ignore
            Prestador.id_prestador,
            Prestador.nome_prestador,
            grupo_prestador.columns.id_grupo,
            Grupo.nome_grupo,
        )
        .outerjoin(
            grupo_prestador,
            Prestador.id_prestador == grupo_prestador.columns.id_prestador,
        )
        .outerjoin(Grupo, Grupo.id_grupo == grupo_prestador.columns.id_grupo)
        .order_by(Prestador.nome_prestador)
    )
    df = pd.read_sql(sql=q.statement, con=db.session.bind)  # type: ignore
    df.to_csv(
        path_or_buf=os.path.join(UPLOAD_FOLDER, f"grupo_prestadores_{timestamp}.csv"),
        sep=";",
        index=False,
        encoding="iso-8859-1",
        float_format="%.0f",
    )

    # usuarios
    q = (
        db.session.query(  # type: ignore
            Usuario.id_usuario,
            Usuario.username,
            grupo_usuario.columns.id_grupo,
            Grupo.nome_grupo,
        )
        .outerjoin(
            grupo_usuario, Usuario.id_usuario == grupo_usuario.columns.id_usuario
        )
        .outerjoin(Grupo, Grupo.id_grupo == grupo_usuario.columns.id_grupo)
        .order_by(Usuario.username)
    )
    df = pd.read_sql(sql=q.statement, con=db.session.bind)  # type: ignore
    df.to_csv(
        path_or_buf=os.path.join(UPLOAD_FOLDER, f"grupo_usuarios_{timestamp}.csv"),
        sep=";",
        index=False,
        encoding="iso-8859-1",
        float_format="%.0f",
    )

    # compactar
    pasta_zip = zipar_arquivos(
        caminhos_arquivos=[
            os.path.join(UPLOAD_FOLDER, f"grupo_empresas_{timestamp}.csv"),
            os.path.join(UPLOAD_FOLDER, f"grupo_empresas_socnet_{timestamp}.csv"),
            os.path.join(UPLOAD_FOLDER, f"grupo_prestadores_{timestamp}.csv"),
            os.path.join(UPLOAD_FOLDER, f"grupo_usuarios_{timestamp}.csv"),
        ],
        caminho_pasta_zip=os.path.join(UPLOAD_FOLDER, f"Grupos_{timestamp}.zip"),
    )

    return send_from_directory(
        directory=UPLOAD_FOLDER, path="/", filename=os.path.basename(pasta_zip)
    )


@grupo_bp.route("/<int:id_grupo>/excluir", methods=["GET", "POST"])
@login_required
def delete_grupo(id_grupo):
    grupo = Grupo.query.get(id_grupo)

    if not grupo:
        return abort(404)

    try:
        db.session.delete(grupo)  # type: ignore
        db.session.commit()  # type: ignore
    except (SQLAlchemyError, DatabaseError) as e:
        db.session.rollback()  # type: ignore
        app.logger.error(msg=e, exc_info=True)
        flash("Erro interno ao excluir o Grupo", "alert-danger")
        return redirect(url_for("grupo.get_grupos"))

    LogAcoes.registrar_acao(
        nome_tabela="Grupo",
        tipo_acao="Exclusão",
        id_registro=int(grupo.id_grupo),
        nome_registro=grupo.nome_grupo,
    )

    flash("Grupo excluído!", "alert-danger")
    return redirect(url_for("grupo.get_grupos"))
