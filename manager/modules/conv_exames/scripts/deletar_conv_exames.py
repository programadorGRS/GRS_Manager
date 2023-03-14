if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    from datetime import datetime, timedelta

    from sqlalchemy import delete

    from manager import TIMEZONE_SAO_PAULO, database
    from manager.modules.conv_exames.models import (ConvExames,
                                                    PedidoProcessamento)


    HOJE = datetime.now(TIMEZONE_SAO_PAULO).date()
    DIAS = 4
    DATA_LIMITE = HOJE - timedelta(days=DIAS)


    query_pedidos_proc = (
        database.session.query(PedidoProcessamento)
        .filter(PedidoProcessamento.data_criacao <= DATA_LIMITE)
        .all()
    )

    PEDIDOS_PROC: list[int] = [i.id_proc for i in query_pedidos_proc]

    if PEDIDOS_PROC:
        print(f'Deletando PedidosProcessamento: {PEDIDOS_PROC}')

        database.session.execute(
            delete(ConvExames)
            .where(ConvExames.id_proc.in_(PEDIDOS_PROC))
        )

        database.session.execute(
            delete(PedidoProcessamento)
            .where(PedidoProcessamento.id_proc.in_(PEDIDOS_PROC))
        )

        database.session.commit()

    print('Done!')

