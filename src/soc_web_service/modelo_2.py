from typing import Literal

from zeep.client import Factory


class Modelo2:
    factory: Factory

    def __init__(self, factory: Factory) -> None:
        self.factory = factory

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

