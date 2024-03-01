import json
from datetime import date

import pandas as pd
from requests import Response

from .soc_web_service import SOCWebService


class ExportaDados(SOCWebService):
    date_format: str
    EXPORTA_DADOS_KEYS: dict

    def __init__(
        self,
        wsdl_filename: str,
        exporta_dados_keys_filename: str,
        **kwargs
    ) -> None:
        '''
            Classe para integração com o Exporta Dados do SOC

            Arguments:
                wsdl_filename (str): apenas nome do arquivo WSDL. \
                Pasta: configs/soc/wsdl

                exporta_dados_keys_filename (str): nome do arquivo json de \
                chaves do Exporta Dados. Pasta: keys/soc/exporta_dados

            Attributes:
                EXPORTA_DADOS_KEYS (dict[str | any]): chaves dos Exporta Dados
        '''
        super().__init__(wsdl_filename=wsdl_filename, **kwargs)
        self.date_format = '%d/%m/%Y'
        self.set_exporta_dados_keys(filename=exporta_dados_keys_filename)

    def call_service(self, request_body: dict) -> object | Response:
        """
            Envia request para o servico

            Args:
                request_body (zeep.object -> dict): corpo XML do request para ser enviado.
                Deve ser construido usando os metodos zeep da classe

            Retorna requests.Response ou zeep.ResponseObject (dict) de acordo com
            o atributo client_raw_response (bool) da classe.
        """
        resp = self.client.service.exportaDadosWs(request_body)

        return resp

    def set_exporta_dados_keys(self, filename: str):
        '''
            Seta EXPORTA_DADOS_KEYS.

            Args:
                filename (str): nome do arquivo. O arquivo deve estar na pasta keys/soc/exporta_dados/
        '''
        self.EXPORTA_DADOS_KEYS: dict = self.read_json(path=f'keys/soc/exporta_dados/{filename}')
        return None

    def build_request_body(self, param: str):
        # NOTE: zeep entende que a tag erro é obrigatória no request\
        # porém ela só é valida na response, portanto não faz diferença aqui
        arg0 = self.factory.exportaDadosWsVo(
            parametros=param,
            erro=False
        )
        return arg0

    @staticmethod
    def dataframe_from_zeep(retorno: str) -> pd.DataFrame:
        """
            Recebe json string da tag 'retorno' de uma Response do Exporta Dados e \
            transforma em pd.DataFrame
        """
        return pd.DataFrame(data=json.loads(retorno))

    @staticmethod
    def json_from_zeep(retorno: str) -> list[dict[str, any]]:
        """
            Recebe json string da tag 'retorno' de uma Response do Exporta Dados e \
            transforma em list[dict]
        """
        return json.loads(retorno)

    def __processar_parametro(self, param: dict) -> str:
        param_tratado = param.copy()

        for key, value in param.items():
            if value is None: # remover chaves nulas
                param_tratado.pop(key)
            elif isinstance(value, date): # parse dates to string
                param_tratado[key] = param_tratado[key].strftime(self.date_format)
            elif isinstance(value, bool): # boolean to int
                param_tratado[key] = int(param_tratado[key])

        return json.dumps(param_tratado)

    def pedido_exame(
        self,
        empresa: int,
        codigo: int,
        chave: str,
        dataInicio: date,
        dataFim: date,
        paramData: bool = True,
        paramSequencial: bool = False,
        sequenciaFicha: int | None = None,
        funcionarioInicio: int = 0,
        funcionarioFim: int = 999999999,
        paramFunc: bool = False,
        cpffuncionario: str | None = None,
        nomefuncionario: str | None = None,
        paramPresta: bool = False,
        codpresta: int | None = None,
        nomepresta: str | None = None,
        paramUnidade: bool = False,
        codunidade: str | None = None,
        nomeunidade: str | None = None,
        tipoSaida: str = 'json'
    ) -> str:
        '''
            Pedido Exame

            Descrição: Neste Exporta Dados, serão listadas todas as informações relacionadas ao \
            pedido de exame, incluindo dados do funcionário e da hierarquia.

            Campos: CODIGOEMPRESA, NOMEEMPRESA, CNPJEMPRESA, CPFEMPRESA, CEIEMPRESA, SUBGRUPOEMPRESA, \
            SEQUENCIAFICHA, CODIGOFUNCIONARIO, NOMEFUNCIONARIO, CPFFUNCIONARIO, MATRICULAFUNCIONARIO, \
            RGFUNCIONARIO, CODIGOCENTROCUSTO, NOMECENTROCUSTO, CODIGOUNIDADE, CNPJUNIDADE, CPFUNIDADE, \
            CEIUNIDADE, NOMEUNIDADE, CODIGOSETOR, NOMESETOR, CODIGOCARGO, NOMECARGO, DATACRIACAOPEDIDOEXAMES, \
            CODIGOPRESTADOR, NOMEPRESTADOR, CODIGOTIPOEXAME, DATAFICHA, CODIGOTUSSEXAME, CODIGOEXAMEAMB, \
            CODIGOINTERNOEXAME, NOMEEXAME, DATAEXAME, RISCOSFUNCIONARIO, MEDICOCOORDENADOR, UFMEDICO, \
            CRM, RESPONSAVELPEDIDOEXAME, RISCOSASO, DATA NASCIMENTO, NOMEDAMAEDOFUNCIONARIO, CPFMEDICOEXAMINADOR, CODIGORH

            Obs: 'empresa' é o cod da empresa dos pedidos de exame, nao é o cod da EmpresaPrincipal
        '''

        param = {
            'empresa': empresa,
            'codigo': codigo,
            'chave': chave,
            'tipoSaida': tipoSaida,
            'paramSequencial': paramSequencial,
            'sequenciaFicha': sequenciaFicha,
            'funcionarioInicio': funcionarioInicio,
            'funcionarioFim': funcionarioFim,
            'paramData': paramData,
            'dataInicio': dataInicio,
            'dataFim': dataFim,
            'paramFunc': paramFunc,
            'cpffuncionario': cpffuncionario,
            'nomefuncionario': nomefuncionario,
            'codpresta': codpresta,
            'nomepresta': nomepresta,
            'paramPresta': paramPresta,
            'codunidade': codunidade,
            'nomeunidade': nomeunidade,
            'paramUnidade': paramUnidade
        }

        return self.__processar_parametro(param=param)

    def empresas(
        empresa_principal: int,
        cod_exporta_dados: int,
        chave: str,
        tipoSaida: str = 'json'
    ) -> dict:
        '''
            Cadastro de Empresas

            Descrição: Exporta Dados que Listara Informações básicas sobre as Empresas/Cliente cadastradas no Sistema.

            Campos: CODIGO, APELIDO, NOME, RAZAOSOCIAL, ENDERECO, NUMEROENDERECO, COMPLEMENTOENDERECO, BAIRRO, CIDADE, \
            CEP, UF, CNPJ, INSCRICAOESTADUAL, INSCRICAOMUNICIPAL, ATIVO, CODIGOCLIENTEINTEGRACAO.
        '''
        parametro = {
            'empresa':empresa_principal,
            'codigo':cod_exporta_dados,
            'chave':chave,
            'tipoSaida':tipoSaida
        }
        return parametro

    def unidades(
        self,
        empresa: int,
        codigo: int,
        chave: str,
        ativo: int | None = None,
        tipoSaida: str = 'json'
    ) -> dict:
        '''
        Cadastro de Unidades (todas empresas)

        Será listado Todas Unidades e suas Respectivas Empresas/Clientes \
        com informações básicas de cada uma das Unidades.

        Campos: CODIGOEMPRESA, NOMEEMPRESA, CODIGOUNIDADE, NOMEUNIDADE, \
        CODIGORHUNIDADE, GRAUDERISCOUNIDADE, UNIDADEATIVA,
        CNPJUNIDADE, INSCRICAOESTADUALUNIDADE, CODIGOCLIENTEINTEGRACAO, \
        ENDERECO, NUMEROENDERECO, COMPLEMENTO, BAIRRO, CIDADE, \
        UF, CEP, CPFUNIDADE, RAZAOSOCIAL.

        ativo: situacao da empresa (puxa todos se vazio)
        '''
        param = {
            'empresa':empresa,
            'codigo':codigo,
            'chave':chave,
            'tipoSaida':tipoSaida,
            'ativo':ativo
        }
        return self.__processar_parametro(param=param)

    def prestadores(
        cod_empresa_principal: int,
        cod_exporta_dados: int,
        chave: str,
        cnpj: str = '',
        cpf: str = '',
        cod: str = '',
        cidade: str = '',
        estado: str = '',
        tipoPrestador: str = '',
        tipoPessoa: str = '',
        ativo: int = '',
        tipoSaida: str = 'json',
    ):
        '''
        Prestadores

        Exporta dados de Prestadores com filtros por cnpj, cpf, codigo do prestador, \
        situacao, cidade, estado, tipo de prestador e tipo de pessoa.

        Campos de saída:socnet, codigoPrestador, situacao, statusContrato, bairro, cidade, estado, endereco, numeroEndereco, complementoEndereco, cep, \
        representanteLegal, cnpj, cpf, codigoAgenciaBanco, codigoBanco, nomeBanco, numeroContaCorrente, nomeTitularConta, \
        dataCancelamento, dataContratacao, diaPagamento, email, horarioAtendimentoInicial, horarioAtendimentoFinal
        , motivoCancelamento, nomePrestador, razaoSocial, telefone, celular, tipoAtendimento, tipoPagamento, tipoPrestador, \
        tipoPessoa, regraPadraoPagamento, codigoRH, nivelClassificacao, responsavel, pagamentoAntecipado, \
        conselhoClasse, ufConselhoClasse, especialidadeResponsavel, especialidadeResponsavel2
        '''
        parametro = {
            'empresa':cod_empresa_principal,
            'codigo':cod_exporta_dados,
            'chave':chave,
            'tipoSaida':tipoSaida,
            'cnpj':cnpj,
            'cpf':cpf,
            'cod':cod,
            'ativo':ativo,
            'cidade':cidade,
            'estado':estado,
            'tipoPrestador':tipoPrestador,
            'tipoPessoa':tipoPessoa
        }
        return parametro

    def exames(
        cod_empresa_principal: int,
        cod_exporta_dados: int,
        chave: str,
        tipoSaida: str = 'json',
    ):
        '''
        Tabela de Exames

        Exporta Dados que conterá um a lista de todos os códigos de Exames 
        e seu Nome cadastrados na tela de Exame.
        Tipo de Saída: Exporta Dados dedicado ao uso via Web Service.
        
        Campos: COD, DESCRICAO.
        '''
        parametro = {
            'empresa':cod_empresa_principal,
            'codigo':cod_exporta_dados,
            'chave': chave,
            'tipoSaida':tipoSaida
        }
        return parametro

    def exames_realizados_empresa(
        cod_empresa_principal: int,
        cod_exporta_dados: int,
        chave: str,
        empresaTrabalho: int,
        dataInicio: str,
        dataFim: str,
        tipoSaida: str = 'json',
    ):
        '''
        Exames realizados por data de exames por empresa

        Este exportado dados listará todos os exames realizados separados por empresas clientes.
        
        Campos: EMPRESA, CODFUNCIONARIO, NOMEFUNCIONARIO, MATRICULA, DATAFICHA, TIPOFICHA, DATAEXAMES, \
        CODEXAME, NOMEEXAME, EXAMEALTERADO, SAIASO.
        '''
        par = {
            'empresa':cod_empresa_principal,
            'codigo':cod_exporta_dados,
            'chave':chave,
            'tipoSaida':tipoSaida,
            'empresaTrabalho':empresaTrabalho,
            'dataInicio':dataInicio,
            'dataFim':dataFim
        }
        return par

    def cadastro_funcionarios(
        self,
        empresa: int,
        codigo: int,
        chave: str,
        empresaTrabalho: int,
        parametroData: bool = False,
        dataInicio: date | None = None,
        dataFim: date | None = None,
        cpf: str | None = None,
        tipoSaida: str = 'json'
    ):
        '''
        Cadastro de Funcionarios (Por Empresa)

        Dependendo da Empresa que estiver sendo acessado, este Exporta Dados \
        irá listar todos os Funcionários que estão cadastrados na Empresa Logada. \
        Será trazido todos os Funcionários, não importando sua situação.

        Parâmetros de entrada:
            - empresaTrabalho: Tipo: Numérico (8); Obs.: Este campo serve \
            como filtro para selecionar a Empresa, e trazer todos os \
            Funcionários, não importando sua situação.
            - cpf: Tipo: Alfanumérico; Obs.: Deverá ser preenchido somente com números.
            - parametroData: Tipo: Booleano; Obs.: Habilite este campo caso \
            seja necessário realizar a pesquisa dentro de um período \
            específico. Quando este campo estiver selecionado, será \
            obrigatório informar as datas Início e Fim.
            - dataInicio: Tipo: Data
            - dataFim: Tipo: Data

            OBS: os campos dataInicio e dataFim se referem às datas de \
            Admissão ou Demissão dos Funcionários.

        Campos de saída:
            CODIGOEMPRESA, NOMEEMPRESA, CODIGO, NOME, CODIGOUNIDADE, NOMEUNIDADE, \
            CODIGOSETOR, NOMESETOR, CODIGOCARGO, NOMECARGO, CBOCARGO, \
            MATRICULAFUNCIONARIO, CPFFUNCIONARIO, SITUACAO, DATA_NASCIMENTO, \
            DATA_ADMISSAO, DATA_DEMISSAO, ENDERECO, NUMERO_ENDERECO, BAIRRO, UF, \
            EMAILCORPORATIVO, EMAILPESSOAL, TELEFONECELULAR, DATACADASTRO
        '''
        par = {
            'empresa': empresa,
            'codigo': codigo,
            'chave': chave,
            'tipoSaida': tipoSaida,
            'empresaTrabalho': empresaTrabalho,
            'cpf': cpf,
            'parametroData': parametroData,
            'dataInicio': dataInicio,
            'dataFim': dataFim
            }
        
        return self.__processar_parametro(param=par)

    def licenca_socind(
        cod_empresa_principal: int,
        cod_exporta_dados: int,
        chave: str,
        empresaTrabalho: int,
        dataInicio: str = '',
        dataFim: str = '',
        tipoSaida: str = 'json'
    ):
        '''
        Licença (SOCIND)
        
        Trará informações sobre as Licenças Médicas da Empresa
        Campos: TIPO_LICENCA, CODIGO_MEDICO, MEDICO, DATA_FICHA, AFASTAMENTO_EM_HORAS, \
        DATA_INICIO_LICENCA, DATA_FIM_LICENCAO, HORA_INICIO, HORA_FIM, MOTIVO_LICENCA, \
        CID_CONTESTADO, TIPO_CID, ACIDENTE_TRAJETO, SOLICITANTE, ESPECIALIDADE, \
        DATA_SOLICITACAO, LOCAL_ATENDIMENTO, CIDADE_ATENDIMENTO, ESTADO_ATENDIMENTO, \
        NUMERO_BENEFICIO, ESPECIO_BENEFICIO, SITUACAO, DATA_INICIO_FAP, DATA_INDEFERIMENTO, \
        DATA_ULTIMO_DIA_TRABALHO, DATA_REQUERIMENTO, DATA_DESPACHO, PERICIA, \
        DATA_LIMITE_DOSE, DATA_CESSACAO.

        Data Inicio/data fim: Insira um intervalo de datas.

        OBS: o filtro de datas e por data da ficha
        '''
        par = {
            'empresa':cod_empresa_principal,
            'codigo':cod_exporta_dados,
            'chave':chave,
            'tipoSaida':tipoSaida,
            'empresaTrabalho':empresaTrabalho,
            'dataInicio':dataInicio,
            'dataFim':dataFim
        }

        return par

    def licenca_medica(
        cod_exporta_dados: int,
        chave: str,
        empresaTrabalho: int,
        dataInicio: str = '',
        dataFim: str = '',
        tipoSaida: str = 'json',
        pData: int = 0
    ):
        '''
        Licença Médica - Informações Básicas
        
        Interface responsável pelo retorno dos dados básicos de um Afastamento \
        - Não consta informações do eSocial

        Exporta Dados com o objetivo de listar informações referentes a Licença \
        Médica de um período específico.
        Campos: FUNCIONARIO, MATRICULA, CPF, MEDICO, CONSELHO, \
        CRM, SOLICITANTE, CONSELHO_SOLICITANTE, CRM_SOLICITANTE, \
        SOLICITANTEFICHA, CONSELHO_SOLICITANTEFICHA, CRM_SOLICITANTEFICHA, \
        DATAFICHA, TIPOLICENCA, AFASTHORAS, DIASAFASTADOS, \
        PEIODOAFASTADO, SITUACAO, ABONADO, CID.

        Param. data: Responsável por determinar qual a origem das \
        informações para os filtros de datas. Os valores possíveis para o parâmetro são:
        - 0 A busca das informações será baseada na data da ficha do afastamento.
        - 1 A busca das informações será baseada na data de início do afastamento.
        '''
        par = {
            'empresa':empresaTrabalho,
            'codigo':cod_exporta_dados,
            'chave':chave,
            'tipoSaida':tipoSaida,
            'funcionarioInicio':'0',
            'funcionarioFim':'999999999999',
            'dataInicio':dataInicio,
            'dataFim':dataFim,
            'pData':pData
        }

        return par

    def sol_conv_exames_assync(
        cod_empresa: int,
        periodo: str,
        cod_unidade: int='',
        cod_setor: int='',
        cod_turno: int='',
        cod_exame: int='',
        convocar_clinico: str='false',
        nunca_realizados: str='true',
        periodicos_nunca_realizados: str='false',
        exames_pendentes: str='true',
        conv_pendentes_pcmso: str='false',
        selecao: int=1,
    ):
        '''
        Parametro para solicitação de processamento assync convocacao de exames

        periodo: str='mm/aaaa'

        convocarClinico: Se habilitado, caso haja nos riscos do funcionário\ 
        o exame de código CLINICO , se este possuir data Refazer Em dentro\ 
        do período selecionado, então todos os exames do funcionário devem\ 
        ser exibidos considerando a data de vencimento do exame clínico.

        nuncaRealizados: Se habilitado, serão exibidos também os exames\ 
        admissionais ou periódicos do funcionário que nunca foram realizados.\
        Essa opção não pode ser usada em conjunto com o parâmetro periodicosNuncaRealizados.

        periodicosNuncaRealizados: Se habilitado, serão exibidos também os\ 
        exames periódicos do funcionário que nunca foram realizados.\
        Essa opção não pode ser usada em conjunto com parâmetro nuncaRealizados

        selecao: Informe 1 ou 2, sendo: 1 = "Exames não realizados do período +\ 
        exames em atraso (meses anteriores)" 2 = "Exames do período +\ 
        exames em atraso (meses anteriores)"

        examesPendentes: Se habilitado, contemplará os exames que estão associados a\
        um Pedido de Exames, porém não possuem data de resultado.
        
        convocaPendentesPCMSO: Se habilitado, serão exibidos apenas os exames do PCMSO\ 
        que não possuem data de resultado. Considerase exames do PCMSO os exames que\ 
        estão aplicados ao funcionário, seja através de Risco - Exame,\ 
        Aplicação de Exames ou GHE. Considera-se exames fora do PCMSO\ 
        os exames pedidos através da tela "248 - Pedido de Exames"\ 
        e que não estão aplicados ao funcionário.
        '''
        parametro = {
            "empresa":cod_empresa,
            "unidade":cod_unidade,
            "setor":cod_setor,
            "turno":cod_turno,
            "periodo":periodo,
            "exame":cod_exame,
            "convocarClinico":convocar_clinico,
            "nuncaRealizados":nunca_realizados,
            "periodicosNuncaRealizados":periodicos_nunca_realizados,
            "selecao":selecao,
            "examesPendentes":exames_pendentes,
            "convocaPendentesPCMSO":conv_pendentes_pcmso
        }
        return parametro

    def consulta_conv_exames_assync(
        cod_empresa_principal: int,
        cod_exporta_dados: int,
        chave: str,
        cod_empresa_trab: int,
        cod_sol: int
    ):
        '''Consultar resultado da solicitacao assync'''
        parametro = {
            'empresa':cod_empresa_principal,
            'codigo':cod_exporta_dados,
            'chave':chave,
            'tipoSaida':'json',
            'empresaTrabalho':cod_empresa_trab,
            'codigoSolicitacao':cod_sol
        }
        print(parametro)
        return parametro

    def cadastro_pessoas_usuarios(
        empresa: int,
        codigo: int,
        chave: str,
        ativo: int = 1,
        tipoSaida: str = 'json'
    ):
        '''
            Cadastro Pessoa/Usuarios

            Exporta Dados com a finalidade de listar algumas informações de \
            todos os Usuários e Pessoas cadastrados na Empresa Principal.

            Campos: EMPRESA, CODIGO, NOME, EMAIL, TIPO, AVALIADOR, SOLICITANTE, EXAMINADOR, \
            RESPONSAVEL, GERENTE_CONTAS, PROFISSIONAL_AGENDA, EMISSOR_ASO, TELEFONE_COM, ATIVO, \
            ENDERECO ,COMPLEMENTO, BAIRRO, CIDADE, UF, CEP, RG, CPF NIT, CONSELHO_CLASSE, UF_CONSELHO, \
            ESPECIALIDADE1, ESPECIALIDADE2, CD_USUARIO, USUARIO_ATIVO, TODAS_EMPRESAS,
            CNS, PAI, MAE, OCUPACAO, CARGO, FORMACAO_PROFISSIONAL, TIPO_VINCULO, ESCOLARIDADE, \
            REGISTRO_FUNCIONAL, DATA_NASCIMENTO, DATA_CONTRATACAO, SEXO, HORARIO_INICIAL_TRABALHO, \
            HORARIO_FINAL_TRABALHO, FREQUENTA_ESCOLA, BANCO, CONTA, AGENCIA, \
            COMO_EXIBIR_COMPROMISSO_OUTROS_USUARIOS, COMO_EXIBIR_COMPROMISSO_OUTRAS_EMPRESAS.

            Observações:
            1. Para os campos que levam a resposta como "1" e "0", considere "1" como "Sim" e "0" como "Não".
            Campos que utilizam esta resposta: 
        '''

        param = {
            'empresa': empresa,
            'codigo': codigo,
            'chave': chave,
            'tipoSaida': tipoSaida,
            'ativo': ativo
        }
        
        return param

    def cargos(
        self,
        empresa: int,
        codigo: int,
        chave: str,
        tipoSaida: str = 'json'
    ) -> str:
        '''
            Cadastro de Cargos (todas empresas)

            Descrição: Este Exporta Dados é listado todos os \
            cadastros de Cargos de todas as Empresas.
            Campos: CODIGOEMPRESA, NOMEEMPRESA, CODIGOCARGO, \
            NOMECARGO, CODIGORHCARGO, CARGOATIVO, FUNCAO, GFIP, \
            DESCRICAODETALHADA, CBO.

            Exportar a relação de todos os cargos de todas \
            as empresas
        '''

        param = {
            'empresa': empresa,
            'codigo': codigo,
            'chave': chave ,
            'tipoSaida': tipoSaida
        }

        return self.__processar_parametro(param=param)

    def mandato_cipa(
        self,
        empresa: int,
        codigo: int,
        chave: str,
        dataInicio: date,
        dataFim: date,
        ativo: bool,
        tipoSaida: str = 'json'
    ):
        '''
            Esse exporta dados exibe os dados dos mandatos da empresa.

            Parâmetros de entrada:

            - empresa: Tipo: Numérico (8)
            - dataInicio: Tipo: Data
            - dataFim: Tipo: Data
            - ativo: Tipo: Numérico (8); Obs.: Valores possíveis: 1 - Ativo e 2 - Inativo.

            - Obs: dataInicio e dataFim maximo de 1 ano (365 dias)

            Campos de saída:
            CODIGOEMPRESA: Tipo: numérico (8), NOMEEMPRESA: Tipo: alfanumérico (200),
            CODIGOUNIDADE: Tipo: alfanumérico (20), NOMEUNIDADE: Tipo: alfanumérico (130),
            CODIGOSETOR: Tipo: alfanumérico (10), NOMESETOR: Tipo: alfanumérico (130),
            CODIGOMANDATO: Tipo: numérico (8), CODIGOFUNCIONARIO: Tipo: numérico (20),
            MATRICULA: Tipo: alfanumérico (30), NOMEFUNCIONARIO: Tipo: alfanumérico (120),
            APELIDO: Tipo: alfanumérico (60), CPF: Tipo: alfanumérico (19),
            DATAINICIOMANDATO: Tipo: data (10), DATAFIMMANDATO: Tipo: data (10),
            DATACANDIDATURA: Tipo: data (10), TIPOESTABILIDADE: Tipo: alfanumérico (1),
            FUNCIONARIOELEITO: Tipo: alfanumérico (3), TIPOREPRESENTACAO: Tipo: alfanumérico (10),
            FUNCAO: Tipo: alfanumérico (80), TIPOSITUACAO: Tipo: alfanumérico (9),
            DATAINICIOELEITORAL: Tipo: data (10), DATAINICIOPROCESSO: Tipo: data (10),
            DATAINICIALINSCRICAO: Tipo: data (10), DATAFINALINSCRICAO: Tipo: data (10),
            DATAELEICAOCIPA: Tipo: data (10), DATAPRORROGACAO: Tipo: data (10),
            RENUNCIADO: Tipo: alfanumérico (3), DATAESTABILIDADEFUNCIONARIO: Tipo: data (10),
            DSESTABILIDADE: Tipo: alfanumérico (1000)
        '''

        param = {
            'empresa': empresa,
            'codigo': codigo,
            'chave': chave,
            'tipoSaida': tipoSaida,
            'dataInicio': dataInicio,
            'dataFim': dataFim,
            'ativo': ativo
        }

        return self.__processar_parametro(param=param)

