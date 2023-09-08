import os
from datetime import datetime

import pandas as pd
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_login import login_required
from werkzeug.utils import secure_filename

from src import UPLOAD_FOLDER
from src.extensions import database as db
from src.main.empresa.empresa import Empresa
from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
from src.main.unidade.unidade import Unidade
from src.utils import get_data_from_args, get_data_from_form, zipar_arquivos

from .exames_realizados import ExamesRealizados
from .forms import FormBuscarExamesRealizados

exames_realizados_bp = Blueprint(
    name="exames_realizados",
    import_name=__name__,
    url_prefix="/exames-realizados",
    template_folder="templates",
)


@exames_realizados_bp.route("/buscar", methods=["GET", "POST"])
@login_required
def exames_realizados_busca():
    form = FormBuscarExamesRealizados()

    form.cod_emp_princ.choices = [("", "Selecione")] + [
        (i.cod, i.nome)
        for i in EmpresaPrincipal.query.order_by(EmpresaPrincipal.nome).all()
    ]

    if form.validate_on_submit():
        args = get_data_from_form(data=form.data)
        return redirect(
            url_for("exames_realizados.exames_realizados_relatorios", **args)
        )

    return render_template("exames_realizados/busca.html", form=form)


@exames_realizados_bp.route("/gerar-relatorios", methods=["GET", "POST"])
@login_required
def exames_realizados_relatorios():
    args = get_data_from_args(prev_form=FormBuscarExamesRealizados(), data=request.args)

    query = ExamesRealizados.buscar_exames_realizados(**args)

    df = pd.read_sql(sql=query.statement, con=db.session.bind)  # type: ignore

    if df.empty:
        flash("Sem dados", "alert-info")
        return redirect(url_for("exames_realizados.exames_realizados_busca"))

    cod_emp_princ = args.get("cod_emp_princ")
    id_empresa = args.get("id_empresa")
    id_unidade = args.get("id_unidade")

    nome_empresa = None
    nome_unidade = None

    if cod_emp_princ:
        empresa = EmpresaPrincipal.query.get(cod_emp_princ)
        if empresa:
            nome_empresa = empresa.nome

    if id_empresa:
        empresa = Empresa.query.get(id_empresa)
        if empresa:
            nome_empresa = empresa.razao_social

    if id_unidade:
        unidade = Unidade.query.get(id_unidade)
        if unidade:
            nome_unidade = unidade.nome_unidade

    nome_entidade = "Todas Empresas"
    if nome_unidade:
        nome_entidade = nome_unidade
    elif nome_empresa:
        nome_entidade = nome_empresa

    nome_entidade = secure_filename(nome_entidade).replace(".", "_").upper()
    timestamp = int(datetime.now().timestamp())
    caminho_arqvs = os.path.join(
        UPLOAD_FOLDER, f"ExamesRealizados_{nome_entidade}_{timestamp}"
    )

    nome_excel = f"{caminho_arqvs}.xlsx"
    df_excel = df[ExamesRealizados.COLS_PLANILHA]
    df_excel.to_excel(nome_excel, index=False, freeze_panes=(1, 0))

    arquivos_zipar = [nome_excel]

    if len(df) >= 50:
        nome_ppt = f"{caminho_arqvs}.pptx"

        ExamesRealizados.criar_ppt(
            df=df,
            nome_arquivo=nome_ppt,
            nome_empresa=nome_empresa or "Todas",
            nome_unidade=nome_unidade or "Todas",
        )

        arquivos_zipar.append(nome_ppt)

    pasta_zip = zipar_arquivos(
        caminhos_arquivos=arquivos_zipar, caminho_pasta_zip=f"{caminho_arqvs}.zip"
    )

    return send_from_directory(
        directory=UPLOAD_FOLDER, path="/", filename=os.path.basename(pasta_zip)
    )
