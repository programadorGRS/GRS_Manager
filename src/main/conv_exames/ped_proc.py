from datetime import datetime

from src import database


class PedidoProcessamento(database.Model):
    __tablename__ = "PedidoProcessamento"

    id_proc = database.Column(database.Integer, primary_key=True)
    cod_empresa_principal = database.Column(
        database.Integer, database.ForeignKey("EmpresaPrincipal.cod"), nullable=False
    )
    cod_solicitacao = database.Column(database.Integer, nullable=False)
    id_empresa = database.Column(
        database.Integer, database.ForeignKey("Empresa.id_empresa"), nullable=False
    )
    cod_empresa = database.Column(database.Integer, nullable=False)
    data_criacao = database.Column(database.Date, nullable=False)
    resultado_importado = database.Column(
        database.Boolean, nullable=False, default=False
    )
    relatorio_enviado = database.Column(database.Boolean, nullable=False, default=False)
    parametro = database.Column(database.String(500), nullable=False)
    obs = database.Column(database.String(500))

    exames_conv = database.relationship(
        "ConvExames", backref="pedido_proc", lazy=True
    )  # one to many

    COLUNAS_CSV: list[str] = [
        "id_proc",
        "cod_empresa_principal",
        "nome",
        "id_empresa",
        "cod_empresa",
        "razao_social",
        "ativo",
        "cod_solicitacao",
        "data_criacao",
        "resultado_importado",
        "parametro",
        "obs",
    ]

    @classmethod
    def buscar_pedidos_proc(
        cls,
        cod_empresa_principal: int | None = None,
        id_empresa: int | None = None,
        empresas_ativas: bool | None = None,
        cod_solicitacao: int | None = None,
        resultado_importado: bool | None = None,
        relatorio_enviado: bool | None = None,
        obs: str | None = None,
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
    ):
        parametros = [
            (cod_empresa_principal, cls.cod_empresa_principal == cod_empresa_principal),
            (id_empresa, cls.id_empresa == id_empresa),
            (empresas_ativas, Empresa.ativo == empresas_ativas),
            (cod_solicitacao, cls.cod_solicitacao == cod_solicitacao),
            (resultado_importado, cls.resultado_importado == resultado_importado),
            (relatorio_enviado, cls.relatorio_enviado == relatorio_enviado),
            (obs, cls.obs.like(f"%{obs}%")),
            (data_inicio, cls.data_criacao >= data_inicio if data_inicio else None),
            (data_fim, cls.data_criacao <= data_fim if data_fim else None),
        ]

        filtros = []
        for value, param in parametros:
            if value is not None:
                filtros.append(param)

        query = (
            database.session.query(cls)
            .join(Empresa, cls.id_empresa == Empresa.id_empresa)
            .filter(*filtros)
            .order_by(cls.id_proc.desc(), cls.id_empresa)
        )
        return query
