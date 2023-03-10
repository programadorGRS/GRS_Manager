if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    import os
    from datetime import datetime
    from smtplib import SMTPException

    import pandas as pd

    from manager import TIMEZONE_SAO_PAULO, database
    from manager.email_connect import EmailConnect
    from manager.modules.conv_exames.models import (ConvExames,
                                                    PedidoProcessamento)


    pedidos_proc: list[PedidoProcessamento] = (
        database.session.query(PedidoProcessamento)
        .filter(PedidoProcessamento.resultado_importado == False)
        .all()
    )

    responses: list[dict] = []
    for ped_proc in pedidos_proc:
        print(ped_proc)
        responses.append(ConvExames.inserir_conv_exames(id_proc=ped_proc.id_proc))

    print('Enviar report...')
    df = pd.DataFrame(responses)
    df.to_excel('ConvExames.xlsx', index=False, freeze_panes=(1,0))

    for i in range(3):
        try:
            EmailConnect.send_email(
                to_addr=['gabrielsantos@grsnucleo.com.br'],
                message_subject=f"Report Conv Exames - {datetime.now(tz=TIMEZONE_SAO_PAULO).strftime('%d-%m-%Y %H:%M:%S')}",
                message_body='',
                message_attachments=['ConvExames.xlsx']
            )
            break
        except SMTPException:
            continue

    try:
        os.remove('ConvExames.xlsx')
    except:
        pass

