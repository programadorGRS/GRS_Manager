if __name__ == '__main__':
    import sys

    sys.path.append('../GRS_Manager')

    import os
    from datetime import datetime

    import pandas as pd

    from manager import TIMEZONE_SAO_PAULO, database
    from manager.email_connect import EmailConnect
    from manager.models import Empresa, EmpresaPrincipal, Unidade
    from manager.modules.conv_exames.models import (ConvExames,
                                                    PedidoProcessamento)

    registros = []

    empresas_manserv = [529769, 529768, 529759, 529765, 529766]

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
            if empresa.cod_empresa in empresas_manserv:
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
                id_unidade=unidade.id_unidade,
                corpo_email=email_body,
                testando=False,
                gerar_ppt=False,
                filtro_a_vencer=filtro_a_vencer,
                filtro_status=filtro_status
            )
            
            registros.append(dic)
        
    # enviar report
    df = pd.DataFrame(registros)

    nome_arquivo = f'report_conv_exames_unidades_{int(datetime.now().timestamp())}.xlsx'
    df.to_excel(nome_arquivo, index=False, freeze_panes=(1,0))

    try:
        EmailConnect.send_email(
            to_addr=['gabrielsantos@grsnucleo.com.br', 'jlaranjeira@grsnucleo.com.br'],
            message_subject=f"Report Conv Exames Unidades - {datetime.now(tz=TIMEZONE_SAO_PAULO).strftime('%d-%m-%Y %H:%M:%S')}",
            message_body='',
            message_attachments=[nome_arquivo]
        )
    except:
        pass

    try:
        os.remove(nome_arquivo)
    except:
        pass

    print('-----Fim-----')

