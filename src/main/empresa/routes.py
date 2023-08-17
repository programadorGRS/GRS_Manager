from datetime import datetime

import pandas as pd
from flask import (Blueprint, flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required

from src import TIMEZONE_SAO_PAULO, UPLOAD_FOLDER, database
from src.main.empresa.empresa import Empresa
from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
from src.utils import (get_data_from_args, get_data_from_form,
                       get_pagination_url_args)

from .forms import FormBuscarEmpresa, FormEmpresa


empresa = Blueprint(
    name="empresa",
    import_name=__name__,
    url_prefix="/empresa",
    template_folder="templates",
)


RESULTS_PER_PAGE = 200


@empresa.route("/buscar", methods=["GET", "POST"])
@login_required
def buscar_empresas():
    form: FormBuscarEmpresa = FormBuscarEmpresa()
    form.title = "Buscar Empresas"  # type: ignore

    form.cod_empresa_principal.choices = [("", "Selecione")] + [
        (i.cod, i.nome) for i in EmpresaPrincipal.query.all()
    ]

    if form.validate_on_submit():
        data = get_data_from_form(data=form.data)

        if "botao_buscar" in request.form:
            return redirect(url_for("empresa.empresas", **data))
        elif "botao_csv" in request.form:
            return redirect(url_for("empresa.empresas_csv", **data))

    return render_template("empresa/buscar.html", form=form)


@empresa.route("/buscar/resultados")
@login_required
def empresas():
    data = get_data_from_args(prev_form=FormBuscarEmpresa(), data=request.args)
    query = Empresa.buscar_empresas(**data)

    page_num = request.args.get(key="page", type=int, default=1)
    query_pagination = query.paginate(page=page_num, per_page=RESULTS_PER_PAGE)

    pagination_url_args = get_pagination_url_args(data=request.args)

    return render_template(
        "empresa/listar_empresas.html",
        page_title="Empresas",
        query=query_pagination,
        total=query.count(),
        results_per_page=RESULTS_PER_PAGE,
        pagination_url_args=pagination_url_args,
        pagination_endpoint="empresa.empresas",
        return_endpoint="empresa.buscar_empresas",
    )


@empresa.route("/csv")
@login_required
def empresas_csv():
    data = get_data_from_args(prev_form=FormBuscarEmpresa(), data=request.args)
    query = Empresa.buscar_empresas(**data)

    df = pd.read_sql(sql=query.statement, con=database.session.bind)  # type: ignore

    nome_arqv = f"Empresas_{int(datetime.now().timestamp())}.csv"
    camihno_arqv = f"{UPLOAD_FOLDER}/{nome_arqv}"
    df.to_csv(camihno_arqv, sep=";", index=False, encoding="iso-8859-1")

    return send_from_directory(directory=UPLOAD_FOLDER, path="/", filename=nome_arqv)


@empresa.route("/<int:id_empresa>", methods=["GET", "POST"])
@login_required
def editar_empresa(id_empresa):
    empresa: Empresa = Empresa.query.get(id_empresa)

    form: FormEmpresa = FormEmpresa(
        conv_exames=empresa.conv_exames,
        conv_exames_emails=empresa.conv_exames_emails,
        exames_realizados=empresa.exames_realizados,
        exames_realizados_emails=empresa.exames_realizados_emails,
        absenteismo=empresa.absenteismo,
        absenteismo_emails=empresa.absenteismo_emails,
        cipa_erros=empresa.conf_mandato.monit_erros,
        cipa_venc=empresa.conf_mandato.monit_venc,
        cipa_emails=empresa.conf_mandato.emails,
        load_cipa=empresa.conf_mandato.load_hist,
        dominios_email=empresa.dominios_email,
    )

    form.title = "Configurar Empresa"  # type: ignore

    if form.validate_on_submit():
        empresa.conv_exames = form.conv_exames.data
        empresa.conv_exames_emails = form.conv_exames_emails.data

        empresa.exames_realizados = form.exames_realizados.data
        empresa.exames_realizados_emails = form.exames_realizados_emails.data

        empresa.absenteismo = form.absenteismo.data
        empresa.absenteismo_emails = form.absenteismo_emails.data

        # CIPA
        empresa.conf_mandato.monit_erros = form.cipa_erros.data
        empresa.conf_mandato.monit_venc = form.cipa_venc.data
        empresa.conf_mandato.emails = form.cipa_emails.data
        empresa.conf_mandato.load_hist = form.load_cipa.data

        empresa.data_alteracao = datetime.now(tz=TIMEZONE_SAO_PAULO)
        empresa.alterado_por = current_user.username  # type: ignore

        empresa.dominios_email = form.dominios_email.data

        database.session.commit()  # type: ignore

        flash("Empresa atualizada com sucesso!", "alert-success")

        return redirect(
            url_for("empresa.editar_empresa", id_empresa=empresa.id_empresa)
        )

    return render_template("empresa/editar.html", empresa=empresa, form=form)
