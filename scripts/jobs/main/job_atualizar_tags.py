#!~/GRS_Manager/venv/bin/python3


if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    from src import app
    from src.main.pedido.pedido import Pedido

    with app.app_context():
        NOME_TABELA = 'Tags Prev Liberação'

        erro = None

        # NOTE: o total de tags atualizadas sai maior do que o total de pedidos existentes \
        # porque atualmente, ele atualiza o mesmo pedido varias vezes
        try:
            print('Atualizando Tags', end=' - ')
            qtd = Pedido.atualizar_tags_prev_liberacao()
            print(f'Qtd: {qtd}')
        except Exception as exception:
            erro = type(exception).__name__
            print(f'ERRO: {erro}')

        print(f'Done! Total: {qtd}')


