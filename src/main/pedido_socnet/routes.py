import os
from datetime import date, datetime
from io import StringIO
from sys import getsizeof
from typing import Any

import numpy as np
import pandas as pd
from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required
from flask_mail import Attachment, Message
from sqlalchemy.exc import DatabaseError, SQLAlchemyError
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from src import DOWNLOAD_FOLDER, TIMEZONE_SAO_PAULO, UPLOAD_FOLDER, app
from src.email_connect import EmailConnect
from src.extensions import database as db
from src.extensions import mail
from src.utils import get_data_from_args, get_data_from_form

from ..empresa_socnet.empresa_socnet import EmpresaSOCNET
from ..pedido_socnet.pedido_socnet import PedidoSOCNET
from ..prestador.prestador import Prestador
from ..tipo_exame.tipo_exame import TipoExame
from .forms import (FormAtualizarStatusSOCNET, FormBuscarASOSOCNET,
                    FormCarregarPedidosSOCNET, FormEnviarEmailsSOCNET,
                    FormUpload)

pedido_socnet_bp = Blueprint(
    name="pedido-socnet",
    import_name=__name__,
    url_prefix="/pedido-socnet",
    template_folder="templates",
    cli_group="pedido-socnet",
)


@pedido_socnet_bp.route("/buscar", methods=["GET", "POST"])
@login_required
def buscar_pedidos():
    form = FormBuscarASOSOCNET()

    form.load_choices()

    if form.validate_on_submit():
        parametros = get_data_from_form(data=form.data)

        if "btn_buscar" in request.form:
            return redirect(url_for("pedido-socnet.atualizar_status", **parametros))

        elif "btn_emails" in request.form:
            return redirect(url_for("pedido-socnet.enviar_emails", **parametros))

        elif "btn_csv" in request.form:
            return redirect(url_for("pedido-socnet.pedidos_csv", **parametros))

    return render_template("pedido_socnet/buscar.html", form=form)


@pedido_socnet_bp.route("/atualizar-status", methods=["GET", "POST"])
@login_required
def atualizar_status():
    form = FormAtualizarStatusSOCNET()

    form.load_choices()

    params = get_data_from_args(prev_form=FormBuscarASOSOCNET(), data=request.args)

    id_grupos = params.get("id_grupos")
    if id_grupos:
        params["id_grupos"] = PedidoSOCNET.handle_group_choice(choice=id_grupos)

    query = PedidoSOCNET.buscar_pedidos(**params)

    total = PedidoSOCNET.get_total_busca(query=query)

    if form.validate_on_submit():
        lista_atualizar = request.form.getlist("checkItem", type=int)

        update_values = __get_update_vals(form_data=form.data)
        update_values["data_alteracao"] = datetime.now(TIMEZONE_SAO_PAULO)
        update_values["alterado_por"] = current_user.username  # type: ignore

        df = __get_update_df(id_fichas=lista_atualizar, update_vals=update_values)

        df = __tto_final_df_update(df=df)

        df_mappings = df.to_dict(orient="records")

        try:
            db.session.bulk_update_mappings(PedidoSOCNET, df_mappings)  # type: ignore
            db.session.commit()  # type: ignore
        except (SQLAlchemyError, DatabaseError) as e:
            db.session.rollback()  # type: ignore
            app.logger.error(msg=e, exc_info=True)
            flash("Erro interno ao atualizar Status", "alert-danger")

        flash(
            f"Status atualizados com sucesso! Qtd: {len(df_mappings)}",
            "alert-success",
        )
        return redirect(url_for("pedido-socnet.buscar_pedidos"))

    return render_template(
        "pedido_socnet/atualizar_status.html", form=form, query=query, total=total
    )


def __get_update_vals(form_data: dict[str, Any]) -> dict[str, Any]:
    # (coluna tabela, campo formulario, default val)
    CAMPOS = (
        ("id_status", "status_aso", None),
        ("id_status_rac", "status_rac", 1),
        ("data_recebido", "data_recebido", None),
        ("data_comparecimento", "data_comparecimento", None),
        ("obs", "obs", None),
    )

    update_data = {}
    for db_col, form_field, deft_val in CAMPOS:
        field_data = form_data.get(form_field)
        if field_data:
            update_data[db_col] = field_data
        else:
            update_data[db_col] = deft_val

    return update_data


def __get_update_df(id_fichas: list[int], update_vals: dict[str, Any]):
    """Queries id_ficha and adds non empty cols to dataframe"""
    query = db.session.query(PedidoSOCNET.id_ficha).filter(  # type: ignore
        PedidoSOCNET.id_ficha.in_(id_fichas)
    )
    df = pd.read_sql(sql=query.statement, con=db.session.bind)  # type: ignore

    # add update cols from the update_vals dict
    for key, val in update_vals.items():
        val = update_vals.get(key)
        if val:
            df[key] = val

    return df


def __tto_final_df_update(df: pd.DataFrame):
    """Selects correct cols and casts to proper data type. Drops unwanted cols"""
    df = df.copy()

    COL_TYPES: dict[str, type] = {
        "id_ficha": int,
        "id_status": int,
        "id_status_rac": int,
        "data_recebido": date,
        "data_comparecimento": date,
        "data_alteracao": datetime,
        "obs": str,
        "alterado_por": str,
    }

    for col in df.columns:
        if col not in COL_TYPES.keys():
            df = df.drop(columns=col)
        else:
            col_type = COL_TYPES[col].__name__
            match col_type:
                case "int":
                    df[col] = df[col].astype(int)
                case "date":
                    df[col] = pd.to_datetime(df[col], dayfirst=True).dt.date
                case "datetime":
                    df[col] = pd.to_datetime(df[col], dayfirst=True)

    return df


@pedido_socnet_bp.route("/enviar-emails", methods=["GET", "POST"])
@login_required
def enviar_emails():
    form = FormEnviarEmailsSOCNET()

    params = get_data_from_args(prev_form=FormBuscarASOSOCNET(), data=request.args)

    id_grupos = params.get("id_grupos")
    if id_grupos:
        params["id_grupos"] = PedidoSOCNET.handle_group_choice(choice=id_grupos)

    query = PedidoSOCNET.buscar_pedidos(**params)

    total = PedidoSOCNET.get_total_busca(query=query)

    if form.validate_on_submit():
        lista_enviar = request.form.getlist("checkItem", type=int)

        if not lista_enviar:
            flash("Nenhum Pedido selecionado", "alert-info")
            return redirect(url_for("pedido-socnet.buscar_pedidos"))

        df = __get_df_enviar_emails(id_fichas=lista_enviar)

        with mail.connect() as conn:
            qtd_envios = 0
            qtd_pedidos = 0
            nao_enviados = []
            erros_envio = []

            prestadores = df["id_prestador"].drop_duplicates().tolist()

            for id_prest in prestadores:
                df_pedidos_email: pd.DataFrame = df[df["id_prestador"] == id_prest]

                if df_pedidos_email.empty:
                    continue

                nome_prest: str = df_pedidos_email["nome_prestador"].values[0]
                emails_prest: str = df_pedidos_email["emails"].values[0]
                sol_aso: bool = df_pedidos_email["solicitar_asos"].values[0]

                if not emails_prest or not sol_aso:
                    nao_enviados.append(nome_prest)
                    continue

                df_pedidos_email = __tto_df_pedidos_email(df=df_pedidos_email)

                try:
                    msg = __handle_email_msg(
                        df_pedidos=df_pedidos_email,
                        nome_prest=nome_prest,
                        email_prest=emails_prest,
                        obs=form.obs_email.data,
                        assunto_email=form.assunto_email.data,
                        email_copia=form.email_copia.data,
                    )
                except Exception as e:
                    app.logger.error(msg=e, exc_info=True)
                    flash("Erro interno ao gerar email", "alert-danger")
                    return redirect(url_for("pedido-socnet.buscar_pedidos"))

                try:
                    conn.send(msg)
                    qtd_envios += 1
                    qtd_pedidos += len(df_pedidos_email)
                except Exception as e:
                    app.logger.error(msg=e, exc_info=True)
                    erros_envio.append(nome_prest)

        if qtd_envios:
            flash(
                "Emails enviados com sucesso! "
                f"Qtd Emails: {qtd_envios} Qtd Pedidos: {qtd_pedidos}",
                "alert-success",
            )

        if nao_enviados:
            flash(f"Não enviados: {'; '.join(nao_enviados)}", "alert-warning")

        if erros_envio:
            erros_envio = "; ".join(erros_envio)
            flash(f"Erros: {erros_envio}", "alert-danger")

        return redirect(url_for("pedido-socnet.buscar_pedidos"))

    # NOTE: val_email_prest = bloquear selecao de pedidos onde a solicitacao
    # de aso esteja desativada ou o prestador não possua email

    return render_template(
        "pedido_socnet/enviar_emails.html",
        form=form,
        query=query,
        total=total,
        val_email_prest=True,
    )


def __get_df_enviar_emails(id_fichas: list[int]):
    query = (
        db.session.query(  # type: ignore
            PedidoSOCNET.seq_ficha,
            PedidoSOCNET.cpf,
            PedidoSOCNET.nome_funcionario,
            PedidoSOCNET.data_ficha,
            TipoExame.nome_tipo_exame,
            Prestador.id_prestador,
            Prestador.nome_prestador,
            Prestador.emails,
            Prestador.solicitar_asos,
            EmpresaSOCNET.nome_empresa,
        )
        .outerjoin(Prestador, EmpresaSOCNET, TipoExame)
        .filter(PedidoSOCNET.id_ficha.in_(id_fichas))
        .filter(PedidoSOCNET.id_prestador != None)  # noqa
    )

    df = pd.read_sql(sql=query.statement, con=db.session.bind)  # type: ignore
    df = df.replace({np.nan: None, "": None})

    return df


def __tto_df_pedidos_email(df: pd.DataFrame):
    df_pedidos = df[list(PedidoSOCNET.COLS_EMAIL.keys())]
    df_pedidos = df_pedidos.rename(columns=PedidoSOCNET.COLS_EMAIL)

    df_pedidos["Data Ficha"] = pd.to_datetime(df_pedidos["Data Ficha"])
    df_pedidos["Data Ficha"] = df_pedidos["Data Ficha"].dt.strftime("%d/%m/%Y")

    return df_pedidos


def __handle_email_msg(
    df_pedidos: pd.DataFrame,
    nome_prest: str,
    email_prest: str,
    obs: str | None = None,
    assunto_email: str | None = None,
    email_copia: str | None = None,
):
    if not obs:
        obs = "Sinalizar se o funcionário não compareceu."

    em_temp_pth = os.path.join("src", "email_templates", "email_aso.html")

    body = EmailConnect.create_email_body(
        email_template_path=em_temp_pth,
        replacements={
            "DATAFRAME_ASO": df_pedidos.to_html(index=False),
            "USER_OBS": obs,
            "USER_NAME": current_user.nome_usuario,  # type: ignore
            "USER_EMAIL": current_user.email,  # type: ignore
            "USER_TEL": current_user.telefone,  # type: ignore
            "USER_CEL": current_user.celular,  # type: ignore
        },
    )

    email_prest = email_prest.replace(" ", "").replace(",", ";")
    list_email_prest = email_prest.split(";")

    if assunto_email:
        assunto_email = f"{assunto_email} - {nome_prest}"
    else:
        assunto_email = f"ASO GRS - {nome_prest}"

    emails_cc = [current_user.email]  # type: ignore
    if email_copia:
        email_copia = email_copia.replace(",", ";")
        emails_cc.extend(email_copia.split(";"))

    ass_pth: str = EmailConnect.ASSINATURA_BOT["img_path"]
    ass_data = app.open_resource(ass_pth).read()
    ass_att = Attachment(
        filename=ass_pth,
        data=ass_data,
        content_type="image/png",
        disposition="inline",
        headers=[["Content-ID", "<AssEmail>"]],
    )

    msg = Message(
        recipients=list_email_prest,
        cc=emails_cc,
        subject=assunto_email,
        html=body,
        attachments=[ass_att],
        reply_to=current_user.email,  # type: ignore
    )

    return msg


@pedido_socnet_bp.route("/buscar/csv", methods=["GET", "POST"])
@login_required
def pedidos_csv():
    params = get_data_from_args(prev_form=FormBuscarASOSOCNET(), data=request.args)

    id_grupos = params.get("id_grupos")
    if id_grupos:
        params["id_grupos"] = PedidoSOCNET.handle_group_choice(choice=id_grupos)

    query = PedidoSOCNET.buscar_pedidos(**params)
    query = PedidoSOCNET.add_csv_cols(query=query)

    df = pd.read_sql(sql=query.statement, con=db.session.bind)  # type: ignore

    df = df[PedidoSOCNET.COLS_CSV]

    timestamp = int(datetime.now().timestamp())
    nome_arqv = f"Pedidos_SOCNET_{timestamp}"
    camihno_arqv = os.path.join(UPLOAD_FOLDER, nome_arqv)

    df.to_csv(
        f"{camihno_arqv}.zip",
        sep=";",
        index=False,
        encoding="iso-8859-1",
        compression={"method": "zip", "archive_name": f"{nome_arqv}.csv"},
    )

    return send_from_directory(
        directory=UPLOAD_FOLDER, path="/", filename=f"{nome_arqv}.zip"
    )


@pedido_socnet_bp.route("/<int:id_ficha>", methods=["GET", "POST"])
@login_required
def editar_pedido(id_ficha: int):
    pedido: PedidoSOCNET = PedidoSOCNET.query.get(id_ficha)

    if not pedido:
        return abort(404)

    form = FormAtualizarStatusSOCNET(
        status_aso=pedido.id_status,
        status_rac=pedido.id_status_rac,
        data_recebido=pedido.data_recebido,
        data_comparecimento=pedido.data_comparecimento,
        obs=pedido.obs,
    )

    form.load_choices()

    if form.validate_on_submit():
        CAMPOS = (
            "data_recebido",
            "data_comparecimento",
            "obs",
        )

        for form_field in CAMPOS:
            field_data = form.data.get(form_field)
            if field_data:
                setattr(pedido, form_field, field_data)
            else:
                setattr(pedido, form_field, None)

        stt_aso = form.status_aso.data
        pedido.id_status = int(stt_aso) if stt_aso else 1

        stt_rac = form.status_rac.data
        pedido.id_status_rac = int(stt_rac) if stt_rac else 1

        pedido.data_alteracao = datetime.now(TIMEZONE_SAO_PAULO)
        pedido.alterado_por = current_user.username  # type: ignore
        db.session.commit()  # type: ignore

        flash("Pedido atualizado com sucesso!", "alert-success")
        return redirect(url_for("pedido-socnet.editar_pedido", id_ficha=id_ficha))

    return render_template("pedido_socnet/editar.html", form=form, pedido=pedido)


@pedido_socnet_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_csv():
    form = FormUpload()

    if form.validate_on_submit():
        arqv: FileStorage = request.files["csv"]
        data = arqv.read().decode()

        if not data:
            flash("Arquivo vazio", "alert-info")
            return redirect(url_for("pedido-socnet.upload_csv"))

        # tamanho maximo
        max_size_mb = app.config["MAX_UPLOAD_SIZE_MB"]
        max_bytes = max_size_mb * 1024 * 1024

        if getsizeof(data) > max_bytes:
            flash(f"O arquivo deve ser menor que {max_size_mb} MB", "alert-danger")
            return redirect(url_for("pedido-socnet.upload_csv"))

        try:
            __handle_new_file(file_data=data, file_name=arqv.filename)  # type: ignore
            flash("Arquivo importado com sucesso!", "alert-success")
            flash(
                "Agora selecione o arquivo para carregar no banco de dados",
                "alert-info",
            )
            return redirect(url_for("pedido-socnet.carregar_pedidos_socnet"))
        except KeyError:
            # raise error se o arquivo for incompativel
            # (faltar colunas ou nao der pra processar etc)
            flash(
                "O arquivo não contém as colunas ou cabeçalho necessários!",
                "alert-danger",
            )
            return redirect(url_for("pedido-socnet.upload_csv"))
        except Exception as e:
            app.logger.error(msg=e, exc_info=True)
            flash("Erro interno ao processar arquivo", "alert-danger")
            return redirect(url_for("pedido-socnet.upload_csv"))

    return render_template("pedido_socnet/upload_csv.html", form=form)


def __handle_new_file(file_data: Any, file_name: str):
    """criar novo arquivo com os dados recebidos"""
    filename = secure_filename(filename=file_name)
    timestamp = int(datetime.now().timestamp())
    new_filename = f"{filename.split('.')[0]}_{timestamp}.csv"
    new_file_path = os.path.join(DOWNLOAD_FOLDER, new_filename)

    df = pd.read_csv(filepath_or_buffer=StringIO(file_data), header=2, sep=";")
    df = PedidoSOCNET.tratar_df_socnet(df=df)
    df = PedidoSOCNET.filtrar_empresas(df=df)
    df.to_csv(new_file_path, index=False, sep=";", encoding="iso-8859-1")
    return new_file_path


@pedido_socnet_bp.route("/carregar", methods=["GET", "POST"])
@login_required
def carregar_pedidos_socnet():
    form = FormCarregarPedidosSOCNET()
    form.get_file_choices(folder=DOWNLOAD_FOLDER)

    if form.validate_on_submit():
        try:
            path = os.path.join(DOWNLOAD_FOLDER, form.arquivos.data)  # type: ignore
            df = pd.read_csv(path, sep=";", encoding="iso-8859-1")
        except Exception as err:
            app.logger.error(msg=err, exc_info=True)
            flash("Erro interno ao ler o arquivo", "alert-danger")
            return redirect(url_for("pedido-socnet.carregar_pedidos_socnet"))

        try:
            qtd = PedidoSOCNET.inserir_pedidos(df=df)
            if qtd:
                flash(f"Pedidos carregados com sucesso! | Qtd: {qtd}", "alert-success")
            else:
                flash("Nenhum Pedido novo encontrado na planilha", "alert-info")
        except (SQLAlchemyError, DatabaseError) as err:
            db.session.rollback()  # type: ignore
            app.logger.error(msg=err, exc_info=True)
            flash("Erro interno ao inserir no banco de dados", "alert-danger")
        finally:
            os.remove(path=path)

        return redirect(url_for("pedido-socnet.carregar_pedidos_socnet"))

    return render_template("pedido_socnet/carregar_csv.html", form=form)
