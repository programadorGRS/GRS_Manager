from datetime import datetime

import pandas as pd
from flask import (Blueprint, flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required

from src import TIMEZONE_SAO_PAULO, UPLOAD_FOLDER
from src import database as db
from src.main.unidade.unidade import Unidade
from src.utils import (get_data_from_args, get_data_from_form,
                       get_pagination_url_args)

from .forms import FormBuscarUnidade, FormUnidade

_unidade = Blueprint(
    name="unidade",
    import_name=__name__,
    url_prefix="/unidade",
    template_folder="templates",
)

RESULTS_PER_PAGE = 200


@_unidade.route("/buscar", methods=["GET", "POST"])
@login_required
def buscar_unidades():
    form: FormBuscarUnidade = FormBuscarUnidade()
    form.load_choices()
    form.title = "Buscar Unidades"  # type: ignore

    if form.validate_on_submit():
        data = get_data_from_form(data=form.data)

        if "botao_buscar" in request.form:
            return redirect(url_for("unidade.unidades", **data))
        elif "botao_csv" in request.form:
            return redirect(url_for("unidade.unidades_csv", **data))

    return render_template("unidade/buscar.html", form=form)


@_unidade.route("/buscar/resultados")
@login_required
def unidades():
    data = get_data_from_args(prev_form=FormBuscarUnidade(), data=request.args)
    query = Unidade.buscar_unidades(**data)

    page_num = request.args.get(key="page", type=int, default=1)
    query_pagination = query.paginate(page=page_num, per_page=RESULTS_PER_PAGE)

    pagination_url_args = get_pagination_url_args(data=request.args)

    return render_template(
        "unidade/listar_unidades.html",
        page_title="Unidades",
        query=query_pagination,
        total=query.count(),
        results_per_page=RESULTS_PER_PAGE,
        pagination_url_args=pagination_url_args,
        pagination_endpoint="unidade.unidades",
        return_endpoint="unidade.buscar_unidades",
    )


@_unidade.route("/buscar/csv")
@login_required
def unidades_csv():
    data = get_data_from_args(prev_form=FormBuscarUnidade(), data=request.args)
    query = Unidade.buscar_unidades(**data)

    df = pd.read_sql(sql=query.statement, con=db.session.bind)  # type: ignore

    nome_arqv = f"Unidades_{int(datetime.now().timestamp())}.csv"
    camihno_arqv = f"{UPLOAD_FOLDER}/{nome_arqv}"
    df.to_csv(camihno_arqv, sep=";", index=False, encoding="iso-8859-1")

    return send_from_directory(directory=UPLOAD_FOLDER, path="/", filename=nome_arqv)


@_unidade.route("/<int:id_unidade>", methods=["GET", "POST"])
@login_required
def editar_unidade(id_unidade):
    unidade: Unidade = Unidade.query.get(id_unidade)

    form: FormUnidade = FormUnidade(
        conv_exames=unidade.conv_exames,
        conv_exames_emails=unidade.conv_exames_emails,
        exames_realizados=unidade.exames_realizados,
        exames_realizados_emails=unidade.exames_realizados_emails,
        absenteismo=unidade.absenteismo,
        absenteismo_emails=unidade.absenteismo_emails,
        mandatos_cipa=unidade.erros_mandt_cipa,
        mandatos_cipa_emails=unidade.mandatos_cipa_emails,
    )
    form.title = "Configurar Unidade"  # type: ignore

    if form.validate_on_submit():
        unidade.conv_exames = form.conv_exames.data
        unidade.conv_exames_emails = form.conv_exames_emails.data

        unidade.exames_realizados = form.exames_realizados.data
        unidade.exames_realizados_emails = form.exames_realizados_emails.data

        unidade.absenteismo = form.absenteismo.data
        unidade.absenteismo_emails = form.absenteismo_emails.data

        unidade.erros_mandt_cipa = form.mandatos_cipa.data
        unidade.mandatos_cipa_emails = form.mandatos_cipa_emails.data

        unidade.data_alteracao = datetime.now(tz=TIMEZONE_SAO_PAULO)
        unidade.alterado_por = current_user.username  # type: ignore

        db.session.commit()  # type: ignore

        flash("Unidade atualizada com sucesso!", "alert-success")

        return redirect(
            url_for("unidade.editar_unidade", id_unidade=unidade.id_unidade)
        )

    return render_template("unidade/editar.html", unidade=unidade, form=form)
