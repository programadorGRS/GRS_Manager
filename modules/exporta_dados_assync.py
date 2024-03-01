import datetime

import zeep
from zeep.helpers import serialize_object
from zeep.wsse.username import UsernameToken
from zeep.wsse.utils import WSU

from modules.exporta_dados import get_json_configs, json_config_path

# comando para ler WSDL no terminal
# python -mzeep https://ws1.soc.com.br/WSSoc/ProcessamentoAssincronoWs?wsdl


# configs
wsdl_url  = get_json_configs(json_config_path)['PROC_ASSYNC_WSDL_URL']
service_url = get_json_configs(json_config_path)['PROC_ASSYNC_SERVICE_URL']
username = get_json_configs(json_config_path)['PROC_ASSYNC_USERNAME']
password = get_json_configs(json_config_path)['PROC_ASSYNC_PASSWORD']


def timestamp_utc() -> WSU.Timestamp:
    '''
    Cria instancia de WSU.Timestamp()

    WSU.Created: utc.now

    WSU.Expires: + timedelta 10 mins
    '''
    # criar instancia do Timestamp zeep
    timestamp_token = WSU.Timestamp()
    # usar horario UTC-0
    today_datetime = datetime.datetime.utcnow()
    expires_datetime = today_datetime + datetime.timedelta(minutes=10)
    timestamp_elements = [
        WSU.Created(today_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")),
        WSU.Expires(expires_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"))
    ]
    timestamp_token.extend(timestamp_elements)
    return timestamp_token


def requestPedidoProcessamentoSOC(
        UsernameToken_username: str='423',
        UsernameToken_password: str=None,
        identificacaoUsuarioWsVo_codigoEmpresaPrincipal: str='423',
        identificacaoUsuarioWsVo_codigoResponsavel: str='213',
        identificacaoUsuarioWsVo_codigoUsuario: str='1797850',
        processamentoAssincronoWsVo_codigoEmpresa: str=None,
        processamentoAssincronoWsVo_tipoProcessamento: str='8',
        processamentoAssincronoWsVo_parametros: str=None

    ) -> dict:
    '''
    Realiza pedido de processamento no SOC

    Apos realizado, o pedido pode ser visto em 
    Menu > Administração > Pedido de Processamento, no usuario Webservice GRS - Teste

    UsernameToken:
    
    - Username: Código da empresa principal no sistema SOC.
    - Password: Chave de acesso da empresa (disponível nas configurações de integração).
    Contudo o cliente deverá informar o mesmo com o Tipo PasswordDigest

    identificacaoUsuarioWsVo:

    - codigoUsuario: Código de identificação do usuário responsável pela ação

    Retorna OrderedDict
    '''
    # instanciar client usando UsernameToken
    # (com password digest, cria nonce e digest sozinho, vide metodos da classe UsernameToken)
    timestamp=timestamp_utc()

    # criar tags no xml baseadas nas tags do WSDL

    # UsernameToken
    client = zeep.Client(
        wsdl=wsdl_url,
        wsse=UsernameToken(
            # Código da empresa principal no sistema SOC.
            username=UsernameToken_username,
            # Chave de acesso da empresa (disponível nas configurações de integração).
            password=UsernameToken_password,
            use_digest=True,
            timestamp_token=timestamp
        )
    )

    # identificacaoUsuarioWsVo
    factory = client.type_factory('ns0')
    identificacao = factory.identificacaoUsuarioWsVo(
        codigoEmpresaPrincipal=identificacaoUsuarioWsVo_codigoEmpresaPrincipal,
        codigoResponsavel=identificacaoUsuarioWsVo_codigoResponsavel,
        # Código de identificação do usuário responsável pela ação: Webservice - Manager
        codigoUsuario=identificacaoUsuarioWsVo_codigoUsuario
    )

    # processamentoAssincronoWsVo
    proc_assinc = factory.processamentoAssincronoWsVo(
        codigoEmpresa=processamentoAssincronoWsVo_codigoEmpresa,
        identificacaoWsVo=identificacao,
        tipoProcessamento=processamentoAssincronoWsVo_tipoProcessamento,
        parametros=str(processamentoAssincronoWsVo_parametros)
    )

    # realizar request
    request = client.service.incluirSolicitacao(ProcessamentoAssincronoWsVo=proc_assinc)
    return serialize_object(request) # retorna orderedDict


# PARAMETROS--------------------------------------------------------
def param_sol_conv_exames_assync(
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


def param_consulta_conv_exames_assync(
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