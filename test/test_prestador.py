import json
from io import BytesIO

import responses
from click.testing import CliRunner
from flask import Flask

from src.main.prestador.commands import carregar_prestadores
from src.main.prestador.prestador import Prestador

URL = "https://ws1.soc.com.br/WSSoc/services/ExportaDadosWs"

RESP = '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><ns2:exportaDadosWsResponse xmlns:ns2="http://services.soc.age.com/"><return><erro>false</erro><parametros></parametros><retorno>[{"socnet":"não","codigoPrestador":"221","situacao":"Não","statusContrato":"","bairro":"São Luís","cidade":"Jequié","estado":"BA","endereco":"Rua José Alfredo Guimarães","numeroEndereco":"24","complementoEndereco":"1º andar","cep":"45203-330","representanteLegal":"JOSE HENRIQUE GARCIA PADRE","cnpj":"09.911.202/0001-60","cpf":"","codigoAgenciaBanco":"3526","codigoBanco":"237","nomeBanco":"BRADESCO","numeroContaCorrente":"24087-7","nomeTitularConta":"JHPMED COMERCIO DE MATERIAIS MÉDICOS E ASSESSORIA","dataCancelamento":"","dataContratacao":"03/04/2014","diaPagamento":"10","email":"","horarioAtendimentoInicial":"08:00","horarioAtendimentoFinal":"18:00","motivoCancelamento":"","nomePrestador":"CESMET ","razaoSocial":"JHPMED COMERCIO DE MATERIAIS MÉDICOS E ASSESSORIA EM SAUDE OCUPACIONAL LTDA - ME","telefone":"","celular":"","tipoAtendimento":"Ordem de Chegada","tipoPagamento":"Boleto","tipoPrestador":"","tipoPessoa":"Pessoa Jurídica","regraPadraoPagamento":"0","codigoRH":"","nivelClassificacao":"","responsavel":"JOSE HENRIQUE GARCIA PADRE","pagamentoAntecipado":"Não informado","conselhoClasse":"7878","ufConselhoClasse":"BA","especialidadeResponsavel":"Clínico Geral","especialidadeResponsavel2":""},{"socnet":"sim","codigoPrestador":"1736","situacao":"Não","statusContrato":"","bairro":"","cidade":"","estado":"","endereco":"","numeroEndereco":"","complementoEndereco":"","cep":"","representanteLegal":"","cnpj":"61.687.356/0037-40","cpf":"","codigoAgenciaBanco":"","codigoBanco":"","nomeBanco":"","numeroContaCorrente":"","nomeTitularConta":"","dataCancelamento":"","dataContratacao":"","diaPagamento":"1","email":"","horarioAtendimentoInicial":"00:00","horarioAtendimentoFinal":"00:00","motivoCancelamento":"","nomePrestador":"TESTE - SECONCI MOGI","razaoSocial":"","telefone":"","celular":"","tipoAtendimento":"Hora Marcada","tipoPagamento":"","tipoPrestador":"","tipoPessoa":"Pessoa Física","regraPadraoPagamento":"0","codigoRH":"","nivelClassificacao":"","responsavel":"","pagamentoAntecipado":"Não informado","conselhoClasse":"","ufConselhoClasse":"","especialidadeResponsavel":"","especialidadeResponsavel2":""}]</retorno><tipoArquivoRetorno>json</tipoArquivoRetorno></return></ns2:exportaDadosWsResponse></soap:Body></soap:Envelope>'
MSG_ERRO = "Erro teste 123"
RESP_ERRO = f'<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><ns2:exportaDadosWsResponse xmlns:ns2="http://services.soc.age.com/"><return><erro>true</erro><mensagemErro>{MSG_ERRO}</mensagemErro><parametros></parametros><retorno>""</retorno><tipoArquivoRetorno>json</tipoArquivoRetorno></return></ns2:exportaDadosWsResponse></soap:Body></soap:Envelope>'


@responses.activate
def test_carregar_prestadores(app: Flask):
    responses.add(
        method="POST",
        url=URL,
        body=RESP,
    )

    wsdl, ed_keys = __get_credentials()

    with app.app_context():
        res = Prestador.carregar_prestadores(
            cod_emp_princ=423, wsdl=wsdl, ed_keys=ed_keys
        )

    assert res.ok is True

    responses.add(
        method="POST",
        url=URL,
        body=RESP_ERRO,
    )

    wsdl, ed_keys = __get_credentials()

    with app.app_context():
        res = Prestador.carregar_prestadores(
            cod_emp_princ=423, wsdl=wsdl, ed_keys=ed_keys
        )

    assert res.ok is False
    assert MSG_ERRO in res.erro  # type: ignore


@responses.activate
def test_carregar_prestadores_command(runner: CliRunner):
    responses.add(
        method="POST",
        url=URL,
        body=RESP,
    )
    res = runner.invoke(carregar_prestadores)

    assert res.exit_code == 0
    assert res.exception is None


def __get_credentials():
    with open("configs/soc/wsdl/prod/ExportaDadosWs.xml", mode="rb") as f:
        wsdl = BytesIO(f.read())

    with open("keys/soc/exporta_dados/grs.json", mode="rt") as f:
        ed_keys = json.load(f)

    return (wsdl, ed_keys)
