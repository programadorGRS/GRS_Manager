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
    from src.main.unidade.unidade import Unidade

    with app.app_context():
        set_app_config_by_os_name(app=app)

        dias: int = 90

        query_unidades = (
            db.session.query(Unidade)  # type: ignore
            .filter(Unidade.absenteismo == True)  # noqa
            .filter(Unidade.absenteismo_emails != None)  # noqa
        )

        lista_unidades: list[Unidade] = query_unidades.all()

        for unidade in lista_unidades:
            if not unidade.absenteismo_emails:
                continue

            print(
                f"Cod: {unidade.cod_unidade} | Nome: {unidade.nome_unidade[:20]}",
                end=" | ",
            )

            empresa: Empresa = Empresa.query.get(unidade.id_empresa)

            corpo_email: str = EmailConnect.create_email_body(
                email_template_path="src/email_templates/absenteismo.html",
                replacements={"PLACEHOLDER_DIAS": str(dias)},
            )

            try:
                res = Absenteismo.rotina_absenteismo(
                    cod_empresa_principal=unidade.cod_empresa_principal,
                    id_empresa=empresa.id_empresa,
                    nome_empresa=empresa.razao_social,
                    id_unidade=unidade.id_unidade,
                    nome_unidade=unidade.nome_unidade,
                    data_inicio=datetime.now() - timedelta(days=dias),
                    data_fim=datetime.now(),
                    emails_destinatario=unidade.absenteismo_emails.split(";"),
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
