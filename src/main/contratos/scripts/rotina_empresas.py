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
    from manager.modules.contratos.models import Contrato

    infos: list[tuple] = []

    empresas: list[Empresa] = (
        database.session.query(Empresa)
        .filter(Empresa.contratos == True)
        .filter(Empresa.contratos_emails != None)
        .all()
    )

    corpo_email: str = EmailConnect.create_email_body(email_template_path='manager/email_templates/contratos.html')
    
    for empresa in empresas:
        print(empresa)

        infos.append(
            Contrato.rotina_contratos(
                id_empresa=empresa.id_empresa,
                corpo_email=corpo_email,
                testando=True
            )
        )


    # enviar report
    df = pd.DataFrame(infos)
    df = df[[
        'cod_empresa_principal',
        'nome_empresa_principal',
        'id_empresa',
        'razao_social',
        'emails',
        'nome_arquivo',
        'status',
        'tempo_execucao'
    ]]

    nome_arquivo = f'Report_Contratos_{int(datetime.now().timestamp())}.xlsx'
    df.to_excel(nome_arquivo, index=False, freeze_panes=(1,0))

    for i in range(3):
        try:
            EmailConnect.send_email(
                to_addr=['gabrielsantos@grsnucleo.com.br'],
                message_subject=f"Report Envio Contratos Empresas - {datetime.now(tz=TIMEZONE_SAO_PAULO).strftime('%d-%m-%Y %H:%M:%S')}",
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

