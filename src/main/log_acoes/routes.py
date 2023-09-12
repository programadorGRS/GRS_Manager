import os
from datetime import datetime

import pandas as pd
from flask import (Blueprint, flash, redirect, render_template,
                   send_from_directory, url_for)
from flask_login import login_required

from src import UPLOAD_FOLDER
from src.extensions import database as db

from .forms import FormLogAcoes
from .log_acoes import LogAcoes

log_acoes_bp = Blueprint(
    name="log_acoes",
    import_name=__name__,
    url_prefix="/log-acoes",
    template_folder="templates",
)


@log_acoes_bp.route("/", methods=["GET", "POST"])
@login_required
def log_acoes():
    form = FormLogAcoes()

    form.tabela.choices = [("", "Selecione")] + (
        db.session.query(LogAcoes.tabela, LogAcoes.tabela)  # type: ignore
        .order_by(LogAcoes.tabela)
        .distinct()
        .all()
    )

    form.usuario.choices = [("", "Selecione")] + (
        db.session.query(LogAcoes.id_usuario, LogAcoes.username)  # type: ignore
        .order_by(LogAcoes.username)
        .distinct()
        .all()
    )

    if form.validate_on_submit():
        query = LogAcoes.pesquisar_log(
            inicio=form.data_inicio.data,
            fim=form.data_fim.data,
            usuario=form.usuario.data,
            tabela=form.tabela.data,
        )

        df = pd.read_sql(sql=query.statement, con=db.session.bind)  # type: ignore

        if df.empty:
            flash("Sem dados", "alert-info")
            return redirect(url_for("log_acoes.log_acoes"))

        # remover decimais da hora
        df["hora"] = list(map(lambda x: str(x).split(".")[0], df["hora"]))

        timestamp = int(datetime.now().timestamp())
        nome_arqv = f"Log_acoes_{timestamp}.csv"

        camihno_arqv = os.path.join(UPLOAD_FOLDER, nome_arqv)
        df.to_csv(camihno_arqv, sep=";", index=False, encoding="iso-8859-1")

        return send_from_directory(
            directory=UPLOAD_FOLDER, path="/", filename=nome_arqv
        )

    return render_template("log_acoes/log_acoes.html", form=form)
