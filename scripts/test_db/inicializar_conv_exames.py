if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    import pandas as pd

    from manager import database
    from manager.models import (ConvExames, Empresa, EmpresaPrincipal,
                                PedidoProcessamento)

    # inserir pedidos processamento
    df = pd.read_csv('documents/PedidosProcessamento_1665067986.csv', sep=';', encoding='iso-8859-1')
    df['data_criacao'] = pd.to_datetime(df['data_criacao'], dayfirst=True).dt.date

    df_empresas = pd.read_sql(sql=Empresa.query.filter(Empresa.cod_empresa_principal == 423).statement, con=database.session.bind)

    df_empresas = df_empresas[['id_empresa', 'cod_empresa']]

    df = df.merge(
        df_empresas,
        how='left',
        on='cod_empresa'
    )

    df.to_sql(PedidoProcessamento.__tablename__, con=database.session.bind, if_exists='append', index=False)

    for emp in EmpresaPrincipal.query.all():

        pedidos_proc = [
            i.id_proc
            for i in PedidoProcessamento.query.filter_by(cod_empresa_principal=emp.cod)
        ]
        ConvExames.inserir_conv_exames(emp.cod, pedidos_proc)