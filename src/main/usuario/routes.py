import secrets
from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import (current_user, fresh_login_required, login_required,
                         login_user)
from sqlalchemy.exc import DatabaseError, SQLAlchemyError

from src import TIMEZONE_SAO_PAULO, app
from src.extensions import bcrypt
from src.extensions import database as db
from src.main.log_acoes.log_acoes import LogAcoes
from src.main.tipo_usuario.tipo_usuario import TipoUsuario
from src.main.usuario.usuario import Usuario
from src.utils import admin_required

from .forms import (FormAlterarChave, FormAlterarSenha, FormConfigUsuario,
                    FormCriarConta, FormEditarPerfil)


usuario_bp = Blueprint(
    name="usuario",
    import_name=__name__,
    url_prefix="/usuario",
    template_folder="templates",
)


@usuario_bp.route("/buscar/resultados")
@login_required
def listar_usuarios():
    lista_usuarios = db.session.query(Usuario).order_by(  # type: ignore
        Usuario.tipo_usuario, Usuario.username
    )

    return render_template("usuario/usuarios.html", lista_usuarios=lista_usuarios)


@usuario_bp.route("/<int:id_usuario>")
@login_required
def perfil_usuario(id_usuario):
    usuario = Usuario.query.get(id_usuario)

    if not usuario:
        abort(404)

    return render_template("usuario/perfil_usuario.html", usuario=usuario)


@usuario_bp.route("/criar", methods=["GET", "POST"])
@fresh_login_required
@admin_required
def criar_usuario():
    form = FormCriarConta()

    form.tipo_usuario.choices = [("", "Selecione")] + [
        (role.id_role, role.nome) for role in TipoUsuario.query.all()
    ]

    if form.validate_on_submit():
        usuario = Usuario.criar_usuario(
            username=form.username.data,
            nome_usuario=form.nome_usuario.data,
            telefone=form.tel.data,
            celular=form.cel.data,
            email=form.email.data,
            senha=form.senha.data,
            tipo_usuario=form.tipo_usuario.data,  # type: ignore
            incluido_por=current_user.username,  # type: ignore
        )

        LogAcoes.registrar_acao(
            nome_tabela="Usuario",
            tipo_acao="Inclusão",
            id_registro=usuario.id_usuario,
            nome_registro=usuario.username,
        )

        flash(f"Usuário {usuario.username} criado com sucesso!", "alert-success")
        return redirect(url_for("usuario.criar_usuario"))
    return render_template("usuario/criar_usuario.html", form=form)


@usuario_bp.route("/<int:id_usuario>/editar-perfil", methods=["GET", "POST"])
@fresh_login_required
def editar_perfil(id_usuario):
    usuario = Usuario.query.get(id_usuario)

    if not usuario:
        abort(404)

    form = FormEditarPerfil(
        username=usuario.username,
        nome_usuario=usuario.nome_usuario,
        email=usuario.email,
        tel=usuario.telefone,
        cel=usuario.celular,
    )
    form.id_usuario = id_usuario

    if form.validate_on_submit():
        denied_resp = __check_owner_or_admin(
            id_usuario=id_usuario, redirect_endpoint="editar_perfil"
        )
        if denied_resp:
            return denied_resp

        # NOTE: se mudar username, atualizar id cookie (invalida todas as sessoes dessa conta)
        if form.username.data != usuario.username:
            usuario.id_cookie = secrets.token_hex(16)
            if current_user.id_usuario == usuario.id_usuario:  # type: ignore
                # NOTE: logar usuario novamente com o novo id_cookie.
                login_user(usuario)

        usuario.username = form.username.data
        usuario.nome_usuario = form.nome_usuario.data
        usuario.email = form.email.data
        usuario.telefone = form.tel.data
        usuario.celular = form.cel.data
        usuario.data_alteracao = datetime.now(TIMEZONE_SAO_PAULO)
        usuario.alterado_por = current_user.username  # type: ignore

        db.session.commit()  # type: ignore

        LogAcoes.registrar_acao(
            nome_tabela="Usuario",
            tipo_acao="Alteração de Perfil",
            id_registro=usuario.id_usuario,
            nome_registro=usuario.username,
        )

        flash("Perfil atualizado com sucesso!", "alert-success")
        return redirect(url_for("usuario.editar_perfil", id_usuario=usuario.id_usuario))

    return render_template("usuario/editar_usuario.html", form=form, usuario=usuario)


@usuario_bp.route("/<int:id_usuario>/alterar-senha", methods=["GET", "POST"])
@fresh_login_required
def alterar_senha(id_usuario):
    usuario = Usuario.query.get(id_usuario)

    if not usuario:
        abort(404)

    form = FormAlterarSenha()

    if form.validate_on_submit():
        denied_resp = __check_owner_or_admin(
            id_usuario=id_usuario, redirect_endpoint="alterar_senha"
        )
        if denied_resp:
            return denied_resp

        # criptografar a senha
        senha = form.senha.data
        senha_cript = bcrypt.generate_password_hash(senha).decode("utf-8")
        usuario.senha = senha_cript

        # NOTE: gerar novo id cookie aleatorio (invalida todas as sessoes dessa conta)
        usuario.id_cookie = secrets.token_hex(16)

        if current_user.id_usuario == usuario.id_usuario:  # type: ignore
            # NOTE: logar usuario novamente com o novo id_cookie.
            login_user(usuario)

        usuario.data_alteracao = datetime.now(TIMEZONE_SAO_PAULO)
        usuario.alterado_por = current_user.username  # type: ignore
        db.session.commit()  # type: ignore

        LogAcoes.registrar_acao(
            nome_tabela="Usuario",
            tipo_acao="Alteração de Senha",
            id_registro=usuario.id_usuario,
            nome_registro=usuario.username,
        )

        flash("Senha alterada com sucesso!", "alert-success")
        return redirect(url_for("usuario.alterar_senha", id_usuario=usuario.id_usuario))

    return render_template("usuario/editar_senha.html", form=form, usuario=usuario)


@usuario_bp.route("/<int:id_usuario>/config", methods=["GET", "POST"])
@fresh_login_required
@admin_required
def config_usuario(id_usuario):
    usuario = Usuario.query.get(id_usuario)

    if not usuario:
        abort(404)

    form = FormConfigUsuario(ativo=usuario.ativo, tipo_usuario=usuario.role.id_role)

    form.tipo_usuario.choices = [("", "Selecione")] + [
        (role.id_role, role.nome) for role in TipoUsuario.query.all()
    ]

    if form.validate_on_submit():
        if form.ativo.data != usuario.ativo:
            # NOTE: invalida todas as sessoes da conta
            usuario.id_cookie = secrets.token_hex(16)

        usuario.ativo = form.ativo.data
        usuario.tipo_usuario = form.tipo_usuario.data

        usuario.data_alteracao = datetime.now(TIMEZONE_SAO_PAULO)
        usuario.alterado_por = current_user.username  # type: ignore

        db.session.commit()  # type: ignore

        LogAcoes.registrar_acao(
            nome_tabela="Usuario",
            tipo_acao="Alteração de Configs usuario",
            id_registro=usuario.id_usuario,
            nome_registro=usuario.username,
        )

        flash("Configurações alteradas com sucesso!", "alert-success")
        return redirect(
            url_for("usuario.config_usuario", id_usuario=usuario.id_usuario)
        )

    return render_template("usuario/configs_usuario.html", form=form, usuario=usuario)


@usuario_bp.route("/<int:id_usuario>/alterar_chave", methods=["GET", "POST"])
@fresh_login_required
def alterar_chave(id_usuario):
    usuario = Usuario.query.get(id_usuario)

    if not usuario:
        abort(404)

    form = FormAlterarChave()

    if form.validate_on_submit():
        denied_resp = __check_owner_or_admin(
            id_usuario=id_usuario, redirect_endpoint="alterar_chave"
        )
        if denied_resp:
            return denied_resp

        # criptografar a chave
        chave = form.chave.data
        chave_cript = bcrypt.generate_password_hash(chave).decode("utf-8")
        usuario.chave_api = chave_cript

        usuario.data_alteracao = datetime.now(TIMEZONE_SAO_PAULO)
        usuario.alterado_por = current_user.username  # type: ignore

        db.session.commit()  # type: ignore

        LogAcoes.registrar_acao(
            nome_tabela="Usuario",
            tipo_acao="Alteração de Chave integracao",
            id_registro=usuario.id_usuario,
            nome_registro=usuario.username,
        )

        flash("Chave de Acesso alterada com sucesso!", "alert-success")
        return redirect(url_for("usuario.alterar_chave", id_usuario=usuario.id_usuario))

    return render_template("usuario/alterar_chave.html", form=form, usuario=usuario)


@usuario_bp.route("/<int:id_usuario>/excluir", methods=["POST"])
@fresh_login_required
@admin_required
def excluir_usuario(id_usuario):
    usuario = Usuario.query.get(id_usuario)

    if not usuario:
        abort(404)

    try:
        db.session.delete(usuario)  # type: ignore
        db.session.commit()  # type: ignore
    except (SQLAlchemyError, DatabaseError) as e:
        db.session.rollback()  # type: ignore
        app.logger.error(e, exc_info=True)
        flash("Erro interno ao tentar excuir o usuário", "alert-danger")
        return redirect(url_for("usuario.listar_usuarios"))

    LogAcoes.registrar_acao(
        nome_tabela="Usuario",
        tipo_acao="Exclusão",
        id_registro=usuario.id_usuario,
        nome_registro=usuario.username,
    )

    flash("Usuário excluído!", "alert-danger")
    return redirect(url_for("usuario.listar_usuarios"))


def __check_owner_or_admin(id_usuario: int, redirect_endpoint: str):
    if current_user.id_usuario != id_usuario:  # type: ignore
        if current_user.tipo_usuario != 1:  # type: ignore
            # se usuario não for dono da conta e não for Admin: recusar
            flash("Você não tem permissão para executar esta ação", "alert-danger")
            return redirect(
                url_for(f"usuario.{redirect_endpoint}", id_usuario=id_usuario)
            )
