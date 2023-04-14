from datetime import datetime

from sqlalchemy import text

from src import TIMEZONE_SAO_PAULO, database

from .infos_carregar import InfosCarregar


class Job(database.Model):
    '''
        Tabela para registrar Jobs de carregamentos feitos na database
    '''
    __tablename__ = 'Job'

    id = database.Column(database.Integer, primary_key=True)
    tabela = database.Column(database.String(100), nullable=False)
    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    id_empresa = database.Column(database.Integer, database.ForeignKey('Empresa.id_empresa'))
    qtd_inseridos = database.Column(database.Integer, nullable=False, server_default=text('0'), default=0)
    qtd_atualizados = database.Column(database.Integer, nullable=False, server_default=text('0'), default=0)
    ok = database.Column(database.Boolean, nullable=False, server_default=text('1'), default=True)
    erro = database.Column(database.String(255))
    data = database.Column(database.Date, nullable=False, default=datetime.now(TIMEZONE_SAO_PAULO).date())
    hora = database.Column(database.Time, nullable=False, default=datetime.now(TIMEZONE_SAO_PAULO).time())

    def __repr__(self) -> str:
        return f'<{self.id}> - {self.tabela} - {self.data_hora}'

    @classmethod
    def log_job(self, infos: InfosCarregar):
        new_job = self(
            tabela=infos.tabela,
            cod_empresa_principal=infos.cod_empresa_principal,
            id_empresa=infos.id_empresa,
            qtd_inseridos=infos.qtd_inseridos,
            qtd_atualizados=infos.qtd_atualizados,
            ok=infos.ok,
            erro=infos.erro,
            data=infos.data_hora.date(),
            hora=infos.data_hora.time()
        )

        database.session.add(new_job)
        database.session.commit()

        return None

