from src.main.conv_exames.ped_proc import PedidoProcessamento
from flask import Flask
from io import BytesIO
import json
import responses
from src.main.job.job_infos import JobInfos
from click.testing import CliRunner
from src.main.conv_exames.commands import criar_ped_proc, sync_configs, inserir_conv_exames


URL = "https://ws1.soc.com.br/WSSoc/ProcessamentoAssincronoWs"


RESP_OK = """<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
<SOAP-ENV:Header xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"/>
<soap:Body>
<ns2:incluirSolicitacaoResponse xmlns:ns2="http://services.soc.age.com/">
<ProcessamentoAssincronoRetorno>
<informacaoGeral>
<codigoMensagem>SOC-100</codigoMensagem>
<mensagem>mock response ok</mensagem>
<mensagemOperacaoDetalheList>
<codigo>SOC-100</codigo>
<mensagem>mock response ok</mensagem>
</mensagemOperacaoDetalheList>
<numeroErros></numeroErros>
</informacaoGeral>
<codigoSolicitacao>123456</codigoSolicitacao>
</ProcessamentoAssincronoRetorno>
</ns2:incluirSolicitacaoResponse>
</soap:Body>
</soap:Envelope>"""

MSG1 = "err msg 1"
MSG2 = "err msg 2"
RESP_ERR = f"""<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
<SOAP-ENV:Header xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"/>
<soap:Body>
<ns2:incluirSolicitacaoResponse xmlns:ns2="http://services.soc.age.com/">
<ProcessamentoAssincronoRetorno>
<informacaoGeral>
<codigoMensagem>SOC-300</codigoMensagem>
<mensagem>{MSG1}</mensagem>
<mensagemOperacaoDetalheList>
<codigo>SOC-300</codigo>
<mensagem>{MSG2}</mensagem>
</mensagemOperacaoDetalheList>
<numeroErros>1</numeroErros>
</informacaoGeral>
<codigoSolicitacao></codigoSolicitacao>
</ProcessamentoAssincronoRetorno>
</ns2:incluirSolicitacaoResponse>
</soap:Body>
</soap:Envelope>"""


RESP_INSERIR = """<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <ns2:exportaDadosWsResponse xmlns:ns2="http://services.soc.age.com/">
            <return>
                <erro>true</erro>
                <mensagemErro>Sem Resultado.</mensagemErro>
                <parametros>{'empresa':'423','codigo':'151346','chave':'b5aa04943cd28ff155ed','tipoSaida':'json','empresaTrabalho':'426','codigoSolicitacao':'114057830'}</parametros>
                <tipoArquivoRetorno>json</tipoArquivoRetorno>
            </return>
        </ns2:exportaDadosWsResponse>
    </soap:Body>
</soap:Envelope>"""


def test_sync_configs(runner: CliRunner):
    res = runner.invoke(sync_configs)

    assert res.exit_code == 0
    assert res.exception is None


@responses.activate
def test_criar_ped_proc(app: Flask):
    responses.add(url=URL, method="POST", body=RESP_OK, status=200)

    with app.app_context():
        wsdl, ws_keys = get_proc_assinc_configs()
        infos = PedidoProcessamento.criar_ped_proc(
            id_empresa=1, wsdl=wsdl, ws_keys=ws_keys
        )

    assert isinstance(infos, JobInfos)
    assert infos.ok is True
    assert infos.erro is None
    assert infos.qtd_inseridos == 1

    responses.add(url=URL, method="POST", body=RESP_ERR, status=200)

    with app.app_context():
        wsdl, ws_keys = get_proc_assinc_configs()
        infos = PedidoProcessamento.criar_ped_proc(
            id_empresa=1, wsdl=wsdl, ws_keys=ws_keys
        )

    assert isinstance(infos, JobInfos)
    assert infos.ok is False
    assert infos.erro is not None
    assert MSG1 in infos.erro
    assert MSG2 in infos.erro


def get_proc_assinc_configs():
    with open(r"configs\soc\wsdl\prod\ProcessamentoAssincronoWs.xml", "rb") as f:
        wsdl = BytesIO(f.read())

    with open(r"keys\soc\web_service\grs.json", "r") as f:
        ws_keys = json.load(f)

    return (wsdl, ws_keys)


@responses.activate
def test_criar_ped_proc_command(runner: CliRunner):
    responses.add(url=URL, method="POST", body=RESP_OK, status=200)

    arg_ls = ["-id", 1, "-id", 2, "-id", 3]
    result = runner.invoke(criar_ped_proc, args=arg_ls)

    assert result.exit_code == 0
    assert result.exception is None


@responses.activate
def test_inserir_conv_exames(runner: CliRunner):
    responses.add(url=URL, method="POST", body=RESP_INSERIR, status=200)
    res = runner.invoke(inserir_conv_exames)

    assert res.exit_code == 0
    assert res.exception is None
