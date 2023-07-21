from dataclasses import dataclass

from ..empresa.empresa import Empresa
from ..exame.exame import Exame
from ..funcionario.funcionario import Funcionario
from ..pedido.pedido import Pedido
from .models import RTC


@dataclass
class InfosRtc:
    empresa: Empresa
    pedido: Pedido
    funcionario: Funcionario
    exames: list[Exame]
    rtcs: list[RTC]
