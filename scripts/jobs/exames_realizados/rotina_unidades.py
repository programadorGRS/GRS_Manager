if __name__ == "__main__":
    import sys

    sys.path.append("../GRS_Manager")

    from datetime import datetime, timedelta

    from scripts.utils import set_app_config_by_os_name
    from src import app
    from src.email_connect import EmailConnect
    from src.extensions import database as db
    from src.main.exames_realizados.exames_realizados import ExamesRealizados
    from src.main.unidade.unidade import Unidade

    with app.app_context():
        set_app_config_by_os_name(app=app)

        REPLY_TO = ["gabrielsantos@grsnucleo.com.br", "relacionamento@grsnucleo.com.br"]

        dias: int = 90

        data_inicio = datetime.now() - timedelta(days=dias)
        data_fim = datetime.now()

        date_format = "%d/%m/%Y"

        print(
            "Enviando relatórios Exames Realizados Unidades | "
            "Periodo: "
            f"{data_inicio.strftime(date_format)}"
            " a "
            f"{data_fim.strftime(date_format)}"
        )

        total = 0
        erros = 0

        query_unidades = (
            db.session.query(Unidade)  # type: ignore
            .filter(Unidade.exames_realizados == True)  # noqa
            .filter(Unidade.exames_realizados_emails != None)  # noqa
        )

        lista_unidades: list[Unidade] = query_unidades.all()

        for unidade in lista_unidades:
            if not unidade.exames_realizados_emails:
                continue

            print(
                f"Cod: {unidade.cod_unidade} | Nome: {unidade.nome_unidade[:20]}",
                end=" | ",
            )

            corpo_email: str = EmailConnect.create_email_body(
                email_template_path="src/email_templates/exames_realizados.html",
                replacements={"PLACEHOLDER_DIAS": str(dias)},
            )

            try:
                res = ExamesRealizados.rotina_exames_realizados(
                    cod_empresa_principal=unidade.cod_empresa_principal,
                    id_empresa=unidade.id_empresa,
                    nome_empresa=unidade.empresa.razao_social,
                    id_unidade=unidade.id_unidade,
                    nome_unidade=unidade.nome_unidade,
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    emails_destinatario=unidade.exames_realizados_emails.split(";"),
                    corpo_email=corpo_email,
                    reply_to=REPLY_TO,
                )
            except Exception as e:
                erros += 1
                app.logger.error(e, exc_info=True)
                continue

            total += 1

            if not res:
                print("Sem resultado")
                erros += 1
                continue

            stt = res.get("status")
            qtd = res.get("qtd")

            if stt != "OK":
                erros += 1

            print(f"Status: {stt} | Qtd: {qtd}")

    print(f"Done! -> Total {total} | Erros {erros}")
