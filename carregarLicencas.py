if __name__ == '__main__':
    import sys
    sys.path.append('../GRS_Manager')

    from datetime import datetime, timedelta

    from manager.models import Empresa
    from manager.modules.absenteismo.models import Licenca

    qtd = 0
    
    empresas: list[Empresa] = Empresa.query.all()

    data_inicio: datetime = datetime(2021, 1, 1)
    data_fim: datetime = data_inicio + timedelta(days=30)

    while data_fim <= datetime.now():
        for empresa in empresas:
            resultado = Licenca.inserir_licenca(
                    id_empresa = empresa.id_empresa,
                    dataInicio = data_inicio,
                    dataFim = data_fim
                )
            print(f'{empresa.id_empresa}-{empresa.razao_social[:51]}: {data_inicio.strftime("%d-%m-%Y")} - {data_fim.strftime("%d-%m-%Y")} = {resultado["geral"]["status"]}: {resultado["geral"]["qtd"]}')
            qtd = qtd + resultado["geral"]["qtd"]

        data_inicio = data_fim + timedelta(days=1)
        data_fim = data_inicio + timedelta(days=30)
    
    print(f'FIM: QTD = {qtd}')

