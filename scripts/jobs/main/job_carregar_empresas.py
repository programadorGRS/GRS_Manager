if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    from src import app
    from src.main.empresa.empresa import Empresa
    from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
    from src.main.job.job import Job


    with app.app_context():
        EMPRESAS_PRINCIPAIS: list[EmpresaPrincipal] = EmpresaPrincipal.query.all()

        print('Carregar Empresas...')
        for empresa in EMPRESAS_PRINCIPAIS:
            print(f'{empresa.cod} - {empresa.nome}', end=' - ')

            infos = Empresa.carregar_empresas(cod_empresa_principal=empresa.cod)

            Job.log_job(infos=infos)

            if infos.erro:
                print(f'ERRO: {infos.erro}')
                continue

            print(f'Inseridos: {infos.qtd_inseridos} - Atualizados: {infos.qtd_atualizados}')

