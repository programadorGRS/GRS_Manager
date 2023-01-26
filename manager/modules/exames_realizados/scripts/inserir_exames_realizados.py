if __name__ == '__main__':
    import sys
    sys.path.append('../Projeto_Manager')

    import os
    from datetime import datetime, timedelta
    from smtplib import SMTPException

    import pandas as pd

    from manager import TIMEZONE_SAO_PAULO
    from manager.email_connect import EmailConnect
    from manager.models import Empresa
    from manager.modules.exames_realizados.models import ExamesRealizados

    responses: list[dict] = []

    dias: int = 30
    data_inicio: datetime = datetime.now(tz=TIMEZONE_SAO_PAULO) - timedelta(days=dias)
    data_fim: datetime = datetime.now(tz=TIMEZONE_SAO_PAULO)

    empresas: list[Empresa] = Empresa.query.all()
    for empresa in empresas:
        print(empresa)
        responses.append(
            ExamesRealizados.inserir_exames_realizados(
            id_empresa = empresa.id_empresa,
            dataInicio = data_inicio,
            dataFim = data_fim
            )
        )

    print('Enviar report...')
    df = pd.DataFrame(responses)
    df.to_excel('ExamesRealizados.xlsx', index=False, freeze_panes=(1,0))

    # enviar report
    for i in range(3):
        try:
            EmailConnect.send_email(
                to_addr = ['gabrielsantos@grsnucleo.com.br'],
                message_subject = f"Report Exames Realizados - {datetime.now(tz=TIMEZONE_SAO_PAULO).strftime('%d-%m-%Y %H:%M:%S')}",
                message_body = '',
                message_attachments=['ExamesRealizados.xlsx']
            )
            break
        except SMTPException:
            continue

    try:
        os.remove('ExamesRealizados.xlsx')
    except:
        pass

