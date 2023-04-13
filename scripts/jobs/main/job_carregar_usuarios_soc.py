if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    from src import app
    from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
    from src.main.usuario_soc.usuario_soc import UsuarioSOC

    with app.app_context():
        # NOTE: apenas GRS
        EMPRESAS_PRINCIPAL: EmpresaPrincipal  = EmpresaPrincipal.query.get(423)
        TENTATIVAS = 4

        NOME_TABELA = 'UsuarioSOC'
        ACAO = 'Inserir'

        total_inseridos = 0
        erro = None

        for i in range(TENTATIVAS):
            print(f'{EMPRESAS_PRINCIPAL.nome} - {ACAO} {NOME_TABELA} - tentativa: {i + 1}/{TENTATIVAS}', end=' - ')
            try:
                ativos = UsuarioSOC.carregar_usuarios(cod_empresa_principal=EMPRESAS_PRINCIPAL.cod, ativo=1)
                inativos = UsuarioSOC.carregar_usuarios(cod_empresa_principal=EMPRESAS_PRINCIPAL.cod, ativo=0)
                
                qtd_inseridos = ativos.get('inseridos') + inativos.get('inseridos')
                print(f'Qtd: {qtd_inseridos}')
                total_inseridos = total_inseridos + qtd_inseridos
                
                break
            except Exception as exception:
                erro = type(exception).__name__
                print(f'ERRO: {erro}')
                continue

        print(f'Done! Total: {total_inseridos}')

