if __name__ == '__main__':
    import sys

    sys.path.append('../GRS_Manager')

    import os
    from datetime import datetime

    import pandas as pd

    from src import TIMEZONE_SAO_PAULO, app, database
    from src.email_connect import EmailConnect
    from src.main.empresa.empresa import Empresa
    from src.main.unidade.unidade import Unidade
    from src.main.conv_exames.models import ConvExames, PedidoProcessamento

    with app.app_context():
        TESTANDO = False
        GERAR_PPT = False

        TENTATIVAS_EMAIL = 3
        INTERVALO_EMAIL = 60 # segundos
        DEST_REPORT = ['gabrielsantos@grsnucleo.com.br'] #'jlaranjeira@grsnucleo.com.br'

        EMPRESAS_MANSERV = (529769, 529768, 529759, 529765, 529766)

        registros: list[dict] = []

        unidades: list[Unidade] = (
            database.session.query(Unidade)
            .filter(Unidade.conv_exames == True)
            .all()
        )
        
        for unidade in unidades:
            print(unidade)
            empresa: Empresa = Empresa.query.get(unidade.id_empresa)

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
                    template = 'src/email_templates/conv_exames_manserv.html'
                    filtro_a_vencer = [30, pd.NA]
                    filtro_status = ['Vencido', 'A vencer', 'Pendente', 'Sem histórico']
                else:
                    template = 'src/email_templates/conv_exames.html'
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
                    id_unidade=unidade.id_unidade,
                    corpo_email=email_body,
                    testando=TESTANDO,
                    gerar_ppt=GERAR_PPT,
                    filtro_a_vencer=filtro_a_vencer,
                    filtro_status=filtro_status,
                    tentativas_email=TENTATIVAS_EMAIL,
                    intervalo_tentativas=INTERVALO_EMAIL
                )
                registros.append(dic)


        print("Enviando Report...")
        df = pd.DataFrame(registros)
        nome_arquivo = f'report_conv_exames_unidades_{int(datetime.now().timestamp())}.xlsx'
        df.to_excel(nome_arquivo, index=False, freeze_panes=(1,0))

        EmailConnect.send_email(
            to_addr=DEST_REPORT,
            message_subject=f"Report Envios Conv Exames Unidades - {datetime.now(tz=TIMEZONE_SAO_PAULO).strftime('%d-%m-%Y %H:%M:%S')}",
            message_body='',
            message_attachments=[nome_arquivo],
            send_attempts=TENTATIVAS_EMAIL,
            attempt_delay=INTERVALO_EMAIL
        )

        try:
            os.remove(nome_arquivo)
        except:
            pass

