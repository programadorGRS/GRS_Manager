from datetime import date, datetime, timedelta

from click.testing import CliRunner
from flask import Flask

from src.extensions import database
from src.main.empresa.empresa import Empresa
from src.main.mandato_cipa.commands.commands import (carregar_hist_mandatos,
                                                     monitorar_mandatos)
from src.main.mandato_cipa.historico_mandatos import HistoricoMandatos
from src.main.mandato_cipa.monitora_mandato import MonitoraMandato
import pandas as pd


def test_carregar_mandatos(app: Flask):
    with app.app_context():
        empresa = (
            database.session.query(Empresa)
            .filter(Empresa.cod_empresa == 529769)
            .first()
        )

        res = HistoricoMandatos.carregar_mandatos(
            id_empresa=empresa.id_empresa,
            data_inicio=(datetime.now() - timedelta(days=360)).date(),
            data_fim=date.today(),
            mandato_ativo=True
        )

        assert not res.erro
        assert res.ok is True


def test_carregar_mandatos_command(runner: CliRunner):
    result = runner.invoke(carregar_hist_mandatos)

    assert result.exit_code == 0
    assert result.exception is None


def test_rotina_monitorar_mandatos(app: Flask):
    with app.app_context():
        empresa = (
            database.session.query(Empresa)
            .filter(Empresa.cod_empresa == 529769)
            .first()
        )

        infos = MonitoraMandato.rotina_monitorar_mandatos(
            id_empresa=empresa.id_empresa,
            data_inicio=(datetime.now() - timedelta(days=360)).date(),
            data_fim=date.today(),
            mandatos_ativos=True
        )

        assert infos['ok'] is True
        assert infos['erro'] is None


def test_monitorar_mandatos_command(runner: CliRunner):
    args_list = [
        '--modo', 2,
        '--id-empresa', 333,
        '--cod-unidade', '269'
    ]

    res = runner.invoke(monitorar_mandatos, args=args_list)

    assert res.exit_code == 0
    assert res.exception is None


def test_erros_funcao():
    df1 = pd.DataFrame({'funcao': [pd.NA, 'teste', pd.NA, 'teste']})

    df2 = MonitoraMandato._MonitoraMandato__erros_funcao(df=df1)  # type: ignore

    msg_erro = 'Candidato sem Função definida'
    assert_series = pd.Series([msg_erro, pd.NA, msg_erro, pd.NA], name='erros_funcionario_funcao')

    pd.testing.assert_series_equal(df2['erros_funcionario_funcao'], assert_series)


def test_erros_situacao():
    df1 = pd.DataFrame({'tipo_situacao': [pd.NA, 'teste', pd.NA, 'teste']})

    df2 = MonitoraMandato._MonitoraMandato__erros_situacao(df=df1)  # type: ignore

    msg_erro = 'Candidato sem definição de Titular/Suplente'
    assert_series = pd.Series([msg_erro, pd.NA, msg_erro, pd.NA], name='erros_funcionario_situacao')

    pd.testing.assert_series_equal(df2['erros_funcionario_situacao'], assert_series)


def test_erros_eleicao():
    df1 = pd.DataFrame({'data_eleicao': [pd.NA, 'teste', pd.NA, 'teste']})

    df2 = MonitoraMandato._MonitoraMandato__erros_eleicao(df=df1)  # type: ignore

    msg_erro = 'Eleição em sem Data Final'
    assert_series = pd.Series([msg_erro, pd.NA, msg_erro, pd.NA], name='erros_mandato_eleicao')

    pd.testing.assert_series_equal(df2['erros_mandato_eleicao'], assert_series)


def test_erros_membros():
    msg_erro = 'Mandato sem eleitos'

    data = [
        (
            pd.DataFrame({'cod_mandato': [1, 1, 1], 'membro_ativo': [True, False, True]}),
            pd.Series([True, True, True], name='possui_membros'),
            pd.Series([None, None, None], name='erros_mandato_membros')
        ),
        (
            pd.DataFrame({'cod_mandato': [1, 1, 1], 'membro_ativo': [False, False, False]}),
            pd.Series([False, False, False], name='possui_membros'),
            pd.Series([msg_erro, msg_erro, msg_erro], name='erros_mandato_membros')
        ),
        (
            pd.DataFrame({'cod_mandato': [1, 1, 1], 'membro_ativo': [True, True, True]}),
            pd.Series([True, True, True], name='possui_membros'),
            pd.Series([None, None, None], name='erros_mandato_membros')
        )
    ]

    for df, s1, s2 in data:
        df2 = MonitoraMandato._MonitoraMandato__erros_membros(df=df)  # type: ignore

        pd.testing.assert_series_equal(df2['possui_membros'], s1)
        pd.testing.assert_series_equal(df2['erros_mandato_membros'], s2)
