from sqlalchemy import text, update

from src.extensions import database


class Processamento(database.Model):
    __tablename__ = 'Processamento'

    id = database.Column(database.Integer, primary_key=True, nullable=False)
    tipo = database.Column(
        database.Integer,
        database.ForeignKey('TipoProcessamento.id'),
        nullable=False
    )
    status = database.Column(
        database.Integer,
        database.ForeignKey('StatusProcessamento.id'),
        nullable=False,
        server_default=text('1')
    )
    erro = database.Column(database.String(100))

    @classmethod
    def nova_tarefa(self, tipo: int) -> int:
        '''
            Registra nova tarefa.

            Retorna id (int) da nova tarefa criada.
        '''
        p = self(tipo=tipo)
        database.session.add(p)
        database.session.commit()
        return p.id

    @classmethod
    def concluir_tarefa(
        self,
        id: int,
        status: int = 2,
        erro: str | None = None
    ):
        '''
            Atualiza Status da tarefa especificada.

            Status:
            - 1: Em Andamento
            - 2: Concluído
            - 3: Cancelado
            - 4: Erro
        '''
        p = self.query.get(id)
        p.status = status
        p.erro = erro
        database.session.commit()
        return None

    @classmethod
    def buscar_tarefas_ativas(self, tipo: int) -> bool:
        '''
            Retorna True se houver outra tarefa \
            do mesmo tipo em andamento.

            Tipos:
            - 1: Carregar Pedidos
            - 2: Carregar Funcionários
        '''
        p = (
            database.session.query(self)
            .filter(self.tipo == tipo)
            .filter(self.status == 1)
            .first()
        )

        if p:
            return True
        else:
            return False

    @classmethod
    def cancelar_todas_tarefas(self) -> int:
        '''
            Seta o status de todas as tarefas Em Andamento para Cancelado

            Retorna num de linhas afetadas
        '''
        stt = (
            update(self)
            .where(self.status == 1)
            .values(status=3)
        )
        res = database.session.execute(statement=stt)
        database.session.commit()
        return res.rowcount

