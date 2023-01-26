if __name__ == '__main__':
    import sys
    sys.path.append('../Projeto_Manager')

    from datetime import datetime

    from manager import database
    from manager.models import *


    for emp in EmpresaPrincipal.query.all():
        print(emp)
        empresas = [e.id_empresa for e in Empresa.query.filter_by(cod_empresa_principal=emp.cod).all()]
        if not emp.socnet:
            qtd = Pedido.inserir_pedidos(
                cod_empresa_principal=emp.cod,
                dataInicio=(datetime.now() - timedelta(days=31)).strftime('%d/%m/%Y'),
                dataFim=datetime.now().strftime('%d/%m/%Y')
            )
            print(f'Pedidos inseridos: {qtd}')
    print('Fim')