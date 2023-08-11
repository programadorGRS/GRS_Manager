if __name__ == "__main__":
    import sys

    sys.path.append("../GRS_Manager")

    from scripts.utils import set_app_config_by_os_name
    from src import app
    from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
    from src.main.exame.exame import Exame

    with app.app_context():
        set_app_config_by_os_name(app=app)

        EMPRESAS_PRINCIPAIS: list[EmpresaPrincipal] = EmpresaPrincipal.query.all()
        TENTATIVAS = 4

        NOME_TABELA = "Exames"
        ACAO = "Atualizar"

        total_inseridos = 0
        erro = None

        for empresa_principal in EMPRESAS_PRINCIPAIS:
            for i in range(TENTATIVAS):
                print(
                    f"{empresa_principal.nome} - {ACAO} {NOME_TABELA} - tentativa: {i + 1}/{TENTATIVAS}",
                    end=" - ",
                )
                try:
                    qtd_inseridos = Exame.atualizar_exames(
                        cod_empresa_principal=empresa_principal.cod
                    )
                    print(f"Qtd: {qtd_inseridos}")
                    total_inseridos = total_inseridos + qtd_inseridos
                    break
                except Exception as exception:
                    erro = type(exception).__name__
                    print(f"ERRO: {erro}")
                    continue

        print(f"Done! Total: {total_inseridos}")
