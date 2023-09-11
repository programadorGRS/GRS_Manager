import json
from datetime import date


class ExportaDadosParams:
    date_format: str

    def __init__(self) -> None:
        self.date_format = "%d/%m/%Y"

    def set_date_format(self, date_format: str):
        self.date_format = date_format
        return None

    def conv_exames_assinc(
        self,
        empresa: int,
        codigo: int,
        chave: str,
        empresaTrabalho: int,
        codigoSolicitacao: int,
        tipoSaida: str = "json",
    ):
        """Convocação de Exames - Assíncrono
        Exporta Dados com o objetivo de exibir os exames dos funcionários,
        vencidos ou a vencer no período informado.

        Parâmetros de entrada:

        - empresa: Tipo: Numérico (8)
        - empresaTrabalho: Tipo: Numérico (8)
        - codigoSolicitacao: Tipo: Numérico (20)

        Campos de saída: CODIGOEMPRESA, NOMEABREVIADO, UNIDADE, CIDADE,
        ESTADO, BAIRRO, ENDERECO, CEP, CNPJUNIDADE, SETOR, CARGO,
        CODIGOFUNCIONARIO, CPFFUNCIONARIO, MATRICULA, DATAADMISSAO, NOME,
        EMAILFUNCIONARIO, TELEFONEFUNCIONARIO, CODIGOEXAME, EXAME,
        ULTIMOPEDIDO, DATARESULTADO, PERIODICIDADE, REFAZER

        Descrição dos filtros:

        - Empresa Selecionada: Informe o código da Empresa Cliente a ser consultada.
        - Código Solicitação: Preencha com o código da Solicitação de
        Processamento Assíncrono recebido via Web Service.
        """
        par = {
            "empresa": empresa,
            "codigo": codigo,
            "chave": chave,
            "tipoSaida": tipoSaida,
            "empresaTrabalho": empresaTrabalho,
            "codigoSolicitacao": codigoSolicitacao,
        }
        return self.__processar_parametro(par)

    def prestadores(
        self,
        empresa: int,
        codigo: int,
        chave: int,
        cod: int | None = None,
        ativo: bool | None = None,
        cnpj: str | None = None,
        cpf: str | None = None,
        cidade: str | None = None,
        estado: str | None = None,
        tipoPrestador: str | None = None,
        tipoPessoa: str | None = None,
        tipoSaida: str = "json",
    ):
        """
        Prestadores

        Exporta dados de Prestadores com filtros por cnpj, cpf, codigo do prestador, \
        situacao, cidade, estado, tipo de prestador e tipo de pessoa.

        Campos de saída:socnet, codigoPrestador, situacao, statusContrato, bairro, cidade, estado, endereco, numeroEndereco, complementoEndereco, cep, \
        representanteLegal, cnpj, cpf, codigoAgenciaBanco, codigoBanco, nomeBanco, numeroContaCorrente, nomeTitularConta, \
        dataCancelamento, dataContratacao, diaPagamento, email, horarioAtendimentoInicial, horarioAtendimentoFinal
        , motivoCancelamento, nomePrestador, razaoSocial, telefone, celular, tipoAtendimento, tipoPagamento, tipoPrestador, \
        tipoPessoa, regraPadraoPagamento, codigoRH, nivelClassificacao, responsavel, pagamentoAntecipado, \
        conselhoClasse, ufConselhoClasse, especialidadeResponsavel, especialidadeResponsavel2
        """
        par = {
            "empresa": empresa,
            "codigo": codigo,
            "chave": chave,
            "tipoSaida": tipoSaida,
            "cnpj": cnpj,
            "cpf": cpf,
            "cod": cod,
            "ativo": ativo,
            "cidade": cidade,
            "estado": estado,
            "tipoPrestador": tipoPrestador,
            "tipoPessoa": tipoPessoa,
        }
        return self.__processar_parametro(param=par)

    def __processar_parametro(self, param: dict) -> str:
        param_tratado = param.copy()

        for key, value in param.items():
            if value is None:  # remover chaves nulas
                param_tratado.pop(key)
            elif isinstance(value, date):  # parse dates to string
                param_tratado[key] = param_tratado[key].strftime(self.date_format)
            elif isinstance(value, bool):  # boolean to int
                param_tratado[key] = int(param_tratado[key])

        return json.dumps(param_tratado)
