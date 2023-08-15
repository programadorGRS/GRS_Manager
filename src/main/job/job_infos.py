from dataclasses import dataclass
from datetime import datetime
from src import TIMEZONE_SAO_PAULO


@dataclass
class JobInfos:
    '''
        Dataclass para coletar informações sobre os \
        Jobs de carregameto em geral
    '''
    tabela: str
    cod_empresa_principal: int
    id_empresa: int | None = None
    qtd_inseridos: int = 0
    qtd_atualizados: int = 0
    ok: bool = True
    erro: str | None = None
    data_hora: datetime = datetime.now(TIMEZONE_SAO_PAULO)

    def add_error(self, error: str):
        if self.erro:
            self.erro += f'; {error}'
        else:
            self.erro = error
