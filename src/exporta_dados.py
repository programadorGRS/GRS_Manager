import json
import re
from datetime import datetime, timedelta

import pandas as pd
import requests
import xmltodict
import zeep
from zeep.settings import Settings
from zeep.wsse.username import UsernameToken
from zeep.wsse.utils import WSU

from src import TIMEZONE_SAO_PAULO, database


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


    # EXPORTA DADOS WS ------------------------------------------------------------
    @classmethod
    def request_exporta_dados_ws(
        self,
        parametro: dict,
        url: str = EXPORTA_DADOS_URL,
        xml_path: str = EXPORTA_DADOS_XML_PATH,
        encoding: str = 'ISO-8859-1',
        id_empresa: int | None = None,
        obs: str | None = None
    ) -> dict[str, any] :
        """
        Realiza Request para o Servico Exporta Dados do SOC. \
        Registra Request e Response na database.

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

        # redigir parametros
        if parametro['chave']:
            parametro['chave'] = 'REDACTED'

        exporta_dados = self(
            request_method = response.request.method,
            request_url = response.request.url,
            request_body = self.redact_parametros(response.request.body).replace('\'', '"'),
            response_status = response.status_code,
            parametros = str(parametro),
            erro_soc = False,
            request_date = datetime.now(tz=TIMEZONE_SAO_PAULO),
            id_empresa = id_empresa,
            obs = obs
        )

        if response.status_code == 200: # REQUEST OK
            response_dic: dict = xmltodict.parse(response.text)
            
            # registrar response.text apenas em caso de erros do SOC
            erro_soc = response_dic['soap:Envelope']['soap:Body']\
            ['ns2:exportaDadosWsResponse']['return']['erro']
            
            if erro_soc == 'true': # ERRO SOC
                msg_erro: str = response_dic['soap:Envelope']['soap:Body']\
                ['ns2:exportaDadosWsResponse']['return']['mensagemErro']

                exporta_dados.response_text = self.redact_parametros(response.text).replace('\'', '"')
                exporta_dados.erro_soc = True
                exporta_dados.msg_erro = msg_erro

                retorno['erro_soc'] = True
                retorno['msg_erro'] = msg_erro
        else: # ERRO REQUEST
            exporta_dados.response_text = response.text

        database.session.add(exporta_dados)
        database.session.commit()

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


    # PROCESSAMENTO ASSINCRONO WS ----------------------------------------------------
    @classmethod
    def request_pedido_processameto_assincrono(
        self,
        UsernameToken_username: str,
        UsernameToken_password: str,
        identificacaoUsuarioWsVo_codigoEmpresaPrincipal: str,
        identificacaoUsuarioWsVo_codigoResponsavel: str,
        identificacaoUsuarioWsVo_codigoUsuario: str,
        processamentoAssincronoWsVo_codigoEmpresa: str,
        processamentoAssincronoWsVo_parametros: dict,
        processamentoAssincronoWsVo_tipoProcessamento: str = '8'
    ) -> dict[str, any]:
        """Realiza request para o servico processamentoAssincronoWsVo do SOC. \
        Registra o request na database. Registra response caso haja erro no request ou no SOC.

        Returns:
            dict[str, any]: {
                'response': requests.Response,
                'erro_soc': bool,
                'msg_erro': str | None,
                'cod_solicitacao': int | None
            }
        """

        response = self.SOAP_request_pedido_processamento(
            UsernameToken_username=UsernameToken_username,
            UsernameToken_password=UsernameToken_password,
            identificacaoUsuarioWsVo_codigoEmpresaPrincipal=identificacaoUsuarioWsVo_codigoEmpresaPrincipal,
            identificacaoUsuarioWsVo_codigoResponsavel=identificacaoUsuarioWsVo_codigoResponsavel,
            identificacaoUsuarioWsVo_codigoUsuario=identificacaoUsuarioWsVo_codigoUsuario,
            processamentoAssincronoWsVo_codigoEmpresa=processamentoAssincronoWsVo_codigoEmpresa,
            processamentoAssincronoWsVo_parametros=processamentoAssincronoWsVo_parametros,
            processamentoAssincronoWsVo_tipoProcessamento=processamentoAssincronoWsVo_tipoProcessamento
        )

        retorno = {
            'response': response,
            'erro_soc': False,
            'msg_erro': None,
            'cod_solicitacao': None
        }

        # registrar response.text apenas em caso de erros
        exporta_dados = self(
            request_method = response.request.method,
            request_url = response.request.url,
            request_body = self.redact_UsernameToken(response.request.body).replace('\'', '"'),
            response_status = response.status_code,
            parametros = str(processamentoAssincronoWsVo_parametros),
            erro_soc = False,
            request_date = datetime.now(tz=TIMEZONE_SAO_PAULO)
        )

        if response.status_code == 200: # REQUEST OK
            response_dic: dict = xmltodict.parse(response.text)
            
            cod_msg_soc: str = response_dic['soap:Envelope']['soap:Body']\
            ['ns2:incluirSolicitacaoResponse']['ProcessamentoAssincronoRetorno']\
            ['informacaoGeral']['codigoMensagem']
            
            if cod_msg_soc != 'SOC-100': # ERRO SOC
                msg_erro: str = response_dic['soap:Envelope']['soap:Body']\
                ['ns2:incluirSolicitacaoResponse']['ProcessamentoAssincronoRetorno']\
                ['informacaoGeral']['mensagemOperacaoDetalheList']['mensagem']

                exporta_dados.response_text = response.text
                exporta_dados.erro_soc = True
                exporta_dados.msg_erro = msg_erro

                retorno['erro_soc'] = True
                retorno['msg_erro'] = msg_erro
            else: # SOC OK
                retorno['cod_solicitacao'] = int(response_dic['soap:Envelope']['soap:Body']\
                ['ns2:incluirSolicitacaoResponse']['ProcessamentoAssincronoRetorno']\
                ['codigoSolicitacao'])
        else: # ERRO REQUEST
            exporta_dados.response_text = response.text

        database.session.add(exporta_dados)
        database.session.commit()

        return retorno

    @classmethod
    def SOAP_request_pedido_processamento(
            self,
            UsernameToken_username: str,
            UsernameToken_password: str,
            identificacaoUsuarioWsVo_codigoEmpresaPrincipal: str,
            identificacaoUsuarioWsVo_codigoResponsavel: str,
            identificacaoUsuarioWsVo_codigoUsuario: str,
            processamentoAssincronoWsVo_codigoEmpresa: str,
            processamentoAssincronoWsVo_parametros: dict,
            processamentoAssincronoWsVo_tipoProcessamento: str = '8',
        ) -> requests.Response:
        '''
        Realiza request para pedido de processamento no SOC

        Apos realizado, o pedido pode ser visto em 
        Menu > Administração > Pedido de Processamento, no usuario Webservice GRS - Teste

        UsernameToken:
        
        - Username: Código da empresa principal no sistema SOC.
        - Password: Chave de acesso da empresa (disponível nas configurações de integração).
        Contudo o cliente deverá informar o mesmo com o Tipo PasswordDigest

        identificacaoUsuarioWsVo:

        - codigoUsuario: Código de identificação do usuário responsável pela ação

        tipoProcessamento: vide manual de processamento assincrono do SOC

        Retorna requests.Response
        '''
        # password digest = True, cria nonce e digest sozinho, vide metodos da classe UsernameToken
        client = zeep.Client(
            wsdl = self.WSDL_URL,
            wsse = UsernameToken(
                # Código da empresa principal no sistema SOC.
                username = UsernameToken_username,
                # Chave de acesso da empresa (disponível nas configurações de integração).
                password = UsernameToken_password,
                use_digest = True,
                timestamp_token = self.timestamp_utc()
            ),
            settings=Settings(raw_response = True)
            # raw response: faz com que a Response seja requests.Response\
            # em vez de uma Response do Zeep 
        )

        factory = client.type_factory('ns0')

        # identificacaoUsuarioWsVo
        identificacao = factory.identificacaoUsuarioWsVo(
            codigoEmpresaPrincipal = identificacaoUsuarioWsVo_codigoEmpresaPrincipal,
            codigoResponsavel = identificacaoUsuarioWsVo_codigoResponsavel,
            # Código de identificação do usuário responsável pela ação: Webservice - Manager
            codigoUsuario = identificacaoUsuarioWsVo_codigoUsuario
        )

        # processamentoAssincronoWsVo
        proc_assinc = factory.processamentoAssincronoWsVo(
            codigoEmpresa = processamentoAssincronoWsVo_codigoEmpresa,
            identificacaoWsVo = identificacao,
            tipoProcessamento = processamentoAssincronoWsVo_tipoProcessamento,
            parametros = str(processamentoAssincronoWsVo_parametros)
        )

        # realizar request
        return client.service.incluirSolicitacao(ProcessamentoAssincronoWsVo = proc_assinc)

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


    # UTILS ----------------------------------------------------------------------
    @staticmethod
    def redact_parametros(xml_string: str) -> str:
        """
        Recebe corpo do Request/Response de Exporta Dados e redige \
        o item 'chave' dos parametros
        """
        param = re.search("{(.*)}", xml_string)
        param = param.group()
        
        param = param.replace('True', 'true')
        param = param.replace('False', 'false')
        
        param = json.loads(param)

        if param['chave']:
            param['chave'] = 'REDACTED'

        xml_string = re.sub(
            pattern = "{(.*)}",
            repl = str(param),
            string = xml_string,
            flags = re.DOTALL # re.DOTALL : to match across all lines
        )

        return xml_string

    @staticmethod
    def redact_UsernameToken(xml_string: str) -> str:
        '''
        Recebe corpo do Request de Processamento Assincrono \
        e redige o campo UsernameToken
        '''
        xml_string: dict = xmltodict.parse(xml_string)

        if xml_string['soap-env:Envelope']['soap-env:Header']['wsse:Security']\
        ['wsse:UsernameToken']:
            xml_string['soap-env:Envelope']['soap-env:Header']['wsse:Security']\
            ['wsse:UsernameToken'] = 'REDACTED'

        return xmltodict.unparse(xml_string)

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
        return parametro

