if __name__ == '__main__':
    import sys

    sys.path.append('../GRS_Manager')

    import os
    import time
    from datetime import datetime

    import pandas as pd

    from manager import TIMEZONE_SAO_PAULO, database
    from manager.email_connect import EmailConnect
    from manager.models import Empresa
    from manager.modules.conv_exames.models import (ConvExames,
                                                    PedidoProcessamento)

    TENTATIVAS_EMAIL = 3
    INTERVALO_EMAIL = 60 # segundos

    TESTANDO = False
    DEST_REPORT = ['gabrielsantos@grsnucleo.com.br'] #'jlaranjeira@grsnucleo.com.br'

    EMPRESAS_MANSERV = (529769, 529768, 529759, 529765, 529766)

    registros: list[dict] = []

    empresas: list[Empresa] = (
        database.session.query(Empresa)
        .filter(Empresa.conv_exames == True)
        .all()
    )
    
    for empresa in empresas:
        print(empresa)

        # buscar ped proc mais recente
        ped_proc: PedidoProcessamento = (
            database.session.query(PedidoProcessamento)
            .filter(PedidoProcessamento.id_empresa == empresa.id_empresa)
            .filter(PedidoProcessamento.resultado_importado == True)
            .order_by(PedidoProcessamento.id_proc.desc())
            .first()
        )

        if ped_proc:
            if empresa.cod_empresa in EMPRESAS_MANSERV:
                template = 'manager/email_templates/conv_exames_manserv.html'
                filtro_a_vencer = [30, pd.NA]
                filtro_status = ['Vencido', 'A vencer', 'Pendente', 'Sem histórico']
            else:
                template = 'manager/email_templates/conv_exames.html'
                filtro_a_vencer = None
                filtro_status = None

            email_body: str = EmailConnect.create_email_body(
                email_template_path=template,
                replacements={
                    'PED_PROC_PLACEHOLDER': str(ped_proc.cod_solicitacao),
                    'DATA_CRIACAO_PLACEHOLDER': ped_proc.data_criacao.strftime('%d/%m/%Y')
                }
            )
            
            dic = ConvExames.rotina_conv_exames(
                id_proc=ped_proc.id_proc,
                corpo_email=email_body,
                testando=TESTANDO,
                gerar_ppt=True,
                filtro_a_vencer=filtro_a_vencer,
                filtro_status=filtro_status
            )
            registros.append(dic)


    # enviar report
    df = pd.DataFrame(registros)
    nome_arquivo = f'report_conv_exames_empresas_{int(datetime.now().timestamp())}.xlsx'
    df.to_excel(nome_arquivo, index=False, freeze_panes=(1,0))

    for _ in range(TENTATIVAS_EMAIL):
        try:
            EmailConnect.send_email(
                to_addr=DEST_REPORT,
                message_subject=f"Report Envios Conv Exames Empresas - {datetime.now(tz=TIMEZONE_SAO_PAULO).strftime('%d-%m-%Y %H:%M:%S')}",
                message_body='',
                message_attachments=[nome_arquivo]
            )
            break
        except:
            time.sleep(INTERVALO_EMAIL)
            continue

    try:
        os.remove(nome_arquivo)
    except:
        pass

