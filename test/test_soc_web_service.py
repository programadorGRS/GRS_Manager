from src.soc_web_service.soc_web_service import SOCWebService
from src.soc_web_service.modelo_2 import Modelo2
from src.soc_web_service.exporta_dados import ExportaDados
from datetime import date


def test_get_client():
    ws = SOCWebService()
    client = ws.get_client(wsdl_url=ws.CONFIGS.get('WSDL_MODELO_2_TESTE'))

def test_service():
    ws = SOCWebService()

    client = ws.get_client(
        wsdl_url=ws.CONFIGS.get('WSDL_MODELO_2_TESTE'),
        raw_response=True
    )

    resp = client.service.importacaoFuncionario()

    assert resp.status_code == 500
    assert 'ERRO DESCONHECIDO' in resp.text

def test_import_funcionario():
    COD_EMPRESA = 268104 # empresa: BASE TREINAMENTO NUCLEO
    COD_FUNCIONARIO = 177 # funcionario: Teste1

    ws = SOCWebService()

    client = ws.get_client(wsdl_url=ws.CONFIGS.get('WSDL_MODELO_2_TESTE'))
    factory=client.type_factory('ns0')

    modelo2 = Modelo2(factory=factory)

    funcionario = modelo2.Funcionario()

    modelo2.config_criacoes(funcionario=funcionario)
    modelo2.config_atualizacoes(funcionario=funcionario, atualizarFuncionario=8)

    funcionario.identificacaoWsVo = ws.generate_identificacaoUsuarioWsVo(factory=factory)
    funcionario.funcionarioWsVo = modelo2.funcionarioWsVo(
        codigo=COD_FUNCIONARIO,
        codigoEmpresa=COD_EMPRESA,
        nomeFuncionario='Teste 1 - modificado modelo 2'
    )

    resp = client.service.importacaoFuncionario(funcionario)

    assert resp['informacaoGeral']['codigoMensagem'] == 'SOC-100'

def test_exporta_dados():
    ws = SOCWebService()

    client = ws.get_client(
        wsdl_url=ws.CONFIGS.get('WSDL_EXPORTA_DADOS'),
        create_username_token=False
    )

    ex = ExportaDados(factory=client.type_factory('ns0'))

    param = ex.pedido_exame(
        empresa=423,
        codigo=ws.EXPORTA_DADOS_KEYS.get('PEDIDO_EXAMES_COD'),
        chave=ws.EXPORTA_DADOS_KEYS.get('PEDIDO_EXAMES_KEY'),
        dataInicio=date.today(),
        dataFim=date.today()
    )

    resp = client.service.exportaDadosWs(ex.build_request_body(param=param))

    assert resp['erro'] == False
    assert resp['mensagemErro'] is None



