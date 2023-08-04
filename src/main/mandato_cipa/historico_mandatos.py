from datetime import date

import pandas as pd
from sqlalchemy import delete

from src import database
from src.soc_web_service.exporta_dados import ExportaDados

from ..empresa.empresa import Empresa
from ..job.job_infos import JobInfos
from .mandato import Mandato


class HistoricoMandatos(database.Model, Mandato):
    __tablename__ = 'HistoricoMandatos'

    id = database.Column(database.Integer, primary_key=True)
    cod_mandato = database.Column(database.Integer, nullable=False)
    ativo = database.Column(database.Boolean, nullable=False)

    cod_empresa_principal = database.Column(database.Integer, database.ForeignKey('EmpresaPrincipal.cod'), nullable=False)
    id_empresa = database.Column(database.Integer, database.ForeignKey('Empresa.id_empresa'), nullable=False)
    cod_unidade = database.Column(database.String(100))
    nome_setor = database.Column(database.String(255))

    cod_funcionario = database.Column(database.Integer, nullable=False)
    nome_funcionario = database.Column(database.String(255))
    funcionario_eleito = database.Column(database.Boolean)
    funcionario_renunciou = database.Column(database.Boolean)

    tipo_estabilidade = database.Column(database.Integer)
    descr_estabilidade = database.Column(database.String(100))
    tipo_representacao = database.Column(database.String(20))
    funcao = database.Column(database.String(100))
    tipo_situacao = database.Column(database.String(10))

    data_inicio_mandato = database.Column(database.Date)
    data_fim_mandato = database.Column(database.Date)

    data_candidatura = database.Column(database.Date)

    data_inicio_eleitoral = database.Column(database.Date)
    data_eleicao = database.Column(database.Date)

    data_inicio_processo = database.Column(database.Date)

    data_inicio_inscricao = database.Column(database.Date)
    data_fim_inscricao = database.Column(database.Date)

    data_prorrogacao = database.Column(database.Date)

    data_estabilidade = database.Column(database.Date)

    data_inclusao = database.Column(database.Date)

    def __repr__(self) -> str:
        return f'<{self.id}> {self.nome_funcionario}'

    @classmethod
    def carregar_mandatos(
        self,
        id_empresa: int,
        data_inicio: date,
        data_fim: date,
        mandato_ativo: bool
    ) -> JobInfos:
        """
            Carrega Mandatos CIPA da Empresa selecionada.

            data_inicio/fim: permite máximo de 1 ano e servem como filtro
            para a data de inicio do mandato.

            Obs: se já houver mandatos com o mesmo
            id_empresa, status e data_inclusao, este será substituido pelo novo.
        """
        EMPRESA: Empresa = Empresa.query.get(id_empresa)

        infos = JobInfos(
            tabela=self.__tablename__,
            cod_empresa_principal=EMPRESA.cod_empresa_principal,
            id_empresa=EMPRESA.id_empresa,
        )

        resp = self.get_mandatos(
            id_empresa = id_empresa,
            data_inicio = data_inicio,
            data_fim = data_fim,
            mandato_ativo = mandato_ativo
        )

        if not resp:
            infos.ok = False
            infos.erro = "erro no request"
            return infos

        if getattr(resp, 'erro', None):
            infos.ok = False
            infos.erro = getattr(resp, 'mensagemErro', None)
            return infos

        df = ExportaDados.dataframe_from_zeep(retorno=getattr(resp, 'retorno', None))

        if df.empty:
            infos.ok = False
            infos.erro = 'df vazio'
            return infos

        df = self.tratar_df(
            df=df,
            id_empresa=EMPRESA.id_empresa,
            cod_empresa_principal=EMPRESA.cod_empresa_principal,
            mandato_ativo=mandato_ativo
        )

        cod_mandatos = (
            df['cod_mandato']
            .astype(int)
            .drop_duplicates()
            .tolist()
        )

        self.__remover_dados_atuais(
            id_empresa=EMPRESA.id_empresa,
            data_inclusao=date.today(),
            cod_mandatos=cod_mandatos
        )

        infos.qtd_inseridos = self.__inserir_mandatos(df)

        return infos

    @classmethod
    def __remover_dados_atuais(self, id_empresa: int, cod_mandatos: list[int], data_inclusao: date):
        stmt = (
            delete(self)
            .where(self.id_empresa == id_empresa)
            .where(self.cod_mandato.in_(cod_mandatos))
            .where(self.data_inclusao == data_inclusao)
        )
        database.session.execute(statement=stmt)
        database.session.commit()
        return None

    @classmethod
    def __inserir_mandatos(self, df: pd.DataFrame) -> int:
        qtd = df.to_sql(
            name=self.__tablename__,
            con=database.session.bind,
            index=False,
            if_exists='append'
        )
        database.session.commit()
        return qtd

