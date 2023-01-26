if __name__ == '__main__':
    import sys
    sys.path.append('../Projeto_Manager')

    from datetime import datetime

    from manager import database
    from manager.models import *
    from manager.modules.exames_realizados.models import ExamesRealizados


    for emp in EmpresaPrincipal.query.all():

        empresas = [e.id_empresa for e in Empresa.query.filter_by(cod_empresa_principal=emp.cod).all()]

        qtd = ExamesRealizados.inserir_exames(
            cod_empresa_principal=emp.cod,
            lista_empresas=empresas,
            dataInicio=(datetime.now() - timedelta(days=31)).strftime('%d/%m/%Y'),
            dataFim=datetime.now().strftime('%d/%m/%Y')
        )
        print(f'ExamesRealizados inseridos: {qtd}')
    print('Fim')