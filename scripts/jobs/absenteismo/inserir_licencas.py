if __name__ == "__main__":
    import sys

    sys.path.append("../GRS_Manager")

    from datetime import datetime, timedelta

    from scripts.utils import set_app_config_by_os_name
    from src import app
    from src.main.absenteismo.absenteismo import Absenteismo
    from src.main.empresa.empresa import Empresa

    with app.app_context():
        set_app_config_by_os_name(app=app)

        dias: int = 30
        data_inicio: datetime = datetime.now() - timedelta(days=dias)
        data_fim: datetime = datetime.now()

        empresas: list[Empresa] = Empresa.query.all()

        for empresa in empresas:
            print(
                f"Cod: {str(empresa.cod_empresa).zfill(8)} | "
                f"Nome: {empresa.razao_social.strip()[:20].ljust(20, ' ')}",
                end=" | ",
            )

            try:
                res = Absenteismo.inserir_licenca(
                    id_empresa=empresa.id_empresa,
                    dataInicio=data_inicio,
                    dataFim=data_fim,
                )
            except Exception as e:
                app.logger.error(e, exc_info=True)
                continue

            stt: str = res["status"]
            qtd: int = res["qtd"]

            print(f"Status: {stt.ljust(20)} | Qtd: {qtd}")

    print("Done!")
