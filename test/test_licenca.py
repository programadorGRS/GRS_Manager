from datetime import datetime, timedelta

import responses
from flask import Flask

from src.extensions import database as db
from src.main.absenteismo.absenteismo import Absenteismo
from src.main.empresa.empresa import Empresa

URL = "https://ws1.soc.com.br/WSSoc/services/ExportaDadosWs"
RESP_SOCIND = """<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><ns2:exportaDadosWsResponse xmlns:ns2="http://services.soc.age.com/"><return><erro>false</erro><parametros>{"empresa": 423, "codigo": "10888", "chave": "7ef6026bb7039837b650", "tipoSaida": "json", "empresaTrabalho": 529765, "dataInicio": "06/10/2023", "dataFim": "11/10/2023"}</parametros><retorno>[{"TIPO_LICENCA":"*ATESTADO MÉDICO &lt; 15 DIAS","CODIGO_MEDICO":"3976","MEDICO":"MÉDICO DE TESTE 1","DATA_FICHA":"06/10/2023","AFASTAMENTO_EM_HORAS":"0","DATA_INICIO_LICENCA":"04/10/2023","DATA_FIM_LICENCAO":"04/10/2023","HORA_INICIO":"0","HORA_FIM":"0","MOTIVO_LICENCA":"ACIDENTE/DOENÇA NÃO RELACIONADA AO TRABALHO","CID_CONTESTADO":"Z00.8","TIPO_CID":"0","ACIDENTE_TRAJETO":"0","SOLICITANTE":"","ESPECIALIDADE":"","SIGLACONSELHOSOLICITANTE":"","CONSELHOSOLICITANTE":"","UFCONSELHOSOLICITANTE":"","DATA_SOLICITACAO":"","LOCAL_ATENDIMENTO":"","CIDADE_ATENDIMENTO":"","ESTADO_ATENDIMENTO":"","NUMERO_BENEFICIO":"","ESPECIO_BENEFICIO":"","SITUACAO":"0","DATA_INICIO_FAP":"","DATA_INDEFERIMENTO":"","DATA_ULTIMO_DIA_TRABALHO":"","DATA_REQUERIMENTO":"","DATA_DESPACHO":"","PERICIA":"","DATA_LIMITE_DOSE":"","DATA_CESSACAO":"","DTINCLUSAOLICENCA":"06/10/2023","CODIGOFUNCIONARIO":"93034398","MATRICULARH":"C02S000064901","NOMEFUNCIONARIO":"JORGE LUIZ BORGES CIRILO","TIPOLICENCA":"30","CODINTTIPOLICENCA":"0","MOTIVOLICENCA":"64","CODINTMOTIVOLICENCA":"0","CODCID":"Z00.8"},{"TIPO_LICENCA":"*ATESTADO MÉDICO &lt; 15 DIAS","CODIGO_MEDICO":"3976","MEDICO":"MÉDICO DE TESTE 1","DATA_FICHA":"06/10/2023","AFASTAMENTO_EM_HORAS":"0","DATA_INICIO_LICENCA":"27/09/2023","DATA_FIM_LICENCAO":"27/09/2023","HORA_INICIO":"0","HORA_FIM":"0","MOTIVO_LICENCA":"ACIDENTE/DOENÇA NÃO RELACIONADA AO TRABALHO","CID_CONTESTADO":"R51","TIPO_CID":"0","ACIDENTE_TRAJETO":"0","SOLICITANTE":"","ESPECIALIDADE":"","SIGLACONSELHOSOLICITANTE":"","CONSELHOSOLICITANTE":"","UFCONSELHOSOLICITANTE":"","DATA_SOLICITACAO":"","LOCAL_ATENDIMENTO":"","CIDADE_ATENDIMENTO":"","ESTADO_ATENDIMENTO":"","NUMERO_BENEFICIO":"","ESPECIO_BENEFICIO":"","SITUACAO":"0","DATA_INICIO_FAP":"","DATA_INDEFERIMENTO":"","DATA_ULTIMO_DIA_TRABALHO":"","DATA_REQUERIMENTO":"","DATA_DESPACHO":"","PERICIA":"","DATA_LIMITE_DOSE":"","DATA_CESSACAO":"","DTINCLUSAOLICENCA":"06/10/2023","CODIGOFUNCIONARIO":"75916001","MATRICULARH":"C02S000060266","NOMEFUNCIONARIO":"ISAAC GABRIEL SOARES OLIVEIRA","TIPOLICENCA":"30","CODINTTIPOLICENCA":"0","MOTIVOLICENCA":"64","CODINTMOTIVOLICENCA":"0","CODCID":"R51"},{"TIPO_LICENCA":"*ATESTADO MÉDICO &lt; 15 DIAS","CODIGO_MEDICO":"3976","MEDICO":"MÉDICO DE TESTE 1","DATA_FICHA":"06/10/2023","AFASTAMENTO_EM_HORAS":"0","DATA_INICIO_LICENCA":"03/10/2023","DATA_FIM_LICENCAO":"09/10/2023","HORA_INICIO":"0","HORA_FIM":"0","MOTIVO_LICENCA":"ACIDENTE/DOENÇA NÃO RELACIONADA AO TRABALHO","CID_CONTESTADO":"M25.5","TIPO_CID":"0","ACIDENTE_TRAJETO":"0","SOLICITANTE":"","ESPECIALIDADE":"","SIGLACONSELHOSOLICITANTE":"","CONSELHOSOLICITANTE":"","UFCONSELHOSOLICITANTE":"","DATA_SOLICITACAO":"","LOCAL_ATENDIMENTO":"","CIDADE_ATENDIMENTO":"","ESTADO_ATENDIMENTO":"","NUMERO_BENEFICIO":"","ESPECIO_BENEFICIO":"","SITUACAO":"0","DATA_INICIO_FAP":"","DATA_INDEFERIMENTO":"","DATA_ULTIMO_DIA_TRABALHO":"","DATA_REQUERIMENTO":"","DATA_DESPACHO":"","PERICIA":"","DATA_LIMITE_DOSE":"","DATA_CESSACAO":"","DTINCLUSAOLICENCA":"06/10/2023","CODIGOFUNCIONARIO":"75916001","MATRICULARH":"C02S000060266","NOMEFUNCIONARIO":"ISAAC GABRIEL SOARES OLIVEIRA","TIPOLICENCA":"30","CODINTTIPOLICENCA":"0","MOTIVOLICENCA":"64","CODINTMOTIVOLICENCA":"0","CODCID":"M25.5"}]</retorno><tipoArquivoRetorno>json</tipoArquivoRetorno></return></ns2:exportaDadosWsResponse></soap:Body></soap:Envelope>"""
RESP_MED = """<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><ns2:exportaDadosWsResponse xmlns:ns2="http://services.soc.age.com/"><return><erro>false</erro><parametros>{"empresa": 529765, "codigo": "11007", "chave": "e0d2fe50debfaec6b2d7", "tipoSaida": "json", "funcionarioInicio": "0", "funcionarioFim": "999999999999", "dataInicio": "06/10/2023", "dataFim": "11/10/2023", "pData": 0}</parametros><retorno>[{"FUNCIONARIO":"93034398","MATRICULA":"077106","CPF":"84564113534","MEDICO":"MÉDICO DE TESTE 1","CONSELHO":"CRM","CRM":"00000","SOLICITANTE":"MÉDICO PROVISORIO","CONSELHO_SOLICITANTE":"CRM","CRM_SOLICITANTE":"0001","SOLICITANTEFICHA":"","CONSELHO_SOLICITANTEFICHA":"","CRM_SOLICITANTEFICHA":"","DATAFICHA":"06/10/2023","TIPOLICENCA":"*ATESTADO MÉDICO &lt; 15 DIAS","AFASTHORAS":"nÃ£o","DIASAFASTADOS":"1","PEIODOAFASTADO":"0","SITUACAO":"Ativo","ABONADO":"1","CID":"Z00.8"},{"FUNCIONARIO":"75916001","MATRICULA":"072443","CPF":"14803297622","MEDICO":"MÉDICO DE TESTE 1","CONSELHO":"CRM","CRM":"00000","SOLICITANTE":"MÉDICO PROVISORIO","CONSELHO_SOLICITANTE":"CRM","CRM_SOLICITANTE":"0001","SOLICITANTEFICHA":"","CONSELHO_SOLICITANTEFICHA":"","CRM_SOLICITANTEFICHA":"","DATAFICHA":"06/10/2023","TIPOLICENCA":"*ATESTADO MÉDICO &lt; 15 DIAS","AFASTHORAS":"nÃ£o","DIASAFASTADOS":"1","PEIODOAFASTADO":"0","SITUACAO":"Ativo","ABONADO":"1","CID":"R51"},{"FUNCIONARIO":"75916001","MATRICULA":"072443","CPF":"14803297622","MEDICO":"MÉDICO DE TESTE 1","CONSELHO":"CRM","CRM":"00000","SOLICITANTE":"LUIS ROBERTO FELIX ALKMIM","CONSELHO_SOLICITANTE":"CRM","CRM_SOLICITANTE":"73959","SOLICITANTEFICHA":"","CONSELHO_SOLICITANTEFICHA":"","CRM_SOLICITANTEFICHA":"","DATAFICHA":"06/10/2023","TIPOLICENCA":"*ATESTADO MÉDICO &lt; 15 DIAS","AFASTHORAS":"nÃ£o","DIASAFASTADOS":"7","PEIODOAFASTADO":"0","SITUACAO":"Ativo","ABONADO":"1","CID":"M25.5"},{"FUNCIONARIO":"93042194","MATRICULA":"083969","CPF":"06595086646","MEDICO":"MÉDICO DE TESTE 1","CONSELHO":"CRM","CRM":"00000","SOLICITANTE":"DENIS MIRANDA ","CONSELHO_SOLICITANTE":"CRM","CRM_SOLICITANTE":"31254","SOLICITANTEFICHA":"","CONSELHO_SOLICITANTEFICHA":"","CRM_SOLICITANTEFICHA":"","DATAFICHA":"06/10/2023","TIPOLICENCA":"*ATESTADO MÉDICO &lt; 15 DIAS","AFASTHORAS":"nÃ£o","DIASAFASTADOS":"3","PEIODOAFASTADO":"0","SITUACAO":"Ativo","ABONADO":"1","CID":"J01.1"},{"FUNCIONARIO":"93049289","MATRICULA":"090395","CPF":"43563692890","MEDICO":"MARIANA MARTINS PAIVA VIEIRA CAMPOS","CONSELHO":"CRM","CRM":"215698","SOLICITANTE":"MARIANA MARTINS PAIVA VIEIRA CAMPOS","CONSELHO_SOLICITANTE":"CRM","CRM_SOLICITANTE":"215698","SOLICITANTEFICHA":"","CONSELHO_SOLICITANTEFICHA":"","CRM_SOLICITANTEFICHA":"","DATAFICHA":"06/10/2023","TIPOLICENCA":"*ATESTADO MÉDICO &lt; 15 DIAS","AFASTHORAS":"nÃ£o","DIASAFASTADOS":"1","PEIODOAFASTADO":"0","SITUACAO":"Ativo","ABONADO":"1","CID":"M54.3"}]</retorno><tipoArquivoRetorno>json</tipoArquivoRetorno></return></ns2:exportaDadosWsResponse></soap:Body></soap:Envelope>"""


@responses.activate
def test_licenca_socind(app: Flask):
    responses.add(method="POST", url=URL, body=RESP_SOCIND, status=200)

    with app.app_context():
        empresa = (
            db.session.query(Empresa)  # type: ignore
            .filter(
                (Empresa.razao_social.like("%MANSERV%"))
                | (Empresa.razao_social.like("%LSI%"))  # noqa
            )
            .first()
        )

        df = Absenteismo.carregar_licenca_socind(
            id_empresa=empresa.id_empresa,
            dataInicio=datetime.now() - timedelta(days=5),
            dataFim=datetime.now(),
        )

        assert df is not None


@responses.activate
def test_licenca_med(app: Flask):
    responses.add(method="POST", url=URL, body=RESP_MED, status=200)

    with app.app_context():
        empresa = (
            db.session.query(Empresa)  # type: ignore
            .filter(
                (Empresa.razao_social.like("%MANSERV%"))
                | (Empresa.razao_social.like("%LSI%"))  # noqa
            )
            .first()
        )

        df = Absenteismo.carregar_licenca_medica(
            id_empresa=empresa.id_empresa,
            dataInicio=datetime.now() - timedelta(days=5),
            dataFim=datetime.now(),
        )

        assert df is not None


@responses.activate
def test_inserir_licenca(app: Flask):
    responses.add(method="POST", url=URL, body=RESP_SOCIND, status=200)
    responses.add(method="POST", url=URL, body=RESP_MED, status=200)

    with app.app_context():
        empresa = (
            db.session.query(Empresa)  # type: ignore
            .filter(
                (Empresa.razao_social.like("%MANSERV%"))
                | (Empresa.razao_social.like("%LSI%"))  # noqa
            )
            .first()
        )

        res = Absenteismo.inserir_licenca(
            id_empresa=empresa.id_empresa,
            dataInicio=datetime.now() - timedelta(days=5),
            dataFim=datetime.now(),
        )

        status = res["status"]

        assert "erro" not in status.lower()  # type: ignore
