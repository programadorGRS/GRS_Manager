import json
from datetime import datetime, timedelta

import pandas as pd
import requests
import xmltodict
import zeep
from zeep.settings import Settings
from zeep.wsse.username import UsernameToken
from zeep.wsse.utils import WSU

from src.extensions import database


class ExportaDadosWS(database.Model):
    """
        Tabela para registrar Requests e Responses do Web Service \
        Exporta Dados do SOC.

        Obs: registrar response_text apenas se o Retorno for um ERRO do SOC, \
        nao do Request

        erro_soc: é quando um request esta OK, mas a operacao \
        nao foi realizada por algum erro interno do SOC ou por erros \
        nos parametros do Request.

        msg_erro: msg de erro do soc
    """
    __tablename__ = 'ExportaDadosWS'

    id = database.Column(database.Integer, primary_key=True)
    request_method = database.Column(database.String(20), nullable=False)
    request_url = database.Column(database.String(255), nullable=False)
    request_body = database.Column(database.String(2000))
    response_status = database.Column(database.Integer)
    response_text = database.Column(database.String(2000))

    parametros = database.Column(database.String(2000), nullable=False)
    erro_soc = database.Column(database.Boolean, nullable=False)
    msg_erro = database.Column(database.String(255))

    request_date = database.Column(database.DateTime, nullable=False)

    id_empresa = database.Column(database.Integer)
    obs = database.Column(database.String(255))

    WSDL_URL: str = 'https://ws1.soc.com.br/WSSoc/ProcessamentoAssincronoWs?wsdl'
    PROC_ASSINC_URL: str = 'https://ws1.soc.com.br/WSSoc/ProcessamentoAssincronoWs'
    EXPORTA_DADOS_URL: str = 'https://ws1.soc.com.br/WSSoc/services/ExportaDadosWs'
    EXPORTA_DADOS_URL_POST: str = 'https://ws1.soc.com.br/WebSoc/exportadados'
    # corpo padrao dos Requests para Exporta Dados
    EXPORTA_DADOS_XML_PATH: str = 'src/exporta_dados.xml'

    def __repr__(self) -> str:
        return f'<{self.id}> {self.request_method} - {self.response_status}'

    @classmethod
    def request_exporta_dados_ws(
        self,
        parametro: dict,
        url: str = EXPORTA_DADOS_URL,
        xml_path: str = EXPORTA_DADOS_XML_PATH,
        encoding: str = 'ISO-8859-1'
    ) -> dict[str, any]:
        """
        Realiza Request para o Servico Exporta Dados do SOC.

        Args:
            xml_path (str, optional): caminho do arquivo xml \
            que contem o corpo do request. \
            Defaults to 'configs/ExportaDadosWs.xml'.

        Returns:
            dict[str, any]: {
                'response': requests.Response,
                'erro_soc': bool,
                'msg_erro': str | None
            }
        """

        response = self.SOAP_request(
            parametro=parametro,
            url=url,
            xml_path=xml_path,
            encoding=encoding
        )

        retorno = {
            'response': response,
            'erro_soc': False,
            'msg_erro': None
        }

        if response.status_code != 200:
            return retorno

        response_dict: dict = xmltodict.parse(response.text)

        erro_soc: str = response_dict['soap:Envelope']['soap:Body']\
        ['ns2:exportaDadosWsResponse']['return']['erro']

        if erro_soc == 'true':
            msg_erro: str = response_dict['soap:Envelope']['soap:Body']\
            ['ns2:exportaDadosWsResponse']['return']['mensagemErro']

            retorno['erro_soc'] = True
            retorno['msg_erro'] = msg_erro

        return retorno

    @staticmethod
    def SOAP_request(
        parametro: dict,
        url: str = EXPORTA_DADOS_URL,
        xml_path: str = EXPORTA_DADOS_XML_PATH,
        encoding: str = 'ISO-8859-1'
    ) -> requests.Response:
        """
            Envia POST request para o WebService Exporta Dados do SOC \
            e retorna a Response.
            
            Padrao SOAP
            
            Obs: manter o xml armazenado como str de uma unica linha para \
            evitar newline characters
        """
        headers: dict = {'content-type': 'application/soap+xml'}

        with open(xml_path, mode='r', encoding=encoding) as f:
            body: str = f.read()

        body = body.replace(
            'placeholder_parametro',
            str(parametro).replace('\'', '"')
        )

        return requests.post(url, data=body, headers=headers)

    @classmethod
    def request_ped_proc_assync(
        self,
        username: str,
        password: str,
        codigoEmpresaPrincipal: str,
        codigoResponsavel: str,
        codigoUsuario: str,
        codigoEmpresa: str,
        parametros: dict,
        tipoProcessamento: str = '8'
    ) -> dict[str, any]:
        """Realiza request para o servico processamentoAssincronoWsVo do SOC.

        Returns:
            dict[str, any]: {
                'response': requests.Response,
                'erro_soc': bool,
                'msg_erro': str | None,
                'cod_solicitacao': int | None
            }
        """

        response = self.SOAP_request_ped_proc_assync(
            username=username,
            password=password,
            codigoEmpresaPrincipal=codigoEmpresaPrincipal,
            codigoResponsavel=codigoResponsavel,
            codigoUsuario=codigoUsuario,
            codigoEmpresa=codigoEmpresa,
            parametros=parametros,
            tipoProcessamento=tipoProcessamento
        )

        retorno = {
            'response': response,
            'erro_soc': False,
            'msg_erro': None,
            'cod_solicitacao': None
        }

        if response.status_code != 200:
            return retorno

        response_dict: dict = xmltodict.parse(response.text)

        cod_msg_soc: str = response_dict['soap:Envelope']['soap:Body']\
        ['ns2:incluirSolicitacaoResponse']['ProcessamentoAssincronoRetorno']\
        ['informacaoGeral']['codigoMensagem']

        if cod_msg_soc != 'SOC-100':
            msg_erro: str = response_dict['soap:Envelope']['soap:Body']\
            ['ns2:incluirSolicitacaoResponse']['ProcessamentoAssincronoRetorno']\
            ['informacaoGeral']['mensagemOperacaoDetalheList']['mensagem']

            retorno['erro_soc'] = True
            retorno['msg_erro'] = msg_erro

            return retorno

        cod_solicitacao: str = response_dict['soap:Envelope']['soap:Body']\
        ['ns2:incluirSolicitacaoResponse']['ProcessamentoAssincronoRetorno']\
        ['codigoSolicitacao']

        retorno['cod_solicitacao'] = int(cod_solicitacao)

        return retorno

    @classmethod
    def SOAP_request_ped_proc_assync(
            self,
            username: str,
            password: str,
            codigoEmpresaPrincipal: str,
            codigoResponsavel: str,
            codigoUsuario: str,
            codigoEmpresa: str,
            parametros: dict,
            tipoProcessamento: str = '8',
        ) -> requests.Response:
        '''
            Realiza request para pedido de processamento no SOC

            Apos realizado, o pedido pode ser visto em \
            Menu > Administração > Pedido de Processamento, no usuario "Webservice GRS"

            UsernameToken:
                - username: Código da Empresa Principal no sistema SOC.
                - password: Chave de acesso da Empresa (disponível nas configurações de integração). \
                Deve ser passado como PasswordDigest.

            identificacaoUsuarioWsVo:
                - codigoUsuario: Código de identificação do usuário responsável pela ação \
                (usuário de Web service do SOC)

            tipoProcessamento: vide manual de processamento assincrono do SOC

            Retorna requests.Response
        '''
        # NOTE: use_digest=True, cria nonce e digest sozinho, \
        # vide metodos da classe UsernameToken
        username_token = UsernameToken(
            username=username,
            password=password,
            use_digest=True,
            timestamp_token=self.timestamp_utc()
        )

        # NOTE: raw response: faz com que a Response seja requests.Response\
        # em vez de uma Response do Zeep
        conf = Settings(raw_response=True)

        client = zeep.Client(
            wsdl=self.WSDL_URL,
            wsse=username_token,
            settings=conf
        )

        # NOTE: NÃO remover o namespace
        factory = client.type_factory(namespace='ns0')

        identificacao = factory.identificacaoUsuarioWsVo(
            codigoEmpresaPrincipal=codigoEmpresaPrincipal,
            codigoResponsavel=codigoResponsavel,
            codigoUsuario=codigoUsuario
        )

        proc_assinc = factory.processamentoAssincronoWsVo(
            codigoEmpresa=codigoEmpresa,
            identificacaoWsVo=identificacao,
            tipoProcessamento=tipoProcessamento,
            parametros=str(parametros)
        )

        return client.service.incluirSolicitacao(ProcessamentoAssincronoWsVo=proc_assinc)

    @staticmethod
    def timestamp_utc():
        '''
        Cria instancia de WSU.Timestamp()

        WSU.Created: utc.now

        WSU.Expires: + timedelta 10 mins
        '''
        # criar instancia do Timestamp zeep
        timestamp_token = WSU.Timestamp()
        # usar horario UTC-0
        today_datetime = datetime.utcnow()
        expires_datetime = today_datetime + timedelta(minutes=10)
        timestamp_elements = [
            WSU.Created(today_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")),
            WSU.Expires(expires_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"))
        ]
        timestamp_token.extend(timestamp_elements)
        return timestamp_token

    @staticmethod
    def xml_to_dataframe(xml_string: str) -> pd.DataFrame:
        """Recebe corpo do Response de Exporta Dados e retorna \
        DataFrame contido na tag 'retorno'
        """
        xml_dic = xmltodict.parse(xml_string)
        dados = json.loads(
            xml_dic['soap:Envelope']['soap:Body']\
                ['ns2:exportaDadosWsResponse']['return']['retorno']
        )
        return pd.DataFrame(data=dados)

    # PARAMETROS ----------------------------------------------------------------
    @staticmethod
    def pedido_exame(
        empresa: int,
        cod_exporta_dados: int,
        chave: str,
        dataInicio: str,
        dataFim: str,
        tipoSaida: str = 'json',
        paramData: int = 1,
        paramSequencial: int = 0,
        sequenciaFicha: int | str = '',
        funcionarioInicio: int = 0,
        funcionarioFim: int = 999999999,
        paramFunc: int | str = 0,
        cpffuncionario: str = '',
        nomefuncionario: str = '',
        codpresta: int | str = '',
        nomepresta: str = '',
        paramPresta: int | str = 0,
        codunidade: int | str = '',
        nomeunidade: str = '',
        paramUnidade: int | str = 0
    ) -> dict[str, any]:
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

        parametro: dict = {
            'empresa':empresa,
            'codigo':cod_exporta_dados,
            'chave':chave,
            'tipoSaida':tipoSaida,
            'paramSequencial':paramSequencial,
            'sequenciaFicha':sequenciaFicha,
            'funcionarioInicio':funcionarioInicio,
            'funcionarioFim':funcionarioFim,
            'paramData':paramData,
            'dataInicio':dataInicio,
            'dataFim':dataFim,
            'paramFunc':paramFunc,
            'cpffuncionario':cpffuncionario,
            'nomefuncionario':nomefuncionario,
            'codpresta':codpresta,
            'nomepresta':nomepresta,
            'paramPresta':paramPresta,
            'codunidade':codunidade,
            'nomeunidade':nomeunidade,
            'paramUnidade':paramUnidade
        }

        return parametro

    @staticmethod
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

    @staticmethod
    def unidades(
        empresa_principal: int,
        cod_exporta_dados: int,
        chave: str,
        ativo: int = '',
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
        parametro = {
            'empresa':empresa_principal,
            'codigo':cod_exporta_dados,
            'chave':chave,
            'tipoSaida':tipoSaida,
            'ativo':ativo
        }
        return parametro

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def cadastro_funcionarios(
        cod_empresa_principal: int,
        cod_exporta_dados: int,
        chave: str,
        empresaTrabalho: int,
        parametroData: int = 0,
        dataInicio: str = '',
        dataFim: str = '',
        cpf: str = '',
        tipoSaida: str = 'json'
    ):
        '''
        Cadastro de Funcionarios (Por Empresa)

        Dependendo da Empresa que estiver sendo acessado, este Exporta Dados \
        irá listar todos os Funcionários que estão cadastrados na Empresa Logada. \
        Será trazido todos os Funcionários, não importando sua situação.
        '''
        par = {
            'empresa':cod_empresa_principal,
            'codigo':cod_exporta_dados,
            'chave':chave,
            'tipoSaida':tipoSaida,
            'empresaTrabalho':empresaTrabalho,
            'cpf':cpf,
            'parametroData':parametroData,
            'dataInicio':dataInicio,
            'dataFim':dataFim
            }
        
        return par

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def cargos(
        empresa: int,
        codigo: int,
        chave: str,
        tipoSaida: str = 'json'
    ):
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

        return param

