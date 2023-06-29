import pandas as pd

from src.main.rtc.models import RTC


def test_load_rtc_funcoes():
    PATH = "documents/RTC paradas/Base RTC/RTCFuncoes2.csv"

    df = pd.read_csv(PATH, sep=';', encoding='iso-8859-1')

    df_res = RTC.tratar_df_rtc_cargos(cod_emp_princ=423, df=df)

    assert df_res is not None
    assert not df_res.empty

