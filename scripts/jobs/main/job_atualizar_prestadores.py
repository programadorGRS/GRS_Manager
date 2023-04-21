if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    from src import app
    from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
    from src.main.prestador.prestador import Prestador

    with app.app_context():
        # NOTE: sempre inserir prestadores apenas da GRS
        EMPRESA_PRINCIPAL: EmpresaPrincipal = EmpresaPrincipal.query.get(423)
        TENTATIVAS = 4

        NOME_TABELA = 'Prestadores'
        ACAO = 'Atualizar'

        total_inseridos = 0
        erro = None

        for i in range(TENTATIVAS):
            print(f'{EMPRESA_PRINCIPAL.nome} - {ACAO} {NOME_TABELA} - tentativa: {i + 1}/{TENTATIVAS}', end=' - ')
            try:
                total_inseridos = Prestador.atualizar_prestadores(cod_empresa_principal=EMPRESA_PRINCIPAL.cod)
                print(f'Qtd: {total_inseridos}')
                break
            except Exception as exception:
                erro = type(exception).__name__
                print(f'ERRO: {erro}')
                continue

        print(f'Done! Total: {total_inseridos}')

