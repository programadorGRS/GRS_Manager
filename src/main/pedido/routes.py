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

from src import TIMEZONE_SAO_PAULO, UPLOAD_FOLDER, app
from src.email_connect import EmailConnect
from src.extensions import database as db
from src.extensions import mail
from src.utils import get_data_from_args, get_data_from_form

from ..empresa.empresa import Empresa
from ..pedido.pedido import Pedido
from ..prestador.prestador import Prestador
from ..status.status import Status
from ..status.status_lib import StatusLiberacao
from ..tipo_exame.tipo_exame import TipoExame
from .bulk_update import BulkUpdateHandler, DfValidationInfos
from .forms import (FormAtualizarStatus, FormBuscarASO, FormEnviarEmails,
                    FormPedidoBulkUpdate)

pedido_bp = Blueprint(
    name="pedido",
    import_name=__name__,
    url_prefix="/pedido",
    template_folder="templates",
    cli_group="pedido",
)


@pedido_bp.route("/buscar", methods=["GET", "POST"])
@login_required
def buscar_pedidos():
    form = FormBuscarASO()

    form.load_choices()

    if form.validate_on_submit():
        parametros = get_data_from_form(data=form.data)

        if "btn_buscar" in request.form:
            return redirect(url_for("pedido.atualizar_status", **parametros))

        elif "btn_emails" in request.form:
            return redirect(url_for("pedido.enviar_emails", **parametros))

        elif "btn_csv" in request.form:
            return redirect(url_for("pedido.pedidos_csv", **parametros))

    return render_template("pedido/buscar.html", form=form)


@pedido_bp.route("/atualizar-status", methods=["GET", "POST"])
@login_required
def atualizar_status():
    form = FormAtualizarStatus()

    form.load_choices()

    params = get_data_from_args(prev_form=FormBuscarASO(), data=request.args)

    id_grupos = params.get("id_grupos")
    if id_grupos:
        params["id_grupos"] = Pedido.handle_group_choice(choice=id_grupos)

    query = Pedido.buscar_pedidos(**params)

    total = Pedido.get_total_busca(query=query)

    if form.validate_on_submit():
        lista_atualizar = request.form.getlist("checkItem", type=int)

        update_values = __get_update_vals(form_data=form.data)
        update_values["data_alteracao"] = datetime.now(TIMEZONE_SAO_PAULO)
        update_values["alterado_por"] = current_user.username  # type: ignore

        df = __get_update_df(id_fichas=lista_atualizar, update_vals=update_values)
        df = __handle_status_lib_col(
            df=df, id_status_aso=int(update_values["id_status"])
        )

        df = __tto_final_df_update(df=df)

        df_mappings = df.to_dict(orient="records")

        try:
            db.session.bulk_update_mappings(Pedido, df_mappings)  # type: ignore
            db.session.commit()  # type: ignore
        except (SQLAlchemyError, DatabaseError) as e:
            db.session.rollback()  # type: ignore
            app.logger.error(msg=e, exc_info=True)
            flash("Erro interno ao atualizar Status", "alert-danger")

        flash(
            f"Status atualizados com sucesso! Qtd: {len(df_mappings)}",
            "alert-success",
        )
        return redirect(url_for("pedido.buscar_pedidos"))

    return render_template(
        "pedido/atualizar_status.html", form=form, query=query, total=total
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
    query = db.session.query(Pedido.id_ficha, Pedido.prev_liberacao).filter(  # type: ignore
        Pedido.id_ficha.in_(id_fichas)
    )
    df = pd.read_sql(sql=query.statement, con=db.session.bind)  # type: ignore

    # add update cols from the update_vals dict
    for key, val in update_vals.items():
        val = update_vals.get(key)
        if val:
            df[key] = val

    return df


def __handle_status_lib_col(df: pd.DataFrame, id_status_aso: int):
    """Calcula id_status_lib de acordo com o status ASO selecionado"""
    # status aso que finalizam processo
    query_fin_proc = db.session.query(Status.id_status).filter(  # type: ignore
        Status.finaliza_processo == True  # noqa
    )
    list_fin_proc: list[int] = [stt.id_status for stt in query_fin_proc]

    if id_status_aso in (list_fin_proc):
        # se status aso filaniza processo: setar todas tags para OK
        STT_LIB_OK = StatusLiberacao.get_id_status_ok()
        df["id_status_lib"] = STT_LIB_OK
    else:
        # se não: calcular cada tag baseado na prev liberacao de cada pedido
        df["id_status_lib"] = list(
            map(Pedido.calcular_tag_prev_lib, df["prev_liberacao"])
        )

    return df


def __tto_final_df_update(df: pd.DataFrame):
    """Selects correct cols and casts to proper data type. Drops unwanted cols"""
    df = df.copy()

    COL_TYPES: dict[str, type] = {
        "id_ficha": int,
        "id_status": int,
        "id_status_rac": int,
        "id_status_lib": int,
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


@pedido_bp.route("/enviar-emails", methods=["GET", "POST"])
@login_required
def enviar_emails():
    form = FormEnviarEmails()

    params = get_data_from_args(prev_form=FormBuscarASO(), data=request.args)

    id_grupos = params.get("id_grupos")
    if id_grupos:
        params["id_grupos"] = Pedido.handle_group_choice(choice=id_grupos)

    query = Pedido.buscar_pedidos(**params)

    total = Pedido.get_total_busca(query=query)

    if form.validate_on_submit():
        lista_enviar = request.form.getlist("checkItem", type=int)

        if not lista_enviar:
            flash("Nenhum Pedido selecionado", "alert-info")
            return redirect(url_for("pedido.buscar_pedidos"))

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
                    print('EMAIL ENVIADO COM SUCESSO')
                except Exception as e:
                    app.logger.error(msg=e, exc_info=True)
                    flash("Erro interno ao gerar email", "alert-danger")
                    return redirect(url_for("pedido.buscar_pedidos"))

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

        return redirect(url_for("pedido.buscar_pedidos"))

    # NOTE: val_email_prest = bloquear selecao de pedidos onde a solicitacao
    # de aso esteja desativada ou o prestador não possua email

    return render_template(
        "pedido/enviar_emails.html",
        form=form,
        query=query,
        total=total,
        val_email_prest=True,
    )


def __get_df_enviar_emails(id_fichas: list[int]):
    query = (
        db.session.query(  # type: ignore
            Pedido.seq_ficha,
            Pedido.cpf,
            Pedido.nome_funcionario,
            Pedido.data_ficha,
            TipoExame.nome_tipo_exame,
            Prestador.id_prestador,
            Prestador.nome_prestador,
            Prestador.emails,
            Prestador.solicitar_asos,
            Empresa.razao_social,
            StatusLiberacao.nome_status_lib,
        )
        .outerjoin(Prestador, Empresa, TipoExame, StatusLiberacao)
        .filter(Pedido.id_ficha.in_(id_fichas))
        .filter(Pedido.id_prestador != None)  # noqa
    )

    df = pd.read_sql(sql=query.statement, con=db.session.bind)  # type: ignore
    df = df.replace({np.nan: None, "": None})

    return df


def __tto_df_pedidos_email(df: pd.DataFrame):
    df_pedidos = df[list(Pedido.COLS_EMAIL.keys())]
    df_pedidos = df_pedidos.rename(columns=Pedido.COLS_EMAIL)

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

    #email_prest = 'hideki@quaestum.com.br, aso.manager@grsnucleo.com.br, thiagoikehara@gmail.com'
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


@pedido_bp.route("/buscar/csv", methods=["GET", "POST"])
@login_required
def pedidos_csv():
    params = get_data_from_args(prev_form=FormBuscarASO(), data=request.args)

    id_grupos = params.get("id_grupos")
    if id_grupos:
        params["id_grupos"] = Pedido.handle_group_choice(choice=id_grupos)

    query = Pedido.buscar_pedidos(**params)
    query = Pedido.add_csv_cols(query=query)

    df = pd.read_sql(sql=query.statement, con=db.session.bind)  # type: ignore

    df = df[Pedido.COLS_CSV]

    df['prontuario_conferido'] = df['prontuario_conferido'].replace({0: 'Não', 1: 'Sim'})

    timestamp = int(datetime.now().timestamp())
    nome_arqv = f"Pedidos_exames_{timestamp}"
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


@pedido_bp.route("/<int:id_ficha>", methods=["GET", "POST"])
@login_required
def editar_pedido(id_ficha: int):
    pedido: Pedido = Pedido.query.get(id_ficha)

    if not pedido:
        return abort(404)

    form = FormAtualizarStatus(
        status_aso=pedido.id_status,
        status_rac=pedido.id_status_rac,
        data_recebido=pedido.data_recebido,
        data_comparecimento=pedido.data_comparecimento,
        obs=pedido.obs,
        prontuario_conferido=pedido.prontuario_conferido,
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

        stt_rac = form.status_rac.data
        pedido.id_status_rac = int(stt_rac) if stt_rac else 1

        Pedido.set_id_status(
            id_ficha=id_ficha, id_status=int(form.status_aso.data)  # type: ignore
        )

        pedido.prontuario_conferido = form.prontuario_conferido.data

        pedido.data_alteracao = datetime.now(TIMEZONE_SAO_PAULO)
        pedido.alterado_por = current_user.username  # type: ignore
        db.session.commit()  # type: ignore

        flash("Pedido atualizado com sucesso!", "alert-success")
        return redirect(url_for("pedido.editar_pedido", id_ficha=id_ficha))

    return render_template("pedido/editar.html", form=form, pedido=pedido)


@pedido_bp.route("/bulk-update", methods=["GET", "POST"])
@login_required
def bulk_update_pedidos():
    form = FormPedidoBulkUpdate()

    lista_status: list[Status] = db.session.query(  # type: ignore
        Status.id_status, Status.nome_status
    ).all()

    if form.validate_on_submit():
        # ler arquivo
        arqv = request.files["csv"]
        data = arqv.read().decode()

        # tamanho maximo
        max_size_mb = app.config["MAX_UPLOAD_SIZE_MB"]
        max_bytes = max_size_mb * 1024 * 1024

        if getsizeof(data) > max_bytes:
            flash(f"O arquivo deve ser menor que {max_size_mb} MB", "alert-danger")
            return redirect(url_for("pedido.bulk_update_pedidos"))

        # ler string como objeto para csv
        df_base: pd.DataFrame = pd.read_csv(
            filepath_or_buffer=StringIO(data),
            sep=";",
        )

        handler = BulkUpdateHandler()

        res = handler.handle_df_columns(
            df=df_base,
            required_cols=list(handler.REQUIRED_COLS.keys()),
            allowed_cols=list(handler.ALLOWED_COLS.keys()),
        )
        if not res.ok:
            return __stop_update_proc(res=res)

        df = res.df

        res = handler.cast_df_col_types(
            df=df, cols=dict(**handler.REQUIRED_COLS, **handler.ALLOWED_COLS)
        )
        if not res.ok:
            return __stop_update_proc(res=res)

        df = res.df
        df = df.drop_duplicates(subset="id_ficha", ignore_index=True)

        res = handler.handle_enum_col(df=df, col_name="id_status", table=Status)
        if not res.ok:
            return __stop_update_proc(res=res)

        df = res.df

        res = handler.handle_id_ficha(df=df)
        if not res.ok:
            return __stop_update_proc(res=res)

        df = res.df

        df = handler.handle_status_lib(df=df)

        df["data_alteracao"] = datetime.now(tz=TIMEZONE_SAO_PAULO)
        df["alterado_por"] = current_user.username  # type: ignore

        df_final = handler.tto_final_bulk_update(df=df)

        df_mappings = df_final.to_dict(orient="records")

        try:
            db.session.bulk_update_mappings(Pedido, df_mappings)  # type: ignore
            db.session.commit()  # type: ignore
        except (SQLAlchemyError, DatabaseError) as e:
            db.session.rollback()  # type: ignore
            app.logger.error(msg=e, exc_info=True)
            flash("Erro interno ao atualizar o Banco de Dados", "alert-danger")
            return redirect(url_for("pedido.bulk_update_pedidos"))

        flash(
            "Pedidos atualizados com sucesso! | " f"Total: {len(df_mappings)}",
            "alert-success",
        )

        return redirect(url_for("pedido.bulk_update_pedidos"))

    return render_template(
        "pedido/bulk_update.html",
        form=form,
        lista_status=lista_status,
    )


def __stop_update_proc(res: DfValidationInfos):
    if res.msgs:
        for msg, cat_msg in res.msgs:
            flash(msg, cat_msg)
    return redirect(url_for("pedido.bulk_update_pedidos"))
