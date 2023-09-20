from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd
from pandas.errors import IntCastingNaNError

from src.extensions import database as db

from ..pedido.pedido import Pedido
from ..status.status import Status
from ..status.status_lib import StatusLiberacao


@dataclass
class DfValidationInfos:
    """DataClass para validação dos DataFrames de em bulk update

    Attributes:
        ok: bool
        df: DataFrame
        msgs: list[tuple(str, str)] = lista de mensagens para flash (msg, categoria)
    """

    ok: bool = True
    df: pd.DataFrame = pd.DataFrame()
    msgs: list[tuple[str, str]] | None = None

    def add_msg(self, msg: str, category: str):
        if self.msgs:
            self.msgs.append((msg, category))
        else:
            self.msgs = [(msg, category)]
        return None


class BulkUpdateHandler:
    def __init__(self) -> None:
        self.REQUIRED_COLS: dict[str, type] = {"id_ficha": int, "id_status": int}

        self.ALLOWED_COLS: dict[str, type] = {
            "data_recebido": date,
            "data_comparecimento": date,
            "obs": str,
        }

        return None

    def handle_df_columns(
        self, df: pd.DataFrame, required_cols: list[str], allowed_cols: list[str]
    ):
        """Validar colunas aceitas no dataframe"""
        df = df.copy()

        res = DfValidationInfos()

        all_cols = required_cols + allowed_cols
        for col in df.columns:
            # remover cols invalidas
            if col not in all_cols:
                df = df.drop(columns=col)
            # remover cols vazias
            elif df[col].dropna().empty:
                df = df.drop(columns=col)

        if df.empty:
            res.ok = False
            res.add_msg(
                msg="A tabela não possui colunas válidas", category="alert-danger"
            )
            return res

        # validar cols obrigatorias
        for col in required_cols:
            if col not in df.columns:
                res.ok = False
                res.add_msg(
                    msg=f"A coluna {col} é obrigatória", category="alert-danger"
                )
                return res

        res.df = df

        return res

    def cast_df_col_types(self, df: pd.DataFrame, cols: dict[str, type]):
        """Converter as colunas aceitas para os tipos corretos"""
        df = df.copy()

        res = DfValidationInfos()

        for col, col_type in cols.items():
            if col not in df.columns:
                continue

            match col_type.__name__:
                case int.__name__:
                    try:
                        df[col] = df[col].astype(int)
                    except (IntCastingNaNError, ValueError):
                        res.ok = False
                        res.add_msg(
                            msg=f"Erro ao tratar a coluna {col}. "
                            "Deve conter apenas números inteiros",
                            category="alert-danger",
                        )
                        return res

                case date.__name__:
                    try:
                        df[col] = df[col].astype(str)
                        df[col] = pd.to_datetime(df[col], dayfirst=True).dt.date
                        # NOTE: remover pd.NaT, databases aceitam apenas None como valor nulo
                        df[col] = df[col].astype(object).replace(pd.NaT, None)  # type: ignore
                    except Exception:
                        res.ok = False
                        res.add_msg(
                            msg=f"Erro ao tratar a coluna {col}. "
                            "Deve conter apenas datas no formato: dd/mm/yyyy.",
                            category="alert-danger",
                        )
                        return res

                case str.__name__:
                    df[col] = df[col].astype(object).replace(np.nan, None)

        res.df = df

        return res

    def handle_enum_col(self, df: pd.DataFrame, col_name: str, table: object):
        """Validar coluna que possui restrição de valores aceitos. Exemplo: id_status, id_status_rac"""
        df = df.copy()

        res = DfValidationInfos()

        query = table.query.all()  # type: ignore

        valid_vals: list[int] = [getattr(val, col_name) for val in query]

        invalid_vals: list[str] = []
        for val in df[col_name].drop_duplicates():
            if val not in valid_vals:
                invalid_vals.append(str(val))

        if invalid_vals:
            res.ok = False
            res.add_msg(
                msg=f"A coluna {col_name} contém valores inválidos. | "
                f"Exemplo: {',' .join(invalid_vals)}",
                category="alert-danger",
            )
            return res

        res.df = df

        return res

    def handle_id_ficha(self, df: pd.DataFrame):
        """Valida id das fichas e remove fichas inexistentes"""
        df = df.copy()

        res = DfValidationInfos()

        query = db.session.query(Pedido.id_ficha).filter(  # type: ignore
            Pedido.id_ficha.in_(df["id_ficha"])
        )
        df_db = pd.read_sql(query.statement, con=db.session.bind)  # type: ignore

        df_invalidos = df[~df["id_ficha"].isin(df_db["id_ficha"])]
        ids_invalidos = df_invalidos["id_ficha"].astype(str).tolist()

        if ids_invalidos:
            res.ok = False
            ids_df = df["id_ficha"].drop_duplicates().tolist()
            if len(ids_invalidos) == len(ids_df):
                # se todos os ids forem invalidos
                res.add_msg(
                    msg="Os pedidos na tabela não foram encontrados no banco de dados",
                    category="alert-danger",
                )
            else:
                # se alguns forem invalidos
                res.add_msg(
                    msg="Alguns IDs de Ficha não foram encontrados no banco de dados | "
                    f'Total: {len(ids_invalidos)} | Ex: {", ".join(ids_invalidos[:10])}',
                    category="alert-danger",
                )
            return res

        res.df = df

        return res

    def handle_status_lib(self, df: pd.DataFrame):
        df = df.copy()

        # buscar prev liberacao
        query = db.session.query(Pedido.id_ficha, Pedido.prev_liberacao).filter(  # type: ignore
            Pedido.id_ficha.in_(df["id_ficha"])
        )
        df_db = pd.read_sql(query.statement, con=db.session.bind)  # type: ignore

        df = df.merge(df_db, how="left", on="id_ficha")

        # inserir tags prev lib
        df["id_status_lib"] = list(
            map(Pedido.calcular_tag_prev_lib, df["prev_liberacao"])
        )
        df = df.drop(columns="prev_liberacao")

        # status que finalizam processo
        stt_fin_proc = db.session.query(Status.id_status).filter(  # type: ignore
            Status.finaliza_processo == True  # noqa
        )
        list_stt_fin_proc = [status.id_status for status in stt_fin_proc]

        TAG_OK = StatusLiberacao.get_id_status_ok()
        df.loc[df["id_status"].isin(list_stt_fin_proc), "id_status_lib"] = TAG_OK

        return df

    def tto_final_bulk_update(self, df: pd.DataFrame):
        df = df.copy()

        COLS = [
            "id_ficha",
            "id_status",
            "id_status_lib",
            "data_recebido",
            "data_comparecimento",
            "obs",
            "data_alteracao",
            "alterado_por",
        ]

        for col in df.columns:
            if col not in COLS:
                df = df.drop(columns=col)

        return df
