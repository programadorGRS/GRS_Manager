import json

import pandas as pd
import requests
import xmltodict

json_config_path = 'configs/exporta_dados_grs.json'

def get_json_configs(json_path: str) -> dict:
    '''
    Le o arquivo json de configuracao e retorna um dicionario
    
    Retorna dicionario de configs
    '''
    with open(json_path, mode='r', encoding='iso-8859-1') as f:
        data = json.loads(f.read())
    return dict(data)


# FUNCOES
def request(parametro: str, encoding: str='ISO-8859-1') -> str:
    '''
    Realiza o request para o webservice do SOC
    
    Retorna a resposta xml em string
    '''
    url = get_json_configs(json_config_path)['EXPORTADADOS_URL']
    # headers = {'content-type': 'text/xml'}
    headers = {'content-type': 'application/soap+xml'}
    body = f"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
    xmlns:ser="http://services.soc.age.com/">
     <soapenv:Header/>
     <soapenv:Body>
     <ser:exportaDadosWs>
     <arg0>
     <parametros>{parametro}</parametros>
     </arg0>
     </ser:exportaDadosWs>
     </soapenv:Body>
    </soapenv:Envelope>"""
    # print('Enviando request...')
    resposta = requests.post(url, data=body, headers=headers)
    conteudo = resposta.content
    conteudo = conteudo.decode(encoding) # encoding usado pelos retornos do SOC
    return conteudo


def retorno_dict(xml_string: str) -> dict:
    '''Obtem a resposta dentro do xml (msg de erro ou retorno)'''
    # transformar o string xml em OrderedDict
    # print('Transformando em dicionário...')
    dic = xmltodict.parse(xml_string)
    # pegar erro True ou False
    erro = dic['soap:Envelope']['soap:Body']['ns2:exportaDadosWsResponse']['return']['erro']
    if erro == 'true':
        msg_erro = dic['soap:Envelope']['soap:Body']['ns2:exportaDadosWsResponse']['return']['mensagemErro']
        resposta = {'erro': erro, 'mensagem_erro': msg_erro}
        return resposta
    else:
        # pegar conteudo do retorno dentro do xml
        retorno = dic['soap:Envelope']['soap:Body']['ns2:exportaDadosWsResponse']['return']['retorno']
        resposta = {'erro': erro, 'retorno': retorno}
        return resposta


def criar_df(dict_xml: str) -> pd.DataFrame:
    '''Cria dataframe a partir do OrderedDict xml'''
    # transformar o dict em json
    # print('Criando Json...')
    arqv_json = json.loads(dict_xml)
    # transformar o json em DataFrame
    # print('Criando DataFrame...')
    df = pd.DataFrame(data=arqv_json)
    return df


def exporta_dados(parametro: str, encoding: str='ISO-8859-1') -> pd.DataFrame:
    '''
    Executa todas as funcoes de para retornar um DataFrame a partir do Request.

    Ordem de execução:
   - request(parametro)
   - retorno_dict(request)
   - criar_df(retorno_dict)

    Retorna DataFrame ou DataFrame vazio e printa msg de erro
    '''
    # print('Carregando...')
    dic = retorno_dict(request(parametro, encoding))
    if dic['erro'] == 'true':
        print(f"ERRO: {dic['mensagem_erro']}, param: {parametro}")
        return pd.DataFrame()
    else:
        # print('Concluído!')
        df = criar_df(dic['retorno'])
        return df


# PARAMETROS------------------------------------------------------------------------
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


def pedido_exame(
    empresa: int,
    cod_exporta_dados: int,
    chave: str,
    dataInicio: str,
    dataFim: str,
    tipoSaida: str = 'json',
    paramData: int = 1,
    paramSequencial: int = 0,
    sequenciaFicha: int = '',
    funcionarioInicio: int = 0,
    funcionarioFim: int = 999999999,
    paramFunc: int = 0,
    cpffuncionario: str = '',
    nomefuncionario: str = '',
    codpresta: int = '',
    nomepresta: str = '',
    paramPresta: int = 0,
    codunidade: int = '',
    nomeunidade: str = '',
    paramUnidade: int = 0
    ) -> dict:
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

    Obs: 'empresa' e o cod da empresa dos pedidos de exame, nao e o cod da EmpresaPrincipal
    '''

    parametro = {
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

