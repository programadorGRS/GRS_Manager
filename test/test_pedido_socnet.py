import pandas as pd
from flask import Flask
from datetime import date

from src.main.pedido_socnet.pedido_socnet import PedidoSOCNET


def test_tratar_df(app: Flask):
    COLS = {
        "id_ficha": int,
        "seq_ficha": int,
        "cod_empresa_principal": int,
        "cod_empresa_referencia": int,
        "cod_funcionario": int,
        "cpf": str,
        "nome_funcionario": str,
        "data_ficha": date,
        "cod_tipo_exame": int,
        "id_prestador": int,
        "id_empresa": int,
    }

    with app.app_context():
        df = __get_df_socnet()

        df = PedidoSOCNET.tratar_df_socnet(df=df)

    assert not df.empty
    assert list(df.columns) == list(COLS.keys())


def __get_df_socnet():
    FILE_PATH = r"test\test_files\pedidos_socnet.csv"

    df = pd.read_csv(filepath_or_buffer=FILE_PATH, sep=";", header=2)
    return df
