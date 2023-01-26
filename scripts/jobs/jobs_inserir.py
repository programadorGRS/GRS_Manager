#!~/GRS_Manager/venv/bin/python3

# jobs padrao da database, realizados a cada x horas


if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    from manager.email import enviar_report
    from manager.models import Pedido, Empresa, Unidade, EmpresaPrincipal, Prestador, Exame
    
    from datetime import datetime, timedelta
    from pytz import timezone
    import sys

    total_empresas = 0
    total_unidades = 0
    total_exames = 0
    total_prestadores = 0
    total_pedidos = 0

    for emp in EmpresaPrincipal.query.all():
        
        print(emp)
        
        empresas = Empresa.inserir_empresas(emp.cod)
        unidades = Unidade.inserir_unidades(emp.cod)
        exames = Exame.inserir_exames(emp.cod)

        total_empresas = total_empresas + empresas
        total_unidades = total_unidades + unidades
        total_exames = total_exames + exames

        if not emp.socnet:
            prestadores = Prestador.inserir_prestadores(emp.cod)

            total_prestadores = total_prestadores + prestadores
            
            # atualizar nos ultimos 3 dias
            data_inicio = (datetime.now(tz=timezone('America/Sao_Paulo')) - timedelta(days=3)).strftime('%d/%m/%Y')
            data_fim = datetime.now(tz=timezone('America/Sao_Paulo')).strftime('%d/%m/%Y')

            # tentar inserir pedidos
            tentativas = 4
            for i in range(tentativas):
                try:
                    pedidos = Pedido.inserir_pedidos(cod_empresa_principal=emp.cod, dataInicio=data_inicio, dataFim=data_fim)
                    
                    total_pedidos = total_pedidos + pedidos
                    
                    break
                except Exception as exception:
                    pedidos = f'ERRO: {type(exception).__name__}'
                    continue
                

    print('Enviando report...')
    enviar_report(
        subj='jobs_inserir executado',
        send_to=['gabrielsantos@grsnucleo.com.br'],
        body=str({
            'Empresas': total_empresas,
            'Unidades': total_unidades,
            'Prestadores': total_prestadores,
            'Exames': total_exames,
            'Pedidos': total_pedidos
        })
    )

    print('Fim')
