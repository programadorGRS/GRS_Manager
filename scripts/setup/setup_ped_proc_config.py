if __name__ == "__main__":
    import sys

    sys.path.append("../GRS_Manager")

    import pandas as pd

    from scripts.utils import set_app_config_by_os_name
    from src import app
    from src.extensions import database as db
    from src.main.conv_exames.ped_proc_config import PedProcConfig
    from src.main.empresa.empresa import Empresa

    with app.app_context():
        set_app_config_by_os_name(app=app)

        cols = {
            "id_empresa": "id_empresa",
            "conv_exames": "ativo",
            "conv_exames_convocar_clinico": "convocar_clinico",
            "conv_exames_nunca_realizados": "nunca_realizados",
            "conv_exames_per_nunca_realizados": "per_nunca_realizados",
            "conv_exames_pendentes": "pendentes",
            "conv_exames_pendentes_pcmso": "pendentes_pcmso",
            "conv_exames_selecao": "selecao",
        }

        query = db.session.query(Empresa)

        df = pd.read_sql(query.statement, db.session.bind)
        df = df.dropna(subset="id_empresa", axis=0)

        df = df[list(cols.keys())]
        df = df.rename(columns=cols)

        for col in df.columns[1:]:
            df[col] = df[col].fillna(0).astype(int)

        try:
            qtd = df.to_sql(
                name=PedProcConfig.__tablename__,
                con=db.session.bind,
                if_exists="append",
                index=False,
            )
            db.session.commit()
            print(f"inseridos: {qtd}")
        except Exception as e:
            db.session.rollback()
            print(f"erro: {str(e)}")
