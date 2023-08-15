from flask_sqlalchemy import BaseQuery

from src.extensions import database as db
from src.main.empresa.empresa import Empresa
from src.main.unidade.unidade import Unidade

from .mandato_config_empresa import MandatoConfigEmpresa
from .mandato_config_unidade import MandatoConfigUnidade


class MandatoConfigHandler:
    def __init__(self, tab_empresa: str, tab_unidade: str) -> None:
        """Args:
            tab_empresa (str): nome da tabela
            tab_unidade (str): nome da tabela
        """
        self.empresa: str = tab_empresa
        self.unidade: str = tab_unidade

    def get_pending_confs(self, table_name: str) -> BaseQuery:
        if table_name == self.empresa:
            curr_confs = db.session.query(MandatoConfigEmpresa.id_empresa)
            query = db.session.query(Empresa).filter(
                ~Empresa.id_empresa.in_(curr_confs)
            )
        else:
            curr_confs = db.session.query(MandatoConfigUnidade.id_unidade)
            query = db.session.query(Unidade).filter(
                ~Unidade.id_unidade.in_(curr_confs)
            )

        return query

    def insert_confs(
        self, table_name: str, obj_ids: list[int]
    ) -> int:
        if table_name == self.empresa:
            attr_name = "id_empresa"
            table = MandatoConfigEmpresa
        else:
            attr_name = "id_unidade"
            table = MandatoConfigUnidade

        vals = [{attr_name: obj} for obj in obj_ids]
        stmt = db.insert(table).values(vals)
        res = db.session.execute(stmt)
        db.session.commit()
        return res.rowcount
