import os
from datetime import datetime

import pandas as pd
from flask import (Blueprint, flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required

from src import TIMEZONE_SAO_PAULO, UPLOAD_FOLDER
from src.extensions import database as db
from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
from src.main.exame.exame import Exame
from src.utils import get_data_from_args, get_data_from_form

from .forms import FormBuscarExames, FormExame

_exame_bp = Blueprint(
    name="exame",
    import_name=__name__,
    url_prefix="/exame",
    template_folder="templates",
)


@_exame_bp.route("/buscar", methods=["GET", "POST"])
@login_required
def buscar_exames():
    form = FormBuscarExames()

    form.cod_emp_princ.choices = [("", "Selecione")] + [
        (i.cod, i.nome) for i in EmpresaPrincipal.query.all()
    ]

    if form.validate_on_submit():
        data = get_data_from_form(form.data)
        if "botao_buscar" in request.form:
            return redirect(url_for("exame.listar_exames", **data))

        if "botao_csv" in request.form:
            return redirect(url_for("exame.exames_csv", **data))

    return render_template("exame/busca.html", form=form)


@_exame_bp.route("/buscar/resultados")
@login_required
def listar_exames():
    data = get_data_from_args(prev_form=FormBuscarExames(), data=request.args)
    query = Exame.buscar_exames(**data)
    return render_template("exame/exames.html", lista_exames=query, qtd=query.count())


@_exame_bp.route("/buscar/csv")
@login_required
def exames_csv():
    data = get_data_from_args(prev_form=FormBuscarExames(), data=request.args)
    query = Exame.buscar_exames(**data)

    df = pd.read_sql(sql=query.statement, con=db.session.bind)  # type: ignore
    if df.empty:
        flash("Sem resultados", "alert-info")
        return redirect(url_for("exame.buscar_exames"))

    timestamp = int(datetime.now().timestamp())
    nome_arqv = os.path.join(UPLOAD_FOLDER, f"Exames_{timestamp}.xlsx")
    df.to_excel(nome_arqv, index=False, freeze_panes=(1, 0))

    return send_from_directory(
        directory=UPLOAD_FOLDER, path="/", filename=os.path.basename(nome_arqv)
    )


@_exame_bp.route("/<int:id_exame>", methods=["GET", "POST"])
@login_required
def editar_exame(id_exame):
    exame = Exame.query.get(id_exame)

    form = FormExame(prazo_exame=exame.prazo)

    if form.validate_on_submit():
        exame.prazo = form.prazo_exame.data
        exame.data_alteracao = datetime.now(tz=TIMEZONE_SAO_PAULO)
        exame.alterado_por = current_user.username  # type: ignore
        db.session.commit()  # type: ignore

        flash("Exame atualizado com sucesso!", "alert-success")
        return redirect(url_for("exame.editar_exame", id_exame=exame.id_exame))

    return render_template("exame/exame_editar.html", exame=exame, form=form)
