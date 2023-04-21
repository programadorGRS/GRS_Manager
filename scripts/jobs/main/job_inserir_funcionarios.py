if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    from src import app, database
    from src.main.empresa.empresa import Empresa
    from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
    from src.main.funcionario.funcionario import Funcionario

    with app.app_context():
        EMPRESAS_PRINCIPAIS: list[EmpresaPrincipal]  = EmpresaPrincipal.query.all()
        TENTATIVAS = 4

        NOME_TABELA = 'Funcionarios'
        ACAO = 'Inserir'


        total = 0
        erro = None

        for empresa_principal in EMPRESAS_PRINCIPAIS:
            empresas: list[Empresa] = (
                database.session.query(Empresa)
                .filter(Empresa.cod_empresa_principal == empresa_principal.cod)
                .all()
            )
            for empresa in empresas:
                for i in range(TENTATIVAS):
                    print(f'{empresa_principal.nome} - {empresa.razao_social} - {ACAO} {NOME_TABELA} - tentativa: {i + 1}/{TENTATIVAS}', end=' - ')
                    try:
                        qtd = Funcionario.inserir_funcionarios(id_empresa=empresa.id_empresa)
                        print(f'Qtd: {qtd}')
                        total = total + qtd
                        break
                    except Exception as exception:
                        erro = type(exception).__name__
                        print(f'ERRO: {erro}')
                        continue

        print(f'Done! Total: {total}')

