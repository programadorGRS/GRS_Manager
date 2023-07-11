if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    import os

    from src import app
    from src.config import set_app_config
    from src.extensions import database
    from src.main.processamento.status_processamento import StatusProcessamento
    from src.main.processamento.tipo_processamento import TipoProcessamento

    TIPOS = [
        {'id': 1, 'nome': 'Carregar Pedidos'},
        {'id': 2, 'nome': 'Carregar Funcionários'}
    ]

    STATUS = [
        {'id': 1, 'nome': 'Em Andamento'},
        {'id': 2, 'nome': 'Concluído'},
        {'id': 3, 'nome': 'Cancelado'},
        {'id': 4, 'nome': 'Erro'}
    ]

    update_items = (
        (TipoProcessamento, TIPOS),
        (StatusProcessamento, STATUS)
    )

    name = os.name
    print('Usando configuração: ', end='')
    if name == 'posix':
        print('prod')
        set_app_config(app=app, conf='prod')
    else:
        print('dev')
        set_app_config(app=app, conf='dev')

    with app.app_context():
        StatusProcessamento.query.delete()
        TipoProcessamento.query.delete()
        database.session.commit()

    with app.app_context():
        for table, data in update_items:
            print(f'Inserindo: {table.__tablename__}')
            database.session.bulk_insert_mappings(table, data)
            database.session.commit()

    print('Done!')

