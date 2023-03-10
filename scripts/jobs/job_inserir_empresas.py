if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    from datetime import datetime
    from os.path import basename

    from manager import TIMEZONE_SAO_PAULO
    from manager.email_connect import EmailConnect
    from manager.models import Empresa, EmpresaPrincipal


    EMPRESAS_PRINCIPAIS: list[EmpresaPrincipal]  = EmpresaPrincipal.query.all()
    TENTATIVAS = 4

    NOME_TABELA = 'Empresas'
    ACAO = 'Inserir'


    total_inseridos = 0
    erro = None

    for empresa_principal in EMPRESAS_PRINCIPAIS:
        for i in range(TENTATIVAS):
            print(f'{empresa_principal.nome} - {ACAO} {NOME_TABELA} - tentativa: {i + 1}/{TENTATIVAS}', end=' - ')
            try:
                qtd_inseridos = Empresa.inserir_empresas(cod_empresa_principal=empresa_principal.cod)
                print(f'Qtd: {qtd_inseridos}')
                total_inseridos = total_inseridos + qtd_inseridos
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
        message_body = str({NOME_TABELA: total_inseridos, 'Erro': erro})
    )
    if enviar_report['sent'] == 1:
        print(f'Enviado para: {DESTINATARIO}')
    else:
        print(f"Não enviado. ERRO: {enviar_report['error']}")
    
    print(f'Done! Total: {total_inseridos}')

