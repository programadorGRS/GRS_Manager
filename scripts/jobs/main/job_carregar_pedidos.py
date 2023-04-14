if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    from datetime import datetime, timedelta

    from src import TIMEZONE_SAO_PAULO, app, database
    from src.main.empresa.empresa import Empresa
    from src.main.job.job import Job
    from src.main.pedido.pedido import Pedido


    with app.app_context():
        # NOTE: carregar pedidos apenas da base GRS
        COD_GRS = 423

        HOJE = datetime.now(tz=TIMEZONE_SAO_PAULO)
        DIAS_INICIO = 5
        DIAS_FIM = 3
        DATA_INICIO = (HOJE - timedelta(days=DIAS_INICIO)).strftime('%d/%m/%Y')
        DATA_FIM = (HOJE + timedelta(days=DIAS_FIM)).strftime('%d/%m/%Y')

        query_empresas: list[Empresa] = (
            database.session.query(Empresa)
            .filter(Empresa.cod_empresa_principal == COD_GRS)
            .all()
        )

        print('Carregar Pedidos da Base GRS...')
        for empresa in query_empresas:
            print(f'{empresa.id_empresa} - {empresa.razao_social}', end=' - ')

            infos = Pedido.carregar_pedidos(
                id_empresa=empresa.id_empresa,
                dataInicio=DATA_INICIO,
                dataFim=DATA_FIM
            )

            Job.log_job(infos=infos)

            if infos.erro:
                print(f'ERRO: {infos.erro}')
                continue

            print(f'Inseridos: {infos.qtd_inseridos} - Atualizados: {infos.qtd_atualizados}')

