import random

import pandas as pd
from flask import Flask

from src.extensions import database
from src.main.exame.exame import Exame
from src.main.funcionario.funcionario import Funcionario
from src.main.rtc.gerar_rtc import GerarRTC
from src.main.rtc.infos_rtc import InfosRtc
from src.main.rtc.models import RTC, RTCCargos
from src.main.tipo_exame.tipo_exame import TipoExame
from src.main.empresa.empresa import Empresa
from src.main.pedido.pedido import Pedido
from src.main.rtc.routes import RTC_DEFAULT
import secrets


def test_load_rtc_funcoes():
    PATH = "documents/RTC paradas/Base RTC/RTCFuncoes2.csv"

    df = pd.read_csv(PATH, sep=";", encoding="iso-8859-1")

    df_res = RTC.tratar_df_rtc_cargos(cod_emp_princ=423, df=df)

    assert df_res is not None
    assert not df_res.empty


def test_get_funcionario(app: Flask):
    g = GerarRTC()
    with app.app_context():
        f = g._GerarRTC__get_funcionario(random.randint(1, 100), random.randint(1, 500))

        assert isinstance(f, Funcionario) or f is None


def test_get_rtcs_cargo(app: Flask):
    g = GerarRTC()
    with app.app_context():
        query_cargos = database.session.query(RTCCargos).all()

        cargo = random.choice(query_cargos)[0]

        query_rtcs = (
            database.session.query(RTCCargos)
            .filter(RTCCargos.c.cod_cargo == cargo)
            .all()
        )

        ls_rtcs = [i.id_rtc for i in query_rtcs]

        rtcs: list[RTC] = g._GerarRTC__get_rtcs_cargo(cargo)

        for rtc in rtcs:
            assert rtc.id_rtc in ls_rtcs


def test_get_exames_rtc(app: Flask):
    g = GerarRTC()
    with app.app_context():
        ids_rtcs = []
        for rtc in RTC.query.all():
            choice = random.choice((True, False))
            if choice is True:
                ids_rtcs.append(rtc.id_rtc)

        tipo_exame = random.choice((TipoExame.query.all())).cod_tipo_exame
        emp_princ = 423

        exames: list[Exame] = g._GerarRTC__get_exames_rtc(
            ids_rtcs=ids_rtcs, cod_tipo_exame=tipo_exame, cod_emp_princ=emp_princ
        )

        assert len(exames) > 0


def test_render_rtc_html(app: Flask):
    g = GerarRTC()
    with app.app_context():
        f = random.choice(Funcionario.query.limit(100).all())
        e = random.choice(Empresa.query.limit(100).all())
        p = random.choice(Pedido.query.limit(100).all())
        ex = Exame.query.limit(random.randint(1, 7)).all()
        r = RTC.query.limit(random.randint(1, 6)).all()

        infos = InfosRtc(empresa=e, pedido=p, funcionario=f, exames=ex, rtcs=r)

        tipo_s = random.choice((True, False))
        qr = random.choice((None, secrets.token_hex()))

        with open(RTC_DEFAULT, "rt", encoding="utf-8") as fl:
            temp_body = fl.read()

        html_str = g.render_rtc_html(
            infos=infos, template_body=temp_body, render_tipo_sang=tipo_s, qr_code=qr
        )

        assert f.nome_funcionario in html_str
        assert f.nome_setor in html_str
        assert f.nome_cargo in html_str

        for exame in ex:
            assert exame.nome_exame in html_str

        if tipo_s is True:
            assert "Tipo Sanguíneo" in html_str
        else:
            assert "Tipo Sanguíneo" not in html_str

        if qr:
            assert qr in html_str
