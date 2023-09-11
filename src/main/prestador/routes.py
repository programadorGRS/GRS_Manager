import os
from datetime import datetime

import pandas as pd
from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required

from src import TIMEZONE_SAO_PAULO, UPLOAD_FOLDER, app
from src.extensions import database as db
from src.utils import get_data_from_args, get_data_from_form, tratar_emails

from ..empresa_principal.empresa_principal import EmpresaPrincipal
from .forms import FormBuscarPrestador, FormPrestador
from .prestador import Prestador

prestador_bp = Blueprint(
    name="prestador",
    import_name=__name__,
    url_prefix="/prestador",
    template_folder="templates",
    cli_group="prestador",
)


@prestador_bp.route("/buscar", methods=["GET", "POST"])
@login_required
def buscar_prestadores():
    form = FormBuscarPrestador()

    form.cod_emp_princ.choices = [("", "Selecione")] + [
        (i.cod, i.nome) for i in EmpresaPrincipal.query.all()
    ]

    if form.validate_on_submit():
        form_data = get_data_from_form(data=form.data)

        if "botao_buscar" in request.form:
            return redirect(url_for("prestador.listar_prestadores", **form_data))

        if "botao_csv" in request.form:
            return redirect(url_for("prestador.prestadores_csv", **form_data))

    return render_template("prestador/buscar.html", form=form)


@prestador_bp.route("/buscar/resultados")
@login_required
def listar_prestadores():
    args = get_data_from_args(prev_form=FormBuscarPrestador(), data=request.args)

    query = Prestador.buscar_prestadores(**args)

    return render_template(
        "prestador/listar.html", prestadores=query, qtd=query.count()
    )


@prestador_bp.route("/buscar/csv")
@login_required
def prestadores_csv():
    args = get_data_from_args(prev_form=FormBuscarPrestador(), data=request.args)

    query = Prestador.buscar_prestadores(**args)

    df = pd.read_sql(sql=query.statement, con=db.session.bind)  # type: ignore

    timestamp = int(datetime.now().timestamp())
    nome_arqv = f"Prestadores_{timestamp}.csv"

    camihno_arqv = os.path.join(UPLOAD_FOLDER, nome_arqv)
    df.to_csv(camihno_arqv, sep=";", index=False, encoding="iso-8859-1")

    return send_from_directory(directory=UPLOAD_FOLDER, path="/", filename=nome_arqv)


@prestador_bp.route("/<int:id_prestador>", methods=["GET", "POST"])
@login_required
def editar_prestador(id_prestador):
    prestador = Prestador.query.get(id_prestador)

    if not prestador:
        return abort(404)

    form = FormPrestador(
        emails=prestador.emails, solicitar_asos=prestador.solicitar_asos
    )

    if form.validate_on_submit():
        try:
            emails_tratados = tratar_emails(email_str=form.emails.data)
        except Exception as e:
            app.logger.error(msg=e, exc_info=True)
            flash("Erro ao validar os emails inseridos", "alert-danger")
            return redirect(
                url_for("prestador.editar_prestador", id_prestador=id_prestador)
            )

        prestador.emails = emails_tratados if emails_tratados else None
        prestador.solicitar_asos = form.solicitar_asos.data

        prestador.data_alteracao = datetime.now(tz=TIMEZONE_SAO_PAULO)
        prestador.alterado_por = current_user.username  # type: ignore

        db.session.commit()  # type: ignore

        flash("Prestador atualizado com sucesso!", "alert-success")
        return redirect(
            url_for("prestador.editar_prestador", id_prestador=id_prestador)
        )

    return render_template(
        "prestador/editar.html",
        prestador=prestador,
        form=form,
    )
