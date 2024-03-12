import json
from typing import Any

from requests import Response

from .soc_web_service_v2 import SOCWebServiceV2


class ProcessamentoAssincrono(SOCWebServiceV2):
    def __init__(self) -> None:
        super().__init__()

    def call_service(self, request_body: dict) -> object | Response:
        self.attribute_required("client")
        resp = self.client.service.incluirSolicitacao(request_body)  # type: ignore        
        return resp

    def build_request_body(
        self,
        identificacaoWsVo: Any,
        codigoEmpresa: int,
        tipoProcessamento: int,
        parametros: str,
    ):
        self.attribute_required("factory")
        arg = self.factory.processamentoAssincronoWsVo(  # type: ignore
            identificacaoWsVo=identificacaoWsVo,
            codigoEmpresa=str(codigoEmpresa),
            tipoProcessamento=str(tipoProcessamento),
            parametros=parametros,
        )
        return arg

    def generate_identificacaoUsuarioWsVo(self):
        self.attribute_required("WS_KEYS")
        self.attribute_required("factory")

        identificacao = self.factory.identificacaoUsuarioWsVo(  # type: ignore
            codigoEmpresaPrincipal=self.WS_KEYS.get("COD_EMP_PRINCIPAL"),
            codigoResponsavel=self.WS_KEYS.get("COD_RESP"),
            codigoUsuario=self.WS_KEYS.get("USER")
        )
        return identificacao

    def conv_exames_assinc(
        self,
        empresa: int,
        periodo: str,
        selecao: int = 1,
        unidade: str | None = None,
        setor: str | None = None,
        turno: str | None = None,
        exame: str | None = None,
        convocarClinico: bool = False,
        nuncaRealizados: bool = False,
        periodicosNuncaRealizados: bool = False,
        examesPendentes: bool = False,
        convocaPendentesPCMSO: bool = False,
    ):
        """
        Parametro para solicitação de processamento assync convocacao de exames

        periodo: str='mm/aaaa'

        convocarClinico: Se habilitado, caso haja nos riscos do funcionário
        o exame de código CLINICO , se este possuir data Refazer Em dentro
        do período selecionado, então todos os exames do funcionário devem
        ser exibidos considerando a data de vencimento do exame clínico.

        nuncaRealizados: Se habilitado, serão exibidos também os exames
        admissionais ou periódicos do funcionário que nunca foram realizados.
        Essa opção não pode ser usada em conjunto com o parâmetro periodicosNuncaRealizados.

        periodicosNuncaRealizados: Se habilitado, serão exibidos também os
        exames periódicos do funcionário que nunca foram realizados.
        Essa opção não pode ser usada em conjunto com parâmetro nuncaRealizados

        selecao: Informe 1 ou 2, sendo: 1 = "Exames não realizados do período +
        exames em atraso (meses anteriores)" 2 = "Exames do período +
        exames em atraso (meses anteriores)"

        examesPendentes: Se habilitado, contemplará os exames que estão associados a
        um Pedido de Exames, porém não possuem data de resultado.

        convocaPendentesPCMSO: Se habilitado, serão exibidos apenas os exames do PCMSO
        que não possuem data de resultado. Considerase exames do PCMSO os exames que
        estão aplicados ao funcionário, seja através de Risco - Exame,
        Aplicação de Exames ou GHE. Considera-se exames fora do PCMSO
        os exames pedidos através da tela "248 - Pedido de Exames"
        e que não estão aplicados ao funcionário.
        """
        par = {
            "empresa": empresa,
            "unidade": unidade,
            "setor": setor,
            "turno": turno,
            "periodo": periodo,
            "exame": exame,
            "convocarClinico": convocarClinico,
            "nuncaRealizados": nuncaRealizados,
            "periodicosNuncaRealizados": periodicosNuncaRealizados,
            "selecao": selecao,
            "examesPendentes": examesPendentes,
            "convocaPendentesPCMSO": convocaPendentesPCMSO,
        }
        return self.processar_parametro(par)

    @staticmethod
    def processar_parametro(param: dict[str, Any]) -> str:
        param_tratado = param.copy()

        for key, value in param.items():
            if value is None:  # remover chaves nulas
                param_tratado.pop(key)
            elif isinstance(value, bool):  # boolean to int
                param_tratado[key] = int(param_tratado[key])

        return json.dumps(param_tratado)
