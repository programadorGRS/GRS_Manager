from io import BytesIO

import pandas as pd
from flask import (flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import login_required
from sqlalchemy import delete
from werkzeug.datastructures import FileStorage

from src import UPLOAD_FOLDER, app
from src.extensions import database
from src.main.pedido.forms import FormBuscarASO
from src.main.pedido.pedido import Pedido
from src.utils import (get_data_from_args, get_data_from_form,
                       validate_upload_file_size)

from ..empresa_principal.empresa_principal import EmpresaPrincipal
from .exceptions import RTCGeneratioError, RTCValidationError
from .forms import FormGerarRTC, FormUploadCSV
from .models import RTC, RTCCargos


@app.route("/rtc/buscar", methods=["GET", "POST"])
@login_required
def busca_rtc():
    form = FormBuscarASO()
    form.load_choices()

    if form.validate_on_submit():
        parametros = get_data_from_form(data=form.data, ignore_keys=["pesquisa_geral"])
        return redirect(url_for("gerar_rtcs", **parametros))

    return render_template("rtc/busca.html", form=form)


@app.route("/rtc/gerar", methods=["GET", "POST"])
@login_required
def gerar_rtcs():
    form: FormGerarRTC = FormGerarRTC()

    data = get_data_from_args(prev_form=FormBuscarASO(), data=request.args)

    id_grupos = data.get("id_grupos")
    if id_grupos is not None:
        data["id_grupos"] = Pedido.handle_group_choice(choice=id_grupos)

    query = Pedido.buscar_pedidos(**data)

    total = Pedido.get_total_busca(query=query)

    if form.validate_on_submit():
        lista_pdfs: list[str] = []
        erros = []
        for id_ficha in request.form.getlist("checkItem", type=int):
            try:
                infos_ficha = RTC.buscar_infos_rtc(id_ficha)
            except RTCGeneratioError as err:
                pedido = Pedido.query.get(id_ficha)
                erros.append((pedido, err.message))
                continue

            html_str = RTC.render_rtc_html(
                infos=infos_ficha,
                logo_empresa=RTC.LOGO_MANSERV,
                logo_width=RTC.LOGO_MANSERV_WIDTH,
                logo_height=RTC.LOGO_MANSERV_HEIGHT,
                render_tipo_sang=form.tipo_sang.data,
            )

            file_path = RTC.gerar_pdf(infos=infos_ficha, html=html_str)

            lista_pdfs.append(file_path)

        if erros:
            df_erros = RTC.gerar_df_erros(erros=erros)
            csv = RTC.gerar_csv_erros(df_erros=df_erros)
            lista_pdfs.append(csv)

        nome_zip = RTC.gerar_zip(arquivos=lista_pdfs)

        return send_from_directory(directory=UPLOAD_FOLDER, path="/", filename=nome_zip)

    return render_template(
        "rtc/gerar_rtcs.html",
        page_title="Gerar RTCs",
        query=query,
        total=total,
        form=form,
    )


@app.route("/rtc/importar-dados", methods=["GET", "POST"])
@login_required
def importar_dados_rtc():
    form: FormUploadCSV = FormUploadCSV()

    form.cod_emp_princ.choices = [("", "Selecione")] + [
        (emp.cod, emp.nome) for emp in EmpresaPrincipal.query.all()
    ]

    if form.validate_on_submit():
        df = __get_df_from_form(form=form)

        if df is None:
            return redirect(url_for("importar_dados"))

        try:
            __handle_choice_tabela(form=form, df=df)
        except RTCValidationError as err:
            flash(f"Erro: {err.message}", "alert-danger")

        return redirect(url_for("importar_dados"))

    return render_template(
        "rtc/upload.html", page_title="Importar Dados RTC", form=form
    )


def __get_df_from_form(form: FormUploadCSV):
    file_storage: FileStorage = form.csv_file.data
    data: bytes = file_storage.read()

    # validate size of data
    validated = validate_upload_file_size(file_data=data)
    max_size = app.config["MAX_UPLOAD_SIZE_MB"]

    if not validated:
        flash(f"O arquivo deve ser menor que {max_size} MB", "alert-info")
        return None

    # read dataframe
    sep = form.SEP.get(int(form.file_sep.data))
    enc = form.ENCODING.get(int(form.file_sep.data))

    df = pd.read_csv(BytesIO(data), sep=sep, encoding=enc)

    if df.empty:
        flash("Tabela vazia", "alert-info")
        return None

    return df


def __handle_choice_tabela(form: FormUploadCSV, df: pd.DataFrame):
    choice = int(form.tabela.data)
    emp_princ = int(form.cod_emp_princ.data)

    match choice:
        case 1:
            __atualizar_cargos(cod_emp_princ=emp_princ, df=df)

    return None


def __atualizar_cargos(cod_emp_princ: int, df: pd.DataFrame):
    df: pd.DataFrame = RTC.tratar_df_rtc_cargos(cod_emp_princ=int(cod_emp_princ), df=df)

    database.session.execute(delete(RTCCargos))
    database.session.commit()

    df = df[["cod_cargo", "id_rtc"]]

    qtd = df.to_sql(
        name="RTCCargos", con=database.session.bind, if_exists="append", index=False
    )
    database.session.commit()

    flash(
        f"Tabela RTC X Cargos atualizada com sucesso! Linhas afetadas: {qtd}",
        "alert-success",
    )

    return None
