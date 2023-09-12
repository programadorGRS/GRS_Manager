import os
from datetime import datetime
from io import StringIO
from sys import getsizeof
from typing import Any

import numpy as np
import pandas as pd
from flask import (Blueprint, flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required
from sqlalchemy.exc import DatabaseError, SQLAlchemyError

from src import TIMEZONE_SAO_PAULO, UPLOAD_FOLDER, app
from src.extensions import database as db
from src.utils import admin_required, tratar_emails, zipar_arquivos

from ..empresa.empresa import Empresa
from ..unidade.unidade import Unidade
from .forms import FormConfigRelatoriosAgendados

rel_agendados_bp = Blueprint(
    name="rel_agendados",
    import_name=__name__,
    url_prefix="/rel-agendados",
    template_folder="templates",
)


@rel_agendados_bp.route("/config", methods=["GET", "POST"])
@login_required
@admin_required
def config_rel_agendados():
    form = FormConfigRelatoriosAgendados()

    if form.validate_on_submit():
        # ler arquivo
        arqv = request.files["csv"]
        data = arqv.read().decode("iso-8859-1")

        # tamnho maximo
        max_size_mb = app.config["MAX_UPLOAD_SIZE_MB"]
        max_bytes = max_size_mb * 1024 * 1024

        if getsizeof(data) > max_bytes:
            flash(f"O arquivo deve ser menor que {max_size_mb} MB", "alert-danger")
            return redirect(url_for("rel_agendados.config_rel_agendados"))

        # ler string como objeto para csv
        df: pd.DataFrame = pd.read_csv(
            filepath_or_buffer=StringIO(data),
            sep=";",
            encoding="iso-8859-1",
        )

        if df.empty:
            flash("Arquivo vazio", "alert-danger")
            return redirect(url_for("rel_agendados.config_rel_agendados"))

        COLS_EMAIL = [
            "conv_exames_emails",
            "exames_realizados_emails",
            "absenteismo_emails",
        ]

        COLS_BOOL = [
            "conv_exames",
            "exames_realizados",
            "absenteismo",
        ]

        tabela = form.tabela.data
        match tabela:
            case 1:  # Empresas
                tabela = Empresa
                coluna_chave = "id_empresa"

                # checar colunas
                colunas_erro = []
                for col in df.columns:
                    if col not in COLS_BOOL + COLS_EMAIL + [coluna_chave]:
                        colunas_erro.append(col)

                if colunas_erro:
                    flash(f"Colunas erradas: {colunas_erro}", "alert-danger")
                    return redirect(url_for("rel_agendados.config_rel_agendados"))

                modelos_query = [
                    (Empresa.id_empresa),
                    (Empresa.razao_social),
                    (Empresa.conv_exames),
                    (Empresa.conv_exames_emails),
                    (Empresa.exames_realizados),
                    (Empresa.exames_realizados_emails),
                    (Empresa.absenteismo),
                    (Empresa.absenteismo_emails),
                ]

                id_empresas = df[coluna_chave].drop_duplicates().astype(int).tolist()
                filtros = [Empresa.id_empresa.in_(id_empresas)]

            case 2:  # Unidades
                tabela = Unidade
                coluna_chave = "id_unidade"

                # checar colunas
                colunas_erro = []
                for col in df.columns:
                    if col not in COLS_BOOL + COLS_EMAIL + [coluna_chave]:
                        colunas_erro.append(col)

                if colunas_erro:
                    flash(f"Colunas erradas: {colunas_erro}", "alert-danger")
                    return redirect(url_for("rel_agendados.config_rel_agendados"))

                modelos_query = [
                    (Unidade.id_unidade),  # inserir nome da empresa
                    (Unidade.nome_unidade),
                    (Unidade.conv_exames),
                    (Unidade.conv_exames_emails),
                    (Unidade.exames_realizados),
                    (Unidade.exames_realizados_emails),
                    (Unidade.absenteismo),
                    (Unidade.absenteismo_emails),
                ]

                id_unidades = df[coluna_chave].drop_duplicates().astype(int).tolist()
                filtros = [Unidade.id_unidade.in_(id_unidades)]

            case _:
                return redirect(url_for("rel_agendados.config_rel_agendados"))

        # tratar df
        df = __tratar_df_config(
            df=df, col_chave=coluna_chave, curr_username=current_user.username  # type: ignore
        )

        df_mappings = df.to_dict(orient="records")

        final_mappings = __handle_celulas_null(
            df_mapping=df_mappings,  # type: ignore
            manter_celulas_null=form.celulas_null.data,
        )

        # backup antes de atualizar
        arq_bk = __gerar_arq_estado_atual(
            nome="backup",
            cols_query=modelos_query,
            filtros_query=filtros,
        )

        try:
            db.session.bulk_update_mappings(tabela, final_mappings)  # type: ignore
            db.session.commit()  # type: ignore
        except (SQLAlchemyError, DatabaseError) as e:
            db.session.rollback()  # type: ignore
            app.logger.error(msg=e, exc_info=True)
            flash("Erro interno ao atualizar tabela", "alert-danger")
            return redirect(url_for("rel_agendados.config_rel_agendados"))

        # gerar report das atualizacoes
        arq_updates = __gerar_arq_estado_atual(
            nome="alteracoes",
            cols_query=modelos_query,
            filtros_query=filtros,
        )

        timestamp = int(datetime.now().timestamp())
        nome_pasta = os.path.join(UPLOAD_FOLDER, f"report_{timestamp}.zip")

        caminho_arquivos = zipar_arquivos(
            caminhos_arquivos=[arq_updates, arq_bk],
            caminho_pasta_zip=nome_pasta,
        )

        return send_from_directory(
            directory=UPLOAD_FOLDER,
            path="/",
            filename=os.path.basename(caminho_arquivos),
        )

    return render_template("relatorios_agendados/config.html", form=form)


def __tratar_df_config(df: pd.DataFrame, col_chave: str, curr_username: str):
    df = df.copy()

    df = df.drop_duplicates(subset=col_chave, ignore_index=True)

    df = df.replace(to_replace={"": None, pd.NA: None, np.nan: None})

    for col in df.columns:
        if "email" in col:
            df[col] = list(
                map(lambda email: tratar_emails(email) if email else None, df[col])
            )

    df["data_alteracao"] = datetime.now(tz=TIMEZONE_SAO_PAULO)
    df["alterado_por"] = curr_username

    return df


def __gerar_arq_estado_atual(
    nome: str, cols_query: list[Any], filtros_query: list[Any]
):
    """
    Realiza query para mostrar como a tabela está atualmente.

    Retorna caminho do csv gerado a partir da query
    """
    query = db.session.query(*cols_query).filter(*filtros_query)  # type: ignore

    timestamp = int(datetime.now().timestamp())
    nome_arq = os.path.join(UPLOAD_FOLDER, f"{nome}_{timestamp}.csv")

    df = pd.read_sql(query.statement, con=db.session.bind)  # type: ignore

    df.to_csv(
        path_or_buf=nome_arq,
        index=False,
        sep=";",
        encoding="iso-8859-1",
    )

    return nome_arq


def __handle_celulas_null(
    df_mapping: list[dict[str, Any]], manter_celulas_null: bool = False
):
    """
    Se celulas null for True, manter as celulas vazias para
    que a informacao correspondente SEJA excluida na tabela da db.

    Se for False, eliminar as celulas vazias para que a informacao
    NAO SEJA apagada na db
    """
    if manter_celulas_null is True:
        final_mapping = df_mapping
    elif manter_celulas_null is False:
        final_mapping = []
        for dic in df_mapping:
            aux = {k: v for k, v in dic.items() if v is not None}
            final_mapping.append(aux)
    else:
        raise ValueError("manter_celulas_null deve ser booleano")
    return final_mapping


@rel_agendados_bp.route("/modelo-empresas", methods=["GET", "POST"])
@login_required
@admin_required
def rel_agendados_modelo_empresas():
    COLS = [
        "id_empresa",
        "conv_exames",
        "conv_exames_emails",
        "exames_realizados",
        "exames_realizados_emails",
        "absenteismo",
        "absenteismo_emails",
    ]

    df = pd.DataFrame(columns=COLS)

    caminho_arq = os.path.join(UPLOAD_FOLDER, "Relatorios_Agendados_Empresas.csv")

    df.to_csv(
        path_or_buf=caminho_arq,
        sep=";",
        index=False,
        encoding="iso-8859-1",
    )

    return send_from_directory(
        directory=UPLOAD_FOLDER, path="/", filename=os.path.basename(caminho_arq)
    )


@rel_agendados_bp.route("/modelo-unidades", methods=["GET", "POST"])
@login_required
@admin_required
def rel_agendados_modelo_unidades():
    COLS = [
        "id_unidade",
        "conv_exames",
        "conv_exames_emails",
        "exames_realizados",
        "exames_realizados_emails",
        "absenteismo",
        "absenteismo_emails",
    ]

    df = pd.DataFrame(columns=COLS)

    caminho_arq = os.path.join(UPLOAD_FOLDER, "Relatorios_Agendados_Unidades.csv")

    df.to_csv(
        path_or_buf=caminho_arq,
        sep=";",
        index=False,
        encoding="iso-8859-1",
    )

    return send_from_directory(
        directory=UPLOAD_FOLDER, path="/", filename=os.path.basename(caminho_arq)
    )
