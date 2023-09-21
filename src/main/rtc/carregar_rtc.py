import pandas as pd

from src.soc_web_service.exporta_dados import ExportaDados

from .exceptions import RTCValidationError


class CarregarRTC:
    def __init__(self) -> None:
        pass

    @classmethod
    def tratar_df_rtc_cargos(
        cls, cod_emp_princ: int, df: pd.DataFrame
    ) -> pd.DataFrame:
        df = df.copy()

        cls.__validate_rtc_cargos_cols(df)

        df = cls.__get_cod_cargos(cod_emp_princ, df)

        df = cls.__transpose_rtc_cargos_cols(df)

        return df

    @staticmethod
    def __validate_rtc_cargos_cols(df: pd.DataFrame):
        KEY_COLS = ["nome_cargo"]
        RTC_COLS = [c for c in df.columns if "RTC_" in c]

        for c in KEY_COLS:
            if c not in df.columns:
                raise RTCValidationError(f"A coluna {c} é obrigatória")

        if len(RTC_COLS) == 0:
            raise RTCValidationError("Nenhuma coluna RTC_ encontrada")
        return None

    @classmethod
    def __get_cod_cargos(cls, cod_emp_principal: int, df: pd.DataFrame):
        df = df.copy()

        AUX_COLS = {"CODIGOCARGO": "cod_cargo", "NOMECARGO": "nome_cargo"}

        # NOTE: allow xml_huge_tree because of huge response body
        ex = ExportaDados(
            wsdl_filename="prod/ExportaDadosWs.xml",
            exporta_dados_keys_filename="grs.json",
            client_raw_response=False,
            xml_huge_tree=True,
        )

        PARAM = ex.cargos(
            empresa=cod_emp_principal,
            codigo=ex.EXPORTA_DADOS_KEYS.get("CARGOS_COD"),
            chave=ex.EXPORTA_DADOS_KEYS.get("CARGOS_KEY"),
        )

        body = ex.build_request_body(param=PARAM)

        resp = ex.call_service(request_body=body)

        df_aux = ex.dataframe_from_zeep(retorno=getattr(resp, "retorno", None))

        df_aux = df_aux[list(AUX_COLS.keys())]
        df_aux = df_aux.rename(columns=AUX_COLS)

        if df_aux.empty:
            return None

        df = df.merge(right=df_aux, how="left", on="nome_cargo")

        return df

    @staticmethod
    def __transpose_rtc_cargos_cols(df: pd.DataFrame):
        df = df.copy()

        COLS = ["id_rtc", "cod_cargo", "nome_cargo"]

        new_df = pd.DataFrame(columns=COLS)

        for col in df.columns:
            if not col.startswith("RTC_"):
                continue

            # copy to avoid warnings
            df_aux = df[df[col] == "X"].copy()

            if df_aux.empty:
                continue

            df_aux["id_rtc"] = int(col.split("_")[-1])
            df_aux = df_aux[COLS]

            new_df = pd.concat(objs=[new_df, df_aux], axis=0, ignore_index=True)

        return new_df
