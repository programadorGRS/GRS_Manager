import json

from ..pedido.pedido import Pedido
from .qrcode_generator import QrCodeGenerator


class QrCodeRtc(QrCodeGenerator):
    def __init__(self) -> None:
        super().__init__()

    def generate_qrcode_data_str(self, id_ficha: int):
        pedido: Pedido = Pedido.query.get(id_ficha)

        data_dict = {
            "cod_empresa": pedido.empresa.cod_empresa,
            "cod_funcionario": pedido.cod_funcionario,
            "seq_ficha": pedido.seq_ficha,
            "tipo_doc": "rtc",
        }

        return json.dumps(data_dict)
