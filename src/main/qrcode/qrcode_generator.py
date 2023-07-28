from io import BytesIO

import qrcode
from qrcode.image.pure import PyPNGImage


class QrCodeGenerator:
    def __init__(self) -> None:
        pass

    def generate_qr_code(self, data: str) -> bytes:
        # NOTE: use Pure Python PNG (PyPNGImage) because Pillow is not working with this library
        img = qrcode.make(data=data, image_factory=PyPNGImage)

        # save img data to memory as bytes
        output = BytesIO()
        img.save(output)
        return output.getvalue()
