if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    import os
    from datetime import datetime
    from smtplib import SMTPException

    import pandas as pd

    from manager import TIMEZONE_SAO_PAULO, database
    from manager.email_connect import EmailConnect
    from manager.models import Empresa
    from manager.modules.conv_exames.models import PedidoProcessamento, ConvExames


    # deletar Convocacoes anteriores
    ConvExames.query.delete()
    # deletar pedidos anteriores
    PedidoProcessamento.query.delete()
    database.session.commit()


    # criar pedidos novos
    empresas: list[Empresa] = Empresa.query.all()

    responses: list[dict] = []
    for empresa in empresas:
        print(empresa)
        responses.append(PedidoProcessamento.criar_pedido_processamento(id_empresa=empresa.id_empresa))
    
    print('Enviar report...')
    df = pd.DataFrame(responses)
    df.to_excel('PedidosProcessamento.xlsx', index=False, freeze_panes=((1,0)))

    for i in range(3):
        try:
            EmailConnect.send_email(
                to_addr = ['gabrielsantos@grsnucleo.com.br'],
                message_subject = f"Report Pedidos de Processamento - {datetime.now(tz=TIMEZONE_SAO_PAULO).strftime('%d-%m-%Y %H:%M:%S')}",
                message_body = '',
                message_attachments = ['PedidosProcessamento.xlsx']
            )
            break
        except SMTPException:
            continue

    try:
        os.remove('PedidosProcessamento.xlsx')
    except:
        pass

