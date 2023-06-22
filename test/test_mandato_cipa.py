from datetime import date, datetime, timedelta

from click.testing import CliRunner
from flask import Flask

from src.extensions import database
from src.main.empresa.empresa import Empresa
from src.main.mandato_cipa.commands.commands import (carregar_hist_mandatos,
                                                     monitorar_mandatos)
from src.main.mandato_cipa.historico_mandatos import HistoricoMandatos
from src.main.mandato_cipa.monitora_mandato import MonitoraMandato


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
        assert res.ok == True

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

        assert infos['ok'] == True
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
