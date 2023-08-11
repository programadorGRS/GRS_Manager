from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from src import TIMEZONE_SAO_PAULO
from src.extensions import database as db
from src.main.status.status import Status
from src.main.status.status_rac import StatusRAC
from src.utils import admin_required

from .forms import FormCriarStatus

_status_bp = Blueprint(
    name="status",
    import_name=__name__,
    url_prefix="/status",
    template_folder="templates",
)


@_status_bp.route("/buscar/resultados")
@login_required
def listar_status():
    lista_status = Status.query.all()
    return render_template("status/status.html", lista_status=lista_status)


@_status_bp.route("/criar", methods=["GET", "POST"])
@login_required
def criar_status():
    form = FormCriarStatus()

    if form.validate_on_submit():
        status = Status(
            nome_status=form.nome_status.data,
            finaliza_processo=form.finaliza_processo.data,
            data_inclusao=datetime.now(TIMEZONE_SAO_PAULO),
            incluido_por=current_user.username,  # type: ignore
        )

        db.session.add(status)  # type: ignore
        db.session.commit()  # type: ignore

        flash("Status criado com sucesso!", "alert-success")
        return redirect(url_for("status.listar_status"))
    return render_template("status/status_criar.html", form=form)


@_status_bp.route("/<int:id_status>", methods=["GET", "POST"])
@login_required
def editar_status(id_status):
    status: Status = Status.query.get(id_status)

    form = FormCriarStatus(
        nome_status=status.nome_status,
        finaliza_processo=status.finaliza_processo,
        data_inclusao=status.data_inclusao,
        data_alteracao=status.data_alteracao,
        incluido_por=status.incluido_por,
        alterado_por=status.alterado_por,
    )

    if form.validate_on_submit():
        if status.status_padrao:
            flash(
                f'O Status "{status.nome_status}" não pode ser editado', "alert-danger"
            )
            return redirect(url_for("status.listar_status"))

        status.nome_status = form.nome_status.data
        status.finaliza_processo = form.finaliza_processo.data
        status.data_alteracao = datetime.now(TIMEZONE_SAO_PAULO)
        status.alterado_por = current_user.username  # type: ignore
        db.session.commit()  # type: ignore

        flash("Status editado com sucesso!", "alert-success")
        return redirect(url_for("status.listar_status"))

    return render_template("status/status_editar.html", form=form, status=status)


@_status_bp.route("/excluir/<int:id_status>", methods=["GET", "POST"])
@login_required
@admin_required
def excluir_status(id_status):
    status: Status = Status.query.get(id_status)

    if status.status_padrao:
        flash(f'O Status "{status.nome_status}" não pode ser excluído', "alert-danger")
        return redirect(url_for("status.listar_status"))

    try:
        db.session.delete(status)  # type: ignore
        db.session.commit()  # type: ignore
        flash(
            f"Status excluído! Status: {status.id_status} - {status.nome_status}",
            "alert-danger",
        )
        return redirect(url_for("status.listar_status"))
    except IntegrityError:
        db.session.rollback()  # type: ignore
        flash(
            (
                f"O Status: {status.id_status} - {status.nome_status} não pode"
                "ser excluído, pois há outros registros associados a ele"
            ),
            "alert-danger",
        )
        return redirect(url_for("status.listar_status"))


@_status_bp.route("/status-rac/buscar/resultados")
@login_required
def listar_status_rac():
    lista_status = StatusRAC.query.all()
    return render_template("status/status_rac.html", lista_status=lista_status)


@_status_bp.route("/status-rac/criar", methods=["GET", "POST"])
@login_required
def criar_status_rac():
    form = FormCriarStatus()

    if form.validate_on_submit():
        status = StatusRAC(
            nome_status=form.nome_status.data,
            data_inclusao=datetime.now(TIMEZONE_SAO_PAULO),
            incluido_por=current_user.username,  # type: ignore
        )

        db.session.add(status)  # type: ignore
        db.session.commit()  # type: ignore

        flash("Status RAC criado com sucesso!", "alert-success")
        return redirect(url_for("status.listar_status_rac"))
    return render_template("status/status_rac_criar.html", form=form)


@_status_bp.route("/status-rac/<int:id_status>", methods=["GET", "POST"])
@login_required
def editar_status_rac(id_status):
    status: StatusRAC = StatusRAC.query.get(id_status)

    form = FormCriarStatus(
        nome_status=status.nome_status,
        data_inclusao=status.data_inclusao,
        data_alteracao=status.data_alteracao,
        incluido_por=status.incluido_por,
        alterado_por=status.alterado_por,
    )

    if form.validate_on_submit():
        if status.status_padrao:
            flash(
                f'O Status RAC "{status.nome_status}" não pode ser editado',
                "alert-danger",
            )
            return redirect(url_for("status.listar_status_rac"))

        status.nome_status = form.nome_status.data
        status.data_alteracao = datetime.now(TIMEZONE_SAO_PAULO)
        status.alterado_por = current_user.username  # type: ignore
        db.session.commit()  # type: ignore

        flash("Status RAC editado com sucesso!", "alert-success")
        return redirect(url_for("status.listar_status_rac"))

    return render_template(
        "status/status_rac_editar.html",
        form=form,
        status=status,
    )


@_status_bp.route("/status-rac/excluir/<int:id_status>", methods=["GET", "POST"])
@login_required
@admin_required
def excluir_status_rac(id_status):
    status: StatusRAC = StatusRAC.query.get(id_status)

    if status.status_padrao:
        flash(
            f'O Status RAC"{status.nome_status}" não pode ser excluído', "alert-danger"
        )
        return redirect(url_for("status.listar_status_rac"))

    try:
        db.session.delete(status)  # type: ignore
        db.session.commit()  # type: ignore

        flash(
            f"Status RAC excluído! Status: {status.id_status} - {status.nome_status}",
            "alert-danger",
        )
        return redirect(url_for("status.listar_status_rac"))
    except IntegrityError:
        db.session.rollback()  # type: ignore
        flash(
            f"O Status RAC: {status.id_status} - {status.nome_status} não pode ser excluído, pois há outros registros associados a ele",
            "alert-danger",
        )
        return redirect(url_for("status.listar_status_rac"))
