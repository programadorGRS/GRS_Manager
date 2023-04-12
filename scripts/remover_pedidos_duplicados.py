"""
    Script para remover Pedidos duplicados. Realiza query com Group By e deleta
    o Pedidos duplicados com id_ficha mais Recente
"""


if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    import pandas as pd
    from sqlalchemy import delete, func

    from src import app, database
    from src.main.pedido.pedido import Pedido

    with app.app_context():
        Qtd = func.count(Pedido.id_ficha).label('Qtd') # alias
        query_duplicados = (
            database.session.query(Pedido.seq_ficha, Qtd)
            .group_by(Pedido.seq_ficha)
            .having(Qtd > 1) # filtrar usando o alias
        )
        df_duplicados = pd.read_sql(sql=query_duplicados.statement, con=database.session.bind)

        query_id_fichas = (
            database.session.query(Pedido.id_ficha, Pedido.seq_ficha)
            .filter(Pedido.seq_ficha.in_(df_duplicados['seq_ficha']))
            .order_by(Pedido.id_ficha.asc()) # ids mais antigas no inicio
        )
        df_ids = pd.read_sql(sql=query_id_fichas.statement, con=database.session.bind)
        # marcar ids duplicadas como True e as originais(first) como False
        df_ids['duplicado'] = df_ids.duplicated(subset='seq_ficha', keep='first')
        # filtrar apenas as duplicadas mais recentes
        df_ids = df_ids[df_ids['duplicado'] == True]

        if not df_ids.empty:
            delete_query = (
                delete(Pedido).
                where(Pedido.id_ficha.in_(df_ids['id_ficha']))
            )
            database.session.execute(delete_query)
            database.session.commit()

            print(f'Linhas duplicadas deletadas: {len(df_ids)}')
        else:
            print("Nenhum duplicado encontrado")

