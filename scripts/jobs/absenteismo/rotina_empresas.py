if __name__ == "__main__":
    import sys

    sys.path.append("../GRS_Manager")

    from datetime import datetime, timedelta

    from scripts.utils import set_app_config_by_os_name
    from src import app
    from src.email_connect import EmailConnect
    from src.extensions import database as db
    from src.main.absenteismo.absenteismo import Absenteismo
    from src.main.empresa.empresa import Empresa

    with app.app_context():
        set_app_config_by_os_name(app=app)

        dias: int = 90

        query_empresas = (
            db.session.query(Empresa)  # type: ignore
            .filter(Empresa.absenteismo == True)  # noqa
            .filter(Empresa.absenteismo_emails != None)  # noqa
        )

        lista_empresas: list[Empresa] = query_empresas.all()

        for empresa in lista_empresas:
            if not empresa.absenteismo_emails:
                continue

            print(
                f"Cod: {empresa.cod_empresa} | Nome: {empresa.razao_social[:20]}",
                end=" | ",
            )

            corpo_email: str = EmailConnect.create_email_body(
                email_template_path="src/email_templates/absenteismo.html",
                replacements={"PLACEHOLDER_DIAS": str(dias)},
            )

            try:
                res = Absenteismo.rotina_absenteismo(
                    cod_empresa_principal=empresa.cod_empresa_principal,
                    id_empresa=empresa.id_empresa,
                    nome_empresa=empresa.razao_social,
                    data_inicio=datetime.now() - timedelta(days=dias),
                    data_fim=datetime.now(),
                    emails_destinatario=empresa.absenteismo_emails.split(";"),
                    corpo_email=corpo_email,
                    testando=False,
                )
            except Exception as e:
                app.logger.error(e, exc_info=True)
                continue

            if not res:
                print("Sem resultado")
                continue

            print(f"Status: {res.get('status')} | Qtd: {res.get('qtd')}")

    print("Done!")
