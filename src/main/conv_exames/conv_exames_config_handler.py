from flask_sqlalchemy import BaseQuery

from src.extensions import database as db
from src.main.empresa.empresa import Empresa

from .ped_proc_config import PedProcConfig


class ConvExamesConfigHandler:
    def __init__(self) -> None:
        pass

    def get_pending_confs(self) -> BaseQuery:
        """Busca Empresas que ainda não possuem configuração definida na
        tabela PedProcConfig"""
        curr_confs = db.session.query(PedProcConfig.id_empresa)
        query = db.session.query(Empresa).filter(~Empresa.id_empresa.in_(curr_confs))
        return query

    def insert_confs(self, id_empresas: list[int]) -> int:
        """Insere as Empresas passadas baseado nos ids.
        Mantém valores padrão das colunas de PedProcConfig"""
        vals = [{"id_empresa": id_empresa} for id_empresa in id_empresas]
        stmt = db.insert(PedProcConfig).values(vals)
        res = db.session.execute(stmt)
        db.session.commit()
        return res.rowcount
