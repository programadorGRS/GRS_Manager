class RTCValidationError(Exception):
    message: str

    def __init__(self, message: str) -> None:
        """Customização para erros de validação em dataframes de RTC"""
        self.message = message
        super().__init__(self.message)


class RTCGeneratioError(Exception):
    def __init__(self, message: str) -> None:
        """Customização para erros de geração de RTC"""
        self.message = message
        super().__init__(self.message)
