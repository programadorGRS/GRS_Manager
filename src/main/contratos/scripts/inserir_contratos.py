if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    import os
    from datetime import datetime
    from smtplib import SMTPException

    import pandas as pd

    from manager import TIMEZONE_SAO_PAULO, database
    from manager.email_connect import EmailConnect
    from manager.models import Empresa, Unidade
    from manager.modules.contratos.models import Contrato


    # limpar tabela
    Contrato.query.delete()
    database.session.commit()


    responses: list[dict] = []

    empresas: list[Empresa] = Empresa.query.all()
    for empresa in empresas:
        unidades: list[Unidade] = (
            database.session.query(Unidade.id_unidade)
            .filter(Unidade.id_empresa == empresa.id_empresa)
            .all()
        )
        unidades = [unidade.id_unidade for unidade in unidades]
        # inserir zero no comeco da lista para buscar contratos sem unidade
        unidades.insert(0, 0)

        for unidade in unidades:
            print(f'{empresa.nome_abrev} - {unidade}')
            responses.append(
                Contrato.inserir_contratos(
                    id_empresa=empresa.id_empresa,
                    id_unidade=unidade
                )
            )

    print('Enviar report...')
    df = pd.DataFrame(responses)
    df.to_excel('Contratos.xlsx', index=False, freeze_panes=(1,0))

    # enviar report
    for i in range(3):
        try:
            EmailConnect.send_email(
                to_addr = ['gabrielsantos@grsnucleo.com.br'],
                message_subject = f"Report Contratos inseridos - {datetime.now(tz=TIMEZONE_SAO_PAULO).strftime('%d-%m-%Y %H:%M:%S')}",
                message_body = '',
                message_attachments=['Contratos.xlsx']
            )
            break
        except SMTPException:
            continue

    try:
        os.remove('Contratos.xlsx')
    except:
        pass

