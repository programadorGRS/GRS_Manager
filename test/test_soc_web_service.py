from src.soc_web_service.soc_web_service import SOCWebService
from src.soc_web_service.exporta_dados import ExportaDados
from datetime import date
from zeep.plugins import HistoryPlugin


def test_init():
    ws = SOCWebService(wsdl_filename='prod/ExportaDadosWs.xml')


def test_exporta_dados_service():
    history = HistoryPlugin()

    ex = ExportaDados(
        wsdl_filename='prod/ExportaDadosWs.xml',
        exporta_dados_keys_filename='grs.json',
        client_plugins=[history]
    )

    param = ex.pedido_exame(
        empresa=423,
        codigo=ex.EXPORTA_DADOS_KEYS.get('PEDIDO_EXAMES_COD'),
        chave=ex.EXPORTA_DADOS_KEYS.get('PEDIDO_EXAMES_KEY'),
        dataInicio=date.today(),
        dataFim=date.today()
    )

    body = ex.build_request_body(param=param)

    try:
        resp = ex.call_service(request_body=body)
    except:
        pass

    assert resp['erro'] == False
    assert resp['mensagemErro'] is None

