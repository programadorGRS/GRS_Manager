if __name__ == "__main__":
    import sys

    sys.path.append("../GRS_Manager")

    from datetime import datetime, timedelta

    from scripts.utils import set_app_config_by_os_name
    from src import app
    from src.main.empresa.empresa import Empresa
    from src.main.exames_realizados.exames_realizados import ExamesRealizados

    with app.app_context():
        set_app_config_by_os_name(app=app)

        dias: int = 30
        data_inicio: datetime = datetime.now() - timedelta(days=dias)
        data_fim: datetime = datetime.now()

        date_format = "%d/%m/%Y"

        print(
            "Inserindo Exames Realizados | "
            "Período: "
            f"{data_inicio.strftime(date_format)}"
            " a "
            f"{data_fim.strftime(date_format)}"
        )

        total = 0
        inseridos = 0
        erros = 0

        empresas: list[Empresa] = Empresa.query.all()

        for empresa in empresas:
            print(
                f"Cod: {empresa.cod_empresa} | Nome: {empresa.razao_social[:20]}",
                end=" | ",
            )

            try:
                res = ExamesRealizados.inserir_exames_realizados(
                    id_empresa=empresa.id_empresa,
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                )
            except Exception as e:
                app.logger.error(e, exc_info=True)
                continue

            total += 1

            stt: str | None = res.get("status")
            qtd: int | None = res.get("qtd")

            if stt != "OK":
                erros += 1

            if qtd:
                inseridos += qtd

            print(f"Status: {stt} | Qtd: {qtd}")

    print(f"Done! -> Total {total} | Inseridos {inseridos} | Erros: {erros}")
