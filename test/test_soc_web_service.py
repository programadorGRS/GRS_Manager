from src.soc_web_service.soc_web_service import SOCWebService
from src.soc_web_service.modelo_2 import Modelo2
from src.soc_web_service.exporta_dados import ExportaDados
from datetime import date


def test_init():
    ws = SOCWebService(wsdl_filename='prod/ExportaDadosWs.xml')

def test_funcionario_service():
    COD_EMPRESA = 268104 # empresa: BASE TREINAMENTO NUCLEO
    COD_FUNCIONARIO = 177 # funcionario: Teste1

    m2 = Modelo2(wsdl_filename='teste/FuncionarioModelo2Ws.xml')

    m2.set_webservice_keys(filename='grs.json')

    funcionario = m2.Funcionario()

    m2.config_criacoes(funcionario=funcionario)
    m2.config_atualizacoes(funcionario=funcionario, atualizarFuncionario=8)

    funcionario.identificacaoWsVo = m2.generate_identificacaoUsuarioWsVo()

    funcionario.funcionarioWsVo = m2.funcionarioWsVo(
        codigo=COD_FUNCIONARIO,
        codigoEmpresa=COD_EMPRESA,
        nomeFuncionario='Teste 1 - modificado modelo 2'
    )

    resp = m2.call_service(request_body=funcionario)

    assert resp['informacaoGeral']['codigoMensagem'] == 'SOC-100'

def test_exporta_dados_service():
    ex = ExportaDados(
        wsdl_filename='prod/ExportaDadosWs.xml',
        exporta_dados_keys_filename='grs.json'
    )

    param = ex.pedido_exame(
        empresa=423,
        codigo=ex.EXPORTA_DADOS_KEYS.get('PEDIDO_EXAMES_COD'),
        chave=ex.EXPORTA_DADOS_KEYS.get('PEDIDO_EXAMES_KEY'),
        dataInicio=date.today(),
        dataFim=date.today()
    )

    body = ex.build_request_body(param=param)

    resp = ex.call_service(request_body=body)

    assert resp['erro'] == False
    assert resp['mensagemErro'] is None



