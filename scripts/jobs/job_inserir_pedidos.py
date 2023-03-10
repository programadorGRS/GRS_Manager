if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    from datetime import datetime, timedelta
    from os.path import basename

    from manager import TIMEZONE_SAO_PAULO, database
    from manager.email_connect import EmailConnect
    from manager.models import Empresa, EmpresaPrincipal, Pedido


    # NOTE: sempre inserir pedidos apenas da GRS
    EMPRESA_PRINCIPAL: EmpresaPrincipal = EmpresaPrincipal.query.get(423)
    TENTATIVAS = 4

    NOME_TABELA = 'Pedidos'
    ACAO = 'Inserir'
    
    HOJE = datetime.now(tz=TIMEZONE_SAO_PAULO)
    DIAS_INICIO = 5
    DIAS_FIM = 3
    DATA_INICIO = (HOJE - timedelta(days=DIAS_INICIO)).strftime('%d/%m/%Y')
    DATA_FIM = (HOJE + timedelta(days=DIAS_FIM)).strftime('%d/%m/%Y')


    total_pedidos = 0
    erro = None

    EMPRESAS: list[Empresa] = (
        database.session.query(Empresa)
        .filter(Empresa.cod_empresa_principal == EMPRESA_PRINCIPAL.cod)
        .all()
    )

    for empresa in EMPRESAS:
        for i in range(TENTATIVAS):
            print(f'{EMPRESA_PRINCIPAL.nome} - {empresa.razao_social} - {ACAO} {NOME_TABELA} - tentativa: {i + 1}/{TENTATIVAS}', end=' - ')
            try:
                qtd_pedidos = Pedido.inserir_pedidos(
                    id_empresa=empresa.id_empresa,
                    dataInicio=DATA_INICIO,
                    dataFim=DATA_FIM
                )
                total_pedidos = total_pedidos + qtd_pedidos
                print(f'Qtd: {qtd_pedidos}')
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
        message_body = str({NOME_TABELA: total_pedidos, 'Erro': erro})
    )
    if enviar_report['sent'] == 1:
        print(f'Enviado para: {DESTINATARIO}')
    else:
        print(f"Não enviado. ERRO: {enviar_report['error']}")
    
    print(f'Done! Total: {total_pedidos}')




