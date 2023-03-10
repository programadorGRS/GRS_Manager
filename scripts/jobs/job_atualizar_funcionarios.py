if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    from datetime import datetime
    from os.path import basename

    from manager import TIMEZONE_SAO_PAULO, database
    from manager.email_connect import EmailConnect
    from manager.models import Empresa, EmpresaPrincipal, Funcionario


    EMPRESAS_PRINCIPAIS: list[EmpresaPrincipal]  = EmpresaPrincipal.query.all()
    TENTATIVAS = 4

    NOME_TABELA = 'Funcionarios'
    ACAO = 'Atualizar'


    total = 0
    erro = None

    for empresa_principal in EMPRESAS_PRINCIPAIS:
        empresas: list[Empresa] = (
            database.session.query(Empresa)
            .filter(Empresa.cod_empresa_principal == empresa_principal.cod)
            .all()
        )
        for empresa in empresas:
            for i in range(TENTATIVAS):
                print(f'{empresa_principal.nome} - {empresa.razao_social} - {ACAO} {NOME_TABELA} - tentativa: {i + 1}/{TENTATIVAS}', end=' - ')
                try:
                    qtd = Funcionario.atualizar_funcionarios(id_empresa=empresa.id_empresa)
                    print(f'Qtd: {qtd}')
                    total = total + qtd
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
        message_body = str({NOME_TABELA: total, 'Erro': erro})
    )
    if enviar_report['sent'] == 1:
        print(f'Enviado para: {DESTINATARIO}')
    else:
        print(f"Não enviado. ERRO: {enviar_report['error']}")
    
    print(f'Done! Total: {total}')

