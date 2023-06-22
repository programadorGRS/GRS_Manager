from datetime import date, datetime

import pandas as pd

from src.soc_web_service.exporta_dados import ExportaDados
from src.utils import gerar_datas

from ..empresa.empresa import Empresa
from ..empresa_principal.empresa_principal import EmpresaPrincipal


class Mandato:
    def __init__(self) -> None:
        pass

    @staticmethod
    def get_mandatos(
        id_empresa: int,
        data_inicio: date,
        data_fim: date,
        mandato_ativo: bool
    ) -> object | None:
        """
            Envia request para Exporta dados Mandatos CIPA

            data_inicio/fim: permite máximo de 1 ano e servem como filtro
            para a data de inicio do mandato.

            Retorna response object ou None se houver erro no Request
        """
        EMPRESA: Empresa = Empresa.query.get(id_empresa)
        EMPRESA_PRINCIPAL: EmpresaPrincipal = EMPRESA.empresa_principal

        ex = ExportaDados(
            wsdl_filename="prod/ExportaDadosWs.xml",
            exporta_dados_keys_filename=EMPRESA_PRINCIPAL.configs_exporta_dados.split('/')[-1]
        )

        PARAMETRO = ex.mandato_cipa(
            empresa=EMPRESA.cod_empresa,
            codigo=ex.EXPORTA_DADOS_KEYS.get("MANDATO_CIPA_COD"),
            chave=ex.EXPORTA_DADOS_KEYS.get('MANDATO_CIPA_KEY'),
            dataInicio=data_inicio,
            dataFim=data_fim,
            ativo=mandato_ativo
        )

        request_body = ex.build_request_body(param=PARAMETRO)

        try:
            resp = ex.call_service(request_body=request_body)
            return resp
        except:
            return None

    @classmethod
    def get_dados_json_periodo(
        self,
        id_empresa: int,
        data_inicio: date,
        data_fim: date,
        mandato_ativo: bool
    ) -> list[dict[str, any]]:
        '''
            Realiza varios requests no Exporta Dados para coletar dados no periodo indicado.

            Gera os requests respeitando o limite de 365 dias automaticamente.
        '''
        DATAS = gerar_datas(data_inicio=data_inicio, data_fim=data_fim, passo_dias=365)

        dados = []
        for inicio, fim in DATAS:
            resp = self.get_mandatos(
                id_empresa=id_empresa,
                data_inicio=inicio,
                data_fim=fim,
                mandato_ativo=mandato_ativo
            )
            retorno = getattr(resp, 'retorno', None)
            if retorno:
                dados_resp = ExportaDados.json_from_zeep(retorno=retorno)
                dados.extend(dados_resp)

        return dados

    @staticmethod
    def tratar_df(
        df: pd.DataFrame,
        id_empresa: int,
        cod_empresa_principal: int,
        mandato_ativo: bool
    ) -> pd.DataFrame:
        COLS = {
            'CODIGOMANDATO': 'cod_mandato',
            'CODIGOUNIDADE': 'cod_unidade',
            'NOMESETOR': 'nome_setor',
            'CODIGOFUNCIONARIO': 'cod_funcionario',
            'NOMEFUNCIONARIO': 'nome_funcionario',
            'FUNCIONARIOELEITO': 'funcionario_eleito',
            'RENUNCIADO': 'funcionario_renunciou',
            'TIPOESTABILIDADE': 'tipo_estabilidade',
            'DSESTABILIDADE': 'descr_estabilidade',
            'TIPOREPRESENTACAO': 'tipo_representacao',
            'FUNCAO': 'funcao',
            'TIPOSITUACAO': 'tipo_situacao',
            'DATAINICIOMANDATO': 'data_inicio_mandato',
            'DATAFIMMANDATO': 'data_fim_mandato',
            'DATACANDIDATURA': 'data_candidatura',
            'DATAINICIOELEITORAL': 'data_inicio_eleitoral',
            'DATAELEICAOCIPA': 'data_eleicao',
            'DATAINICIOPROCESSO': 'data_inicio_processo',
            'DATAINICIALINSCRICAO': 'data_inicio_inscricao',
            'DATAFINALINSCRICAO': 'data_fim_inscricao',
            'DATAPRORROGACAO': 'data_prorrogacao',
            'DATAESTABILIDADEFUNCIONARIO': 'data_estabilidade'
        }

        df = df.copy()
        df = df[list(COLS.keys())]
        df = df.replace({'': None})
        df.rename(columns=COLS, inplace=True)

        int_cols = [
            'cod_mandato',
            'cod_funcionario',
            'tipo_estabilidade'
        ]

        for col in int_cols:
            df[col] = df[col].astype(dtype=int, errors='ignore')

        date_cols = [
            'data_inicio_mandato',
            'data_fim_mandato',
            'data_candidatura',
            'data_inicio_eleitoral',
            'data_eleicao',
            'data_inicio_processo',
            'data_inicio_inscricao',
            'data_fim_inscricao',
            'data_prorrogacao',
            'data_estabilidade'
        ]

        for col in date_cols:
            df[col] = pd.to_datetime(df[col], dayfirst=True).dt.date

        for col in ['funcionario_eleito', 'funcionario_renunciou']:
            df[col] = df[col].astype(object)
            df[col] = df[col].replace({'Sim': True, 'Não': False})

        df['cod_empresa_principal'] = cod_empresa_principal
        df['id_empresa'] = id_empresa
        df['ativo'] = mandato_ativo

        df['data_inclusao'] = datetime.now().date()

        return df

