if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    from manager.email import enviar_report
    from manager.models import Empresa, EmpresaPrincipal, Funcionario

    total_funcionarios = 0
    for emp in EmpresaPrincipal.query.all():
        print(emp)

        empresas = [i.id_empresa for i in Empresa.query.filter_by(cod_empresa_principal=emp.cod)]
        
        print('Inserindo Funcionarios...')
        
        qtd_funcionarios = Funcionario.inserir_funcionarios(
            cod_empresa_principal=emp.cod,
            lista_empresas=empresas
        )
        total_funcionarios = total_funcionarios + qtd_funcionarios

    print('Enviando report...')
    enviar_report(
        subj='jobs_inserir2 executado',
        send_to=['gabrielsantos@grsnucleo.com.br'],
        body=str({'Funcionarios': total_funcionarios})
    )

    print('Fim')

