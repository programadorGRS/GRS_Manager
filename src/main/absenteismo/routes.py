import os
from datetime import datetime

import pandas as pd
from flask import (Blueprint, flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import login_required
from werkzeug.utils import secure_filename

from src import UPLOAD_FOLDER
from src.extensions import database as db
from src.main.empresa.empresa import Empresa
from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
from src.main.funcionario.funcionario import Funcionario
from src.main.unidade.unidade import Unidade
from src.utils import get_data_from_args, get_data_from_form, zipar_arquivos

from .absenteismo import Absenteismo
from .forms import FormBuscarAbsenteismo

absenteismo_bp = Blueprint(
    name="absenteismo",
    import_name=__name__,
    url_prefix="/absenteismo",
    template_folder="templates",
)


@absenteismo_bp.route("/buscar", methods=["GET", "POST"])
@login_required
def absenteismo_busca():
    form = FormBuscarAbsenteismo()

    form.cod_emp_princ.choices = [("", "Selecione")] + [
        (i.cod, i.nome)
        for i in EmpresaPrincipal.query.order_by(EmpresaPrincipal.nome).all()
    ]

    if form.validate_on_submit():
        return redirect(
            url_for("absenteismo.absenteismo_relatorios", **get_data_from_form(data=form.data))
        )

    return render_template("absenteismo/busca.html", form=form)


@absenteismo_bp.route("/relatorios", methods=["GET", "POST"])
@login_required
def absenteismo_relatorios():
    data = get_data_from_args(FormBuscarAbsenteismo(), data=request.args)

    query = Absenteismo.buscar_licencas(**data)

    df = pd.read_sql(sql=query.statement, con=db.session.bind)  # type: ignore
    if df.empty:
        flash("A pesquisa não gerou dados", "alert-info")
        return redirect(url_for("absenteismo.absenteismo_busca"))

    id_unidade = data.get("id_unidade", None)
    id_empresa = data.get("id_empresa", None)
    cod_emp_princ = data.get("cod_emp_princ", None)

    nome_empresa = __get_nome_empresa(
        cod_emp_princ=cod_emp_princ,
        id_empresa=id_empresa,
    )

    qtd_ativos = __get_qtd_ativos(
        cod_emp_princ=cod_emp_princ, id_empresa=id_empresa, id_unidade=id_unidade
    )

    timestamp = int(datetime.now().timestamp())
    nome_arquivo = secure_filename(nome_empresa).replace("/", "_")
    caminho_arqvs = os.path.join(
        UPLOAD_FOLDER, f"Absenteismo_{nome_arquivo}_{timestamp}"
    )

    nome_excel = f"{caminho_arqvs}.xlsx"
    df_excel = df[Absenteismo.COLUNAS_PLANILHA]
    df_excel.to_excel(nome_excel, index=False, freeze_panes=(1, 0))

    nome_ppt = f"{caminho_arqvs}.pptx"

    nome_unidade = None
    if id_unidade:
        nome_unidade = Unidade.query.get(id_unidade).nome_unidade

    Absenteismo.criar_ppt(
        df=df,
        funcionarios_ativos=qtd_ativos,
        nome_arquivo=nome_ppt,
        nome_empresa=nome_empresa,
        nome_unidade=nome_unidade,
    )

    pasta_zip = zipar_arquivos(
        caminhos_arquivos=[nome_excel, nome_ppt],
        caminho_pasta_zip=f"{caminho_arqvs}.zip",
    )

    return send_from_directory(
        directory=UPLOAD_FOLDER, path="/", filename=os.path.basename(pasta_zip)
    )


def __get_nome_empresa(
    cod_emp_princ: int | None = None, id_empresa: int | None = None
) -> str:
    if id_empresa:
        return Empresa.query.get(id_empresa).razao_social
    elif cod_emp_princ:
        return EmpresaPrincipal.query.get(cod_emp_princ).nome
    else:
        raise ValueError("Parametros de query inválidos __get_nome_empresa")


def __get_qtd_ativos(
    cod_emp_princ: int | None = None,
    id_empresa: int | None = None,
    id_unidade: int | None = None,
) -> int:
    if id_unidade:
        f = Funcionario.id_unidade == id_unidade
    elif id_empresa:
        f = Funcionario.id_empresa == id_empresa
    elif cod_emp_princ:
        f = Funcionario.id_unidade == id_unidade
    else:
        raise ValueError("Parametros de query inválidos para __get_qtd_ativos")

    qtd_ativos = (
        db.session.query(Funcionario)  # type: ignore
        .filter(Funcionario.situacao == "Ativo")
        .filter(f)
        .count()
    )

    return qtd_ativos
