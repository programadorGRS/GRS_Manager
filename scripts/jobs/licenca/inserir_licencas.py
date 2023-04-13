if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    import os
    from datetime import datetime, timedelta
    from smtplib import SMTPException

    import pandas as pd

    from src import TIMEZONE_SAO_PAULO, app
    from src.email_connect import EmailConnect
    from src.main.empresa.empresa import Empresa
    from src.modules.absenteismo.models import Licenca

    with app.app_context():
        responses: list[dict] = []

        dias: int = 30
        data_inicio: datetime = datetime.now() - timedelta(days=dias)
        data_fim: datetime = datetime.now()

        empresas: list[Empresa] = Empresa.query.all()
        for empresa in empresas:
            print(empresa)
            responses.append(
                Licenca.inserir_licenca(
                    id_empresa = empresa.id_empresa,
                    dataInicio = data_inicio,
                    dataFim = data_fim
                )
            )


        print('Enviar report...')
        with pd.ExcelWriter('Licencas.xlsx') as writer:
            for i in ['geral', 'socind', 'licenca_med']:
                aux: list[dict] = [dic[i] for dic in responses]
                df = pd.DataFrame(aux)
                df.to_excel(writer, sheet_name=i, index=False, freeze_panes=(1,0))

        for i in range(3):
            try:
                EmailConnect.send_email(
                    to_addr = ['gabrielsantos@grsnucleo.com.br'],
                    message_subject = f"Report Licencas - {datetime.now(tz=TIMEZONE_SAO_PAULO).strftime('%d-%m-%Y %H:%M:%S')}",
                    message_body = '',
                    message_attachments=['Licencas.xlsx']
                )
                break
            except SMTPException:
                continue

        try:
            os.remove('Licencas.xlsx')
        except:
            pass

