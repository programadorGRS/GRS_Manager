import json
from typing import Any

import pandas as pd
from requests import Response

from .exporta_dados_params import ExportaDadosParams
from .soc_web_service_v2 import SOCWebServiceV2


class ExportaDados(SOCWebServiceV2, ExportaDadosParams):
    ED_KEYS: dict

    def __init__(self) -> None:
        super().__init__()

    def call_service(self, request_body: dict) -> object | Response:
        self.attribute_required("client")
        resp = self.client.service.exportaDadosWs(request_body)  # type: ignore
        return resp

    def set_ed_keys(self, keys: dict[str, Any]):
        self.ED_KEYS = keys
        return None

    def build_request_body(self, param: str):
        self.attribute_required("factory")
        # NOTE: zeep entende que a tag erro é obrigatória no request\
        # porém ela só é valida na response, portanto não faz diferença aqui
        arg0 = self.factory.exportaDadosWsVo(  # type: ignore
            parametros=param, erro=False
        )
        return arg0

    @staticmethod
    def df_from_zeep(response: Any) -> pd.DataFrame:
        retorno = response.retorno
        return pd.DataFrame(data=json.loads(retorno))
