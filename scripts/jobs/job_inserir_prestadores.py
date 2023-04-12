if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    from datetime import datetime
    from os.path import basename

    from src import TIMEZONE_SAO_PAULO, app
    from src.email_connect import EmailConnect
    from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
    from src.main.prestador.prestador import Prestador

    with app.app_context():
        # NOTE: sempre inserir prestadores apenas da GRS
        EMPRESA_PRINCIPAL: EmpresaPrincipal = EmpresaPrincipal.query.get(423)
        TENTATIVAS = 4

        NOME_TABELA = 'Prestadores'
        ACAO = 'Inserir'

        total_inseridos = 0
        erro = None

        for i in range(TENTATIVAS):
            print(f'{EMPRESA_PRINCIPAL.nome} - {ACAO} {NOME_TABELA} - tentativa: {i + 1}/{TENTATIVAS}', end=' - ')
            try:
                total_inseridos = Prestador.inserir_prestadores(cod_empresa_principal=EMPRESA_PRINCIPAL.cod)
                print(f'Qtd: {total_inseridos}')
                break
            except Exception as exception:
                erro = type(exception).__name__
                print(f'ERRO: {erro}')
                continue


        # enviar report
        DESTINATARIO = ['gabrielsantos@grsnucleo.com.br']
        TIMESTAMP = datetime.now(tz=TIMEZONE_SAO_PAULO).strftime('%d-%m-%Y %H:%M:%S')
        FILENAME = basename(__file__)

        print(f'Enviando report...')
        enviar_report = EmailConnect.send_email(
            to_addr = DESTINATARIO,
            message_subject = f"{FILENAME} executado {TIMESTAMP}",
            message_body = str({'Prestadores': total_inseridos, 'Erro': erro})
        )
        if enviar_report['sent'] == 1:
            print(f'Enviado para: {DESTINATARIO}')
        else:
            print(f"Não enviado. ERRO: {enviar_report['error']}")
        
        print(f'Done! Total: {total_inseridos}')

