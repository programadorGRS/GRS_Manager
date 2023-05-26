from typing import Literal

from .soc_web_service import SOCWebService
from requests import Response


class Modelo2(SOCWebService):
    def __init__(self, wsdl_filename: str, **kwargs) -> None:
        """Classe para integração com o módulo Modelo 2 do SOC"""
        super().__init__(wsdl_filename=wsdl_filename, **kwargs)

    def call_service(self, request_body: dict) -> object | Response:
        """
            Gera usernameToken e envia request para o servico

            Args:
                request_body (zeep.object -> dict): corpo XML do request para ser enviado.
                Deve ser construido usando os metodos zeep da classe

            Retorna requests.Response ou zeep.ResponseObject (dict) de acordo com
            o atributo client_raw_response (bool) da classe.
        """
        self.generate_username_token()

        resp = self.client.service.importacaoFuncionario(request_body)

        return resp

    def Funcionario(
            self,
            destravarFuncionarioBloqueado: int = 0,
            naoImportarFuncionarioSemHierarquia: int = 1,
            transferirFuncionario: int = 0,
        ) -> object:
        funcionario = self.factory.Funcionario(
            destravarFuncionarioBloqueado=destravarFuncionarioBloqueado,
            naoImportarFuncionarioSemHierarquia=naoImportarFuncionarioSemHierarquia,
            transferirFuncionario=transferirFuncionario
        )
        return funcionario

    def config_criacoes(self, funcionario: object, criar: Literal[0, 1] = 0, **kwargs):
        '''
            Configura os campos obrigatórios:
                - criarCargo
                - criarCentroCusto
                - criarFuncionario
                - criarHistorico
                - criarMotivoLicenca
                - criarSetor
                - criarTurno
                - criarUnidade
                - criarUnidadeContratant

            Defaults to: 0 (zero) - false
        '''
        atributos = [
            'criarCargo',
            'criarCentroCusto',
            'criarFuncionario',
            'criarHistorico',
            'criarMotivoLicenca',
            'criarSetor',
            'criarTurno',
            'criarUnidade',
            'criarUnidadeContratante'
        ]

        for att in atributos:
            setattr(funcionario, att, criar)

        if kwargs:
            for name, value in kwargs.items():
                setattr(funcionario, name, value)

        return None

    def config_atualizacoes(self, funcionario: object, atualizar: Literal[0, 1] = 0, **kwargs):
        '''
            Configura os campos obrigatórios:
                - atualizarCargo
                - atualizarCentroCusto
                - atualizarFuncionario
                - atualizarMotivoLicenca
                - atualizarSetor
                - atualizarTurno
                - atualizarUnidade

            Defaults to: 0 (zero) - false
        '''
        atributos = [
            'atualizarCargo',
            'atualizarCentroCusto',
            'atualizarFuncionario',
            'atualizarMotivoLicenca',
            'atualizarSetor',
            'atualizarTurno',
            'atualizarUnidade'
        ]

        for att in atributos:
            setattr(funcionario, att, atualizar)

        if kwargs:
            for name, value in kwargs.items():
                setattr(funcionario, name, value)

        return None

    def funcionarioWsVo(
            self,
            codigo: int,
            codigoEmpresa: int,
            chaveProcuraFuncionario: str = 'CODIGO',
            tipoBuscaEmpresa: str = 'CODIGO_SOC',
            **kwargs
        ):
        tag = self.factory.funcionarioWsVo(
            codigo=codigo,
            codigoEmpresa=codigoEmpresa,
            chaveProcuraFuncionario=chaveProcuraFuncionario,
            tipoBuscaEmpresa=tipoBuscaEmpresa
        )

        if kwargs:
            for key, value in kwargs.items():
                setattr(tag, key, value)

        # NOTE: campos personalizados de cadastro \
        # não usamos, mas são obrigatorios
        for key in dir(tag):
            if 'campoInteiro' in key:
                setattr(tag, key, 0)
        return tag

