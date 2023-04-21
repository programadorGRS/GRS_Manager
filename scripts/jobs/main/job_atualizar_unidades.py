if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    from src import app
    from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
    from src.main.unidade.unidade import Unidade

    with app.app_context():
        EMPRESAS_PRINCIPAIS: list[EmpresaPrincipal]  = EmpresaPrincipal.query.all()
        TENTATIVAS = 4

        NOME_TABELA = 'Unidades'
        ACAO = 'Atualizar'


        total_inseridos = 0
        erro = None

        for empresa_principal in EMPRESAS_PRINCIPAIS:
            for i in range(TENTATIVAS):
                print(f'{empresa_principal.nome} - {ACAO} {NOME_TABELA} - tentativa: {i + 1}/{TENTATIVAS}', end=' - ')
                try:
                    qtd_inseridos = Unidade.atualizar_unidades(cod_empresa_principal=empresa_principal.cod)
                    print(f'Qtd: {qtd_inseridos}')
                    total_inseridos = total_inseridos + qtd_inseridos
                    break
                except Exception as exception:
                    erro = type(exception).__name__
                    print(f'ERRO: {erro}')
                    continue

        print(f'Done! Total: {total_inseridos}')

