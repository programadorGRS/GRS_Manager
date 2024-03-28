import os
from io import BytesIO

import pandas as pd
from flask import (Blueprint, flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import login_required
from sqlalchemy import delete
from werkzeug.datastructures import FileStorage

from src import UPLOAD_FOLDER, app
from src.extensions import database as db
from src.utils import (get_data_from_args, get_data_from_form,
                       get_image_file_as_base64_data,
                       validate_upload_file_size)

from ..empresa_principal.empresa_principal import EmpresaPrincipal
from ..pedido.pedido import Pedido
from ..qrcode.qrcode_rtc import QrCodeRtc
from .exceptions import RTCGeneratioError, RTCValidationError
from .forms import FormBuscarRTC, FormGerarRTC, FormUploadCSV
from .gerar_rtc import GerarRTC
from .models import RTC, RTCCargos

rtc = Blueprint(
    name="rtc",
    import_name=__name__,
    url_prefix="/rtc",
    template_folder="templates",
)


MODELOS_RTC = os.path.join(rtc.root_path, rtc.template_folder, "rtc", "modelos")  # type: ignore
RTC_DEFAULT = os.path.join(rtc.root_path, rtc.template_folder, "rtc", "modelos", "rtc_default.html")  # type: ignore
RTCREGRASVIDA_DEFAULT = os.path.join(rtc.root_path, rtc.template_folder, "rtc", "modelos", "rtc_regrasvida.html")  # type: ignore

LOGOS_EMPRESAS = os.path.join(app.static_folder, "logos", "empresas")  # type: ignore
LOGO_DEFAULT = os.path.join(LOGOS_EMPRESAS, "grs.png")


@rtc.route("/buscar", methods=["GET", "POST"])
@login_required
def busca_rtc():
    form = FormBuscarRTC()
    form.load_choices()

    if form.validate_on_submit():
        parametros = get_data_from_form(data=form.data)
        return redirect(url_for("rtc.gerar_rtcs", **parametros))

    return render_template("rtc/buscar.html", form=form)


@rtc.route("/gerar", methods=["GET", "POST"])
@login_required
def gerar_rtcs():
    form: FormGerarRTC = FormGerarRTC()

    data = get_data_from_args(prev_form=FormBuscarRTC(), data=request.args)

    query = Pedido.buscar_pedidos(**data)

    total = Pedido.get_total_busca(query=query)
    #Ao clicar no botao de GERAR
    if form.validate_on_submit():
        gera_rtc = GerarRTC()

        lista_pdfs: list[str] = []
        erros = []

        for id_ficha in request.form.getlist("checkItem", type=int):
            try:
                infos = gera_rtc.get_infos_rtc(id_ficha)
            except RTCGeneratioError as err:
                pedido = Pedido.query.get(id_ficha)
                erros.append((pedido, err.message))
                continue

            try:
                temp_body = __get_company_rtc_template(
                    temp_path=os.path.join(MODELOS_RTC, infos.empresa.modelo_rtc)
                )
                print(RTCREGRASVIDA_DEFAULT)
                temp_bodyRegrasVida = __get_company_rtc_template(temp_path=RTCREGRASVIDA_DEFAULT)                
            except (FileNotFoundError, TypeError):
                temp_body = __get_company_rtc_template(temp_path=RTC_DEFAULT)

            try:
                logo_data = __get_company_logo(
                    logo_path=os.path.join(LOGOS_EMPRESAS, infos.empresa.logo)
                )
            except (FileNotFoundError, TypeError):
                logo_data = __get_company_logo(logo_path=LOGO_DEFAULT)

            qr_code = None
            if form.gerar_qrcode.data:
                qr_code = __get_qrcode(id_ficha=infos.pedido.id_ficha)

            html_str = gera_rtc.render_rtc_html(
                infos=infos,
                template_body=temp_body,
                logo_empresa=logo_data.decode() if logo_data else None,
                qr_code=qr_code.decode() if qr_code else None,
                render_tipo_sang=form.tipo_sang.data,
            )
            html_strRegrasVida = gera_rtc.render_rtc_htmlRegrasVida(
                infos=infos,
                template_body=temp_bodyRegrasVida,
                logo_empresa=logo_data.decode() if logo_data else None,
                qr_code=qr_code.decode() if qr_code else None,
                render_tipo_sang=form.tipo_sang.data,
            )

            file_path = gera_rtc.gerar_pdf(
                html=html_str,
                nome_funcionario=infos.funcionario.nome_funcionario,
                qtd_exames=len(infos.exames),
            )
            file_pathRegrasVida = gera_rtc.gerar_pdf(
                html=html_strRegrasVida,
                nome_funcionario=infos.funcionario.nome_funcionario,
                qtd_exames=len(infos.exames),
            )

            lista_pdfs.append(file_path)
            if form.regras_vida.data:
                lista_pdfs.append(file_pathRegrasVida)

        if erros:
            df_erros = gera_rtc.gerar_df_erros(erros=erros)
            csv = gera_rtc.gerar_csv_erros(df_erros=df_erros)
            lista_pdfs.append(csv)

        nome_zip = gera_rtc.gerar_zip(arquivos=lista_pdfs)


        
        return send_from_directory(directory=UPLOAD_FOLDER, path="/", filename=nome_zip)

    return render_template(
        "rtc/gerar_rtcs.html",
        page_title="Gerar RTCs",
        query=query,
        total=total,
        form=form,
    )


def __get_company_logo(logo_path: str):
    with open(logo_path, "rb") as f:
        logo_data = f.read()
    return get_image_file_as_base64_data(img_data=logo_data)


def __get_company_rtc_template(temp_path: str):
    with open(temp_path, "rt", encoding="utf-8") as f:
        return f.read()


def __get_qrcode(id_ficha: int):
    qr = QrCodeRtc()
    data = qr.generate_qrcode_data_str(id_ficha=id_ficha)
    qrcode_data = qr.generate_qr_code(data=data)
    return get_image_file_as_base64_data(img_data=qrcode_data)


@rtc.route("/importar-dados", methods=["GET", "POST"])
@login_required
def importar_dados_rtc():
    form: FormUploadCSV = FormUploadCSV()

    form.cod_emp_princ.choices = [("", "Selecione")] + [
        (emp.cod, emp.nome) for emp in EmpresaPrincipal.query.all()
    ]

    if form.validate_on_submit():
        df = __get_df_from_form(form=form)

        if df is None:
            return redirect(url_for("rtc.importar_dados"))

        try:
            __handle_choice_tabela(form=form, df=df)
        except RTCValidationError as err:
            flash(f"Erro: {err.message}", "alert-danger")

        return redirect(url_for("rtc.importar_dados"))

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
    sep = form.SEP.get(int(form.file_sep.data))  # type: ignore
    enc = form.ENCODING.get(int(form.file_sep.data))  # type: ignore

    df = pd.read_csv(BytesIO(data), sep=sep, encoding=enc)

    if df.empty:
        flash("Tabela vazia", "alert-info")
        return None

    return df


def __handle_choice_tabela(form: FormUploadCSV, df: pd.DataFrame):
    choice = int(form.tabela.data)  # type: ignore
    emp_princ = int(form.cod_emp_princ.data)  # type: ignore

    match choice:
        case 1:
            __atualizar_cargos(cod_emp_princ=emp_princ, df=df)

    return None


def __atualizar_cargos(cod_emp_princ: int, df: pd.DataFrame):
    df = RTC.tratar_df_rtc_cargos(cod_emp_princ=int(cod_emp_princ), df=df)

    db.session.execute(delete(RTCCargos))  # type: ignore
    db.session.commit()  # type: ignore

    df = df[["cod_cargo", "id_rtc"]]

    qtd = df.to_sql(
        name="RTCCargos",
        con=db.session.bind,  # type: ignore
        if_exists="append",
        index=False,
    )
    db.session.commit()  # type: ignore

    flash(
        f"Tabela RTC X Cargos atualizada com sucesso! Linhas afetadas: {qtd}",
        "alert-success",
    )

    return None
