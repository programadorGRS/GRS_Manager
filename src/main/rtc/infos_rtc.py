from dataclasses import dataclass

from ..empresa.empresa import Empresa
from ..exame.exame import Exame
from ..funcionario.funcionario import Funcionario
from ..pedido.pedido import Pedido
from .models import RTC, RTCRegrasVida


@dataclass
class InfosRtc:
    empresa: Empresa
    pedido: Pedido
    funcionario: Funcionario
    exames: list[tuple[Exame.cod_exame, Exame.nome_exame]]
    rtcs: list[RTC]

@dataclass
class InfosRtcRegrasVida:
    empresa: Empresa
    pedido: Pedido
    funcionario: Funcionario
    exames: list[tuple[Exame.cod_exame, Exame.nome_exame]]
    rtcs: list[RTCRegrasVida]
