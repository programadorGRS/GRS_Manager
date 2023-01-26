#!~/GRS_Manager/venv/bin/python3

# jobs padrao da database, realizados a cada x horas


if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    from datetime import datetime, timedelta
    from manager.email import enviar_report
    from manager.models import Pedido, Empresa, Unidade, EmpresaPrincipal, Prestador, Exame


    total_empresas = 0
    total_unidades = 0
    total_exames = 0
    total_prestadores = 0
    total_tags = 0
    total_pedidos = 0
    for emp in EmpresaPrincipal.query.all():
        print(emp)
        
        empresas = Empresa.atualizar_empresas(emp.cod)
        unidades = Unidade.atualizar_unidades(emp.cod)
        exames = Exame.atualizar_exames(emp.cod)

        total_empresas = total_empresas + empresas
        total_unidades = total_unidades + unidades
        total_exames = total_exames + exames

        if not emp.socnet:
            prestadores = Prestador.atualizar_prestadores(emp.cod)

            total_prestadores = total_prestadores + prestadores

            # obs: o total de tags atualizadas sai maior do que o total de pedidos existentes \
            # porque atualmente, ele atualiza o mesmo pedido varias vezes
            tags = Pedido.atualizar_tags_prev_liberacao() 
            total_tags = total_tags + tags

            # atualizar nos ultimos 90 dias
            data_inicio = datetime.now() - timedelta(days=90)
            data_fim = data_inicio + timedelta(days=31)
            while data_inicio <= datetime.now():
                pedidos = Pedido.atualizar_pedidos(
                    cod_empresa_principal=emp.cod,
                    dataInicio=data_inicio.strftime('%d/%m/%Y'),
                    dataFim=data_fim.strftime('%d/%m/%Y')
                )

                data_inicio = data_fim + timedelta(days=1)
                data_fim = data_inicio + timedelta(days=31)

                total_pedidos = total_pedidos + pedidos



    print('Enviando report...')
    enviar_report(
        subj='jobs_atualizar executado',
        send_to=['gabrielsantos@grsnucleo.com.br'],
        body=str({
            'Empresas': total_empresas,
            'Unidades': total_unidades,
            'Prestadores': total_prestadores,
            'Exames': total_exames,
            'TagsPedidos': total_tags,
            'Pedidos:': total_pedidos
        })
    )
