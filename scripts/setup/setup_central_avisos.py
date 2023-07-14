if __name__ == "__main__":
    import sys

    sys.path.append("../GRS_Manager")

    import pandas as pd

    from scripts.utils import set_app_config_by_os_name
    from src import app
    from src.extensions import database
    from src.main.empresa.empresa import Empresa

    with app.app_context():
        set_app_config_by_os_name(app=app)

    COD_GRS = 423

    print(f"COD GRS: {COD_GRS}")

    # inserir dominios
    file_path = "documents/dominios_empresas.csv"

    print(f"Lendo df: {file_path}")
    df = pd.read_csv(file_path, sep=";")

    print("Tratando df...")
    df["CODIGOEMPRESA"] = df["CODIGOEMPRESA"].astype(int)
    df["DOMAIN"] = df["DOMAIN"].astype(str)
    df["DOMAIN"] = df["DOMAIN"].str.replace(" ", "")
    df["DOMAIN"] = df["DOMAIN"].str.replace("\t", "")
    df["DOMAIN"] = df["DOMAIN"].replace("", None)
    df = df.dropna(axis=0)

    print("Buscando Empresas...")
    with app.app_context():
        query_empresas = database.session.query(
            Empresa.id_empresa, Empresa.cod_empresa
        ).filter(Empresa.cod_empresa_principal == COD_GRS)

        df_empresas = pd.read_sql(
            sql=query_empresas.statement, con=database.session.bind
        )

    df_empresas = df_empresas.merge(
        right=df, how="left", left_on="cod_empresa", right_on="CODIGOEMPRESA"
    )

    df_empresas = df_empresas.rename(columns={"DOMAIN": "dominios_email"})
    df_empresas = df_empresas[["id_empresa", "dominios_email"]]
    df_empresas = df_empresas[df_empresas["dominios_email"].notna()]

    print("df infos:")
    print(df.info())

    print("df_empresas infos:")
    print(df_empresas.info())

    mappings = df_empresas.to_dict(orient="records")

    with app.app_context():
        print("Updating with df_empresas...")
        database.session.bulk_update_mappings(Empresa, mappings=mappings)
        database.session.commit()

    print("Done!")
