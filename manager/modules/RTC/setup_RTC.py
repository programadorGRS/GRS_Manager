'''
    Le as 3 planilhas de RTC, trata cada uma e insere na database
'''


if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    import pandas as pd

    from manager import database
    from manager.modules.RTC.models import RTC, RTCCargos, RTCExames
    from sqlalchemy import delete, insert

    # RTC
    RTC.query.delete()
    database.session.commit()

    arquivo = 'manager/modules/RTC/documents/RTCs.csv'
    df = pd.read_csv(arquivo, sep=';', encoding='iso-8859-1')
    df.to_sql(name=RTC.__tablename__, con=database.session.bind, index=False, if_exists='append')
    database.session.commit()

    # RTCCargos
    delete_query = database.session.execute(delete(RTCCargos))
    database.session.commit()

    arquivo = 'manager/modules/RTC/documents/RTCFuncoes.csv'
    df = pd.read_csv(arquivo, sep=';', encoding='iso-8859-1')
    df['chave'] = df['id_rtc'].astype(str) + df['cod_cargo'].astype(str)
    df.drop_duplicates('chave', inplace=True)
    df = df[['cod_cargo', 'id_rtc']]
    df = df.to_dict(orient='records')
    database.session.execute(insert(RTCCargos).values(df))
    database.session.commit()

    # RTCEXames
    delete_query = database.session.execute(delete(RTCExames))
    database.session.commit()

    arquivo = 'manager/modules/RTC/documents/RTCExames.csv'
    df = pd.read_csv(arquivo, sep=';', encoding='iso-8859-1')
    df['chave'] = (
        df['id_rtc'].astype(str) +
        df['cod_exame'].astype(str) +
        df['cod_tipo_exame'].astype(str)
    )
    df.drop_duplicates('chave', inplace=True)
    df = df[['id_rtc', 'cod_exame', 'cod_tipo_exame']]
    df = df.to_dict(orient='records')
    database.session.execute(insert(RTCExames).values(df))
    database.session.commit()

