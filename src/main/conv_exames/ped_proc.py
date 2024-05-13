from datetime import datetime
from io import BytesIO
from typing import Any

from sqlalchemy.exc import DatabaseError, SQLAlchemyError

from src import TIMEZONE_SAO_PAULO
from src.extensions import database as db
from src.soc_web_service.proc_assinc import ProcessamentoAssincrono

from ..empresa.empresa import Empresa
from ..job.job_infos import JobInfos
from .ped_proc_config import PedProcConfig


class PedidoProcessamento(db.Model):
    __tablename__ = "PedidoProcessamento"

    id_proc = db.Column(db.Integer, primary_key=True)
    cod_empresa_principal = db.Column(
        db.Integer, db.ForeignKey("EmpresaPrincipal.cod"), nullable=False
    )
    cod_solicitacao = db.Column(db.Integer, nullable=False)
    id_empresa = db.Column(
        db.Integer, db.ForeignKey("Empresa.id_empresa"), nullable=False
    )
    cod_empresa = db.Column(db.Integer, nullable=False)
    data_criacao = db.Column(db.Date, nullable=False)
    resultado_importado = db.Column(db.Boolean, nullable=False, default=False)
    relatorio_enviado = db.Column(db.Boolean, nullable=False, default=False)
    parametro = db.Column(db.String(500), nullable=False)
    obs = db.Column(db.String(500))

    exames_conv = db.relationship(
        "ConvExames", backref="pedido_proc", lazy=True
    )  # one to many

    TIPO_PROCESSAMENTO = 8
    COD_RESP_OK = "SOC-100"

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
            db.session.query(cls)  # type: ignore
            .join(Empresa, cls.id_empresa == Empresa.id_empresa)
            .filter(*filtros)
            .order_by(cls.id_proc.desc(), cls.id_empresa)
        )
        return query

    @classmethod
    def criar_ped_proc(
        cls, id_empresa: int, wsdl: str | BytesIO, ws_keys: dict[str, Any]
    ) -> JobInfos:
        empresa: Empresa = Empresa.query.get(id_empresa)

        infos = JobInfos(
            tabela=cls.__tablename__,
            cod_empresa_principal=empresa.cod_empresa_principal,
            id_empresa=empresa.id_empresa,
        )

        try:
            proc_assinc = cls.__setup_proc_assinc(wsdl=wsdl, ws_keys=ws_keys)
            
        except Exception as e:
            infos.ok = False
            infos.add_error(str(e))
            return infos
        
        par = cls._setup_param(
            id_empresa=empresa.id_empresa, proc_assinc=proc_assinc
        )
        if not par:
            infos.ok = False
            infos.add_error("Empresa não tem PedProcConfig")
            return infos

        body = cls.__setup_request_body(
            cod_empresa=empresa.cod_empresa, proc_assinc=proc_assinc, param=par
        )
        #print(body)
        try:
            proc_assinc.set_client_username_token()
            resp = proc_assinc.call_service(request_body=body)            
            #print(f'BODY{body}')
            #print(f'RESPOSTA{resp}')
        except Exception as e:
            infos.ok = False
            infos.add_error(f"Erro no request: {str(e)}")
            return infos

        error = cls.__get_errors(resp=resp)
        if error:
            infos.ok = False
            infos.add_error(f"Erro SOC: {error}")
            return infos

        cod_sol = getattr(resp, "codigoSolicitacao", None)
        if not cod_sol:
            infos.ok = False
            infos.add_error("Sem Cod Solicitação")
            return infos

        new_proc = cls(
            cod_empresa_principal=empresa.cod_empresa_principal,
            cod_solicitacao=cod_sol,
            id_empresa=empresa.id_empresa,
            cod_empresa=empresa.cod_empresa,
            data_criacao=datetime.now(TIMEZONE_SAO_PAULO),
            resultado_importado=False,
            relatorio_enviado=False,
            parametro=par,
        )

        try:
            db.session.add(new_proc)  # type: ignore
            db.session.commit()  # type: ignore
            infos.qtd_inseridos = 1
        except (SQLAlchemyError, DatabaseError) as e:
            db.session.rollback()  # type: ignore
            infos.ok = False
            infos.add_error(str(e))
            return infos

        return infos

    @classmethod
    def __setup_proc_assinc(
        cls, wsdl: str | BytesIO, ws_keys: dict[str, Any], raw_response: bool = False
    ):
        proc_assinc = ProcessamentoAssincrono()
        proc_assinc.set_client(wsdl=wsdl, raw_response=raw_response)
        proc_assinc.set_factory()
        proc_assinc.set_ws_keys(keys=ws_keys)
        return proc_assinc

    @classmethod
    def _setup_param(cls, id_empresa: int, proc_assinc: ProcessamentoAssincrono):
        par_data = PedProcConfig.get_configs(id_empresa=id_empresa)

        if not par_data:
            return None

        par_str = proc_assinc.processar_parametro(param=par_data)
        return par_str

    @classmethod
    def __setup_request_body(
        cls, cod_empresa: int, proc_assinc: ProcessamentoAssincrono, param: str
    ):
        ident = proc_assinc.generate_identificacaoUsuarioWsVo()

        body = proc_assinc.build_request_body(
            identificacaoWsVo=ident,
            codigoEmpresa=cod_empresa,
            tipoProcessamento=cls.TIPO_PROCESSAMENTO,
            parametros=param,
        )

        return body

    @staticmethod
    def __get_errors(resp: Any):
        info_geral = getattr(resp, "informacaoGeral", None)

        num_erros = getattr(info_geral, "numeroErros", 0)
        if not num_erros:
            return None

        erro = ""

        msg_geral = getattr(info_geral, "mensagem", "")
        if msg_geral:
            erro += msg_geral + " - "

        op_dtl_ls = []
        op_dtl = getattr(info_geral, "mensagemOperacaoDetalheList", [])
        for err in op_dtl:
            msg_dtl = getattr(err, "mensagem", "")

            if not msg_dtl:
                continue

            op_dtl_ls.append(msg_dtl)

        erro += "; ".join(op_dtl_ls)

        return erro
