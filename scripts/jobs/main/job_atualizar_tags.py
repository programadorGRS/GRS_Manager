#!~/GRS_Manager/venv/bin/python3


if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    from datetime import datetime
    from os.path import basename

    from src import TIMEZONE_SAO_PAULO, app
    from src.email_connect import EmailConnect
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


        # enviar report
        DESTINATARIO = ['gabrielsantos@grsnucleo.com.br']
        TIMESTAMP = datetime.now(tz=TIMEZONE_SAO_PAULO).strftime('%d-%m-%Y %H:%M:%S')
        FILENAME = basename(__file__)

        print(f'Enviando report...')
        enviar_report = EmailConnect.send_email(
            to_addr = DESTINATARIO,
            message_subject = f"{FILENAME} executado {TIMESTAMP}",
            message_body = str({NOME_TABELA: qtd, 'Erro': erro})
        )
        if enviar_report['sent'] == 1:
            print(f'Enviado para: {DESTINATARIO}')
        else:
            print(f"Não enviado. ERRO: {enviar_report['error']}")
        
        print(f'Done! Total: {qtd}')


