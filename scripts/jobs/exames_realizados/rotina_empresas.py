if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    import os
    from datetime import datetime, timedelta
    from smtplib import SMTPException

    import pandas as pd

    from src import TIMEZONE_SAO_PAULO, app, database
    from src.email_connect import EmailConnect
    from src.main.empresa.empresa import Empresa
    from src.modules.exames_realizados.models import ExamesRealizados

    with app.app_context():
        dias: int = 90
        infos: list[tuple] = []

        empresas: list[Empresa] = (
            database.session.query(Empresa)
            .filter(Empresa.exames_realizados == True)
            .all()
        )
        for empresa in empresas:
            print(empresa)

            if empresa.exames_realizados_emails:
                corpo_email: str = EmailConnect.create_email_body(
                    email_template_path='src/email_templates/exames_realizados.html',
                    replacements={'PLACEHOLDER_DIAS': str(dias)}
                )

                infos.append(
                    ExamesRealizados.rotina_exames_realizados(
                        cod_empresa_principal=empresa.cod_empresa_principal,
                        id_empresa=empresa.id_empresa,
                        nome_empresa=empresa.razao_social,
                        data_inicio=datetime.now() - timedelta(days=dias),
                        data_fim=datetime.now(),
                        emails_destinatario=empresa.exames_realizados_emails.split(';'),
                        corpo_email=corpo_email,
                        testando=False
                    )
                )


        # enviar report
        df = pd.DataFrame(
            infos,
            columns=[
                'id_empresa',
                'nome_empresa',
                'id_unidade',
                'nome_unidade',
                'emails',
                'qtd_linhas',
                'status_email'
            ]
        )

        nome_arquivo = f'Report_ExamesRealizados_{int(datetime.now().timestamp())}.xlsx'
        df.to_excel(nome_arquivo, index=False, freeze_panes=(1,0))

        for i in range(3):
            try:
                EmailConnect.send_email(
                    to_addr=['gabrielsantos@grsnucleo.com.br'],
                    message_subject=f"Report ExamesRealizados Empresas - {datetime.now(tz=TIMEZONE_SAO_PAULO).strftime('%d-%m-%Y %H:%M:%S')}",
                    message_attachments=[nome_arquivo],
                    message_body=''
                )
                break
            except SMTPException:
                continue

        try:
            os.remove(nome_arquivo)
        except:
            pass

