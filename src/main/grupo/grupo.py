from datetime import datetime

from sqlalchemy import delete, insert

from src import TIMEZONE_SAO_PAULO, database


grupo_usuario = database.Table('grupo_usuario',
    database.Column('id_grupo', database.Integer, database.ForeignKey('Grupo.id_grupo')),
    database.Column('id_usuario', database.Integer, database.ForeignKey('Usuario.id_usuario'))
)


grupo_empresa = database.Table('grupo_empresa',
    database.Column('id_grupo', database.Integer, database.ForeignKey('Grupo.id_grupo')),
    database.Column('id_empresa', database.Integer, database.ForeignKey('Empresa.id_empresa'))
)


grupo_empresa_socnet = database.Table('grupo_empresa_socnet',
    database.Column('id_grupo', database.Integer, database.ForeignKey('Grupo.id_grupo')),
    database.Column('id_empresa', database.Integer, database.ForeignKey('EmpresaSOCNET.id_empresa'))
)


grupo_prestador = database.Table('grupo_prestador',
    database.Column('id_grupo', database.Integer, database.ForeignKey('Grupo.id_grupo')),
    database.Column('id_prestador', database.Integer, database.ForeignKey('Prestador.id_prestador'))
)


grupo_empresa_prestador = database.Table('grupo_empresa_prestador',
    database.Column('id_grupo', database.Integer, database.ForeignKey('Grupo.id_grupo')),
    database.Column('id_empresa', database.Integer, database.ForeignKey('Empresa.id_empresa')),
    database.Column('id_prestador', database.Integer, database.ForeignKey('Prestador.id_prestador')),
)


class Grupo(database.Model):
    __tablename__ = 'Grupo'
    id_grupo = database.Column(database.Integer, primary_key=True)
    nome_grupo = database.Column(database.String(255), nullable=False) # many to many

    data_inclusao = database.Column(database.DateTime)
    data_alteracao = database.Column(database.DateTime)
    incluido_por = database.Column(database.String(50))
    alterado_por = database.Column(database.String(50))

    @classmethod
    def update_grupo_usuario(self, id_grupo: int, id_usuarios: list[int], alterado_por: str):
        grupo = self.query.get(id_grupo)

        # reset current group
        database.session.execute(
            delete(grupo_usuario).
            where(grupo_usuario.c.id_grupo == grupo.id_grupo)
        )

        if id_usuarios:
            insert_items = [
                {'id_grupo': grupo.id_grupo, 'id_usuario': i}
                for i in id_usuarios
            ]

            database.session.execute(
                insert(grupo_usuario).
                values(insert_items)
            )

        grupo.data_alteracao = datetime.now(tz=TIMEZONE_SAO_PAULO)
        grupo.alterado_por = alterado_por
        database.session.commit()
        return None

    @classmethod
    def update_grupo_prestador(self, id_grupo: int, id_prestadores: list[int], alterado_por: str):
        grupo = self.query.get(id_grupo)

        # reset current group
        database.session.execute(
            delete(grupo_prestador).
            where(grupo_prestador.c.id_grupo == grupo.id_grupo)
        )

        if id_prestadores:
            insert_items = [
                {'id_grupo': grupo.id_grupo, 'id_prestador': i}
                for i in id_prestadores
            ]

            database.session.execute(
                insert(grupo_prestador).
                values(insert_items)
            )

        grupo.data_alteracao = datetime.now(tz=TIMEZONE_SAO_PAULO)
        grupo.alterado_por = alterado_por
        database.session.commit()

        self.__update_grupo_empresa_prestador(id_grupo=id_grupo)
        return None

    @classmethod
    def update_grupo_empresa(self, id_grupo: int, id_empresas: list[int], alterado_por: str):
        grupo = self.query.get(id_grupo)

        # reset current group
        database.session.execute(
            delete(grupo_empresa).
            where(grupo_empresa.c.id_grupo == grupo.id_grupo)
        )

        if id_empresas:
            insert_items = [
                {'id_grupo': grupo.id_grupo, 'id_empresa': i}
                for i in id_empresas
            ]

            database.session.execute(
                insert(grupo_empresa).
                values(insert_items)
            )

        grupo.data_alteracao = datetime.now(tz=TIMEZONE_SAO_PAULO)
        grupo.alterado_por = alterado_por
        database.session.commit()

        self.__update_grupo_empresa_prestador(id_grupo=id_grupo)
        return None

    @classmethod
    def __update_grupo_empresa_prestador(self, id_grupo: int):
        # reset current group
        database.session.execute(
            delete(grupo_empresa_prestador).
            where(grupo_empresa_prestador.c.id_grupo == id_grupo)
        )

        q_empresa_prestador: list = (
            database.session.query(grupo_empresa.c.id_empresa, grupo_prestador.c.id_prestador)
            .join(grupo_prestador, grupo_prestador.c.id_grupo == grupo_empresa.c.id_grupo)
            .filter(grupo_empresa.c.id_grupo == id_grupo)
            .all()
        )

        if q_empresa_prestador:
            insert_items = []
            for id_empresa, id_prestador in q_empresa_prestador:
                aux = {
                    'id_grupo': id_grupo,
                    'id_empresa': id_empresa,
                    'id_prestador': id_prestador
                }
                insert_items.append(aux)

            database.session.execute(
                insert(grupo_empresa_prestador).
                values(insert_items)
            )

        database.session.commit()
        return None
