import os
from datetime import datetime

import jinja2
import pandas as pd
import pdfkit
from werkzeug.utils import secure_filename

from src import UPLOAD_FOLDER, app, database
from src.main.exame.exame import Exame
from src.main.funcionario.funcionario import Funcionario
from src.main.pedido.pedido import Pedido
from src.utils import get_image_file_as_base64_data, zipar_arquivos

from .exceptions import RTCGeneratioError


class GerarRTC:
    def __init__(self) -> None:
        pass

    MAIN_TEMPLATE = "src/main/rtc/templates/base_rtc.html"

    # NOTE: em Windows, o tamanho de EMPTY_SQUR é diferente \
    # do tamaho de MARKED_SQUR. Em Linux os dois tem o \
    # mesmo tamanho. Portando, sempre manter os tamanhos iguais
    EMPTY_SQUR = "&#9633;"
    EMPTY_SQUR_SIZE = "15pt"
    MARKED_SQUR = "&#9746;"
    MARKED_SQUR_SIZE = "15pt"

    LOGO_GRS = os.path.join(app.static_folder, "logos" "logo_grs.png")
    LOGO_GRS_WIDTH = "70px"
    LOGO_GRS_HEIGHT = "30px"

    LOGO_MANSERV = os.path.join(app.static_folder, "logos", "logo_manserv.png")
    LOGO_MANSERV_WIDTH = "150px"
    LOGO_MANSERV_HEIGHT = "30px"

    pdfkit_options: dict[str, str] = {
        "margin-top": "5mm",
        "margin-right": "5mm",
        "margin-bottom": "5mm",
        "margin-left": "5mm",
    }

    @staticmethod
    def get_pdfkit_configs():
        return pdfkit.configuration(wkhtmltopdf=app.config["WKHTMLTOPDF_PATH"])

    @classmethod
    def buscar_infos_rtc(cls, id_ficha: int) -> dict:
        pedido: Pedido = Pedido.query.get(id_ficha)

        funcionario = cls.__get_funcionario(
            cod_funcionario=pedido.cod_funcionario, id_empresa=pedido.id_empresa
        )
        if not funcionario:
            raise RTCGeneratioError("Funcionário não encontrado.")

        rtcs = cls.__get_rtcs_cargo(cod_cargo=funcionario.cod_cargo)
        if not rtcs:
            raise RTCGeneratioError("Nenhuma RTC encontrada para o Cargo")

        exames = cls.__get_exames_rtc(
            ids_rtcs=rtcs, cod_tipo_exame=pedido.cod_tipo_exame
        )
        if not exames:
            raise RTCGeneratioError("Nenhum Exame encontrado para as RTCs dessa Ficha")

        infos = {
            "id_ficha": pedido.id_ficha,
            "nome_funcionario": pedido.nome_funcionario,
            "cpf_funcionario": pedido.cpf,
            "data_adm": funcionario.data_adm,
            "cargo_funcionario": funcionario.nome_cargo,
            "setor_funcionario": funcionario.nome_setor,
            "ids_rtcs": rtcs,
            "cod_exames": exames,
        }

        return infos

    @staticmethod
    def __get_funcionario(cod_funcionario: int, id_empresa: int) -> Funcionario | None:
        funcionario: Funcionario = (
            database.session.query(Funcionario)
            .filter(Funcionario.cod_funcionario == cod_funcionario)
            .filter(Funcionario.id_empresa == id_empresa)
            .first()
        )
        return funcionario

    @staticmethod
    def __get_rtcs_cargo(cod_cargo: str) -> list[int]:
        from .models import RTCCargos

        ids = database.session.query(RTCCargos).filter(
            RTCCargos.c.cod_cargo == cod_cargo
        )
        ids = [rtc.id_rtc for rtc in ids]
        return ids

    @staticmethod
    def __get_exames_rtc(ids_rtcs: list[int], cod_tipo_exame: int) -> list[str]:
        from .models import RTCExames

        exames = (
            database.session.query(RTCExames)
            .filter(RTCExames.c.id_rtc.in_(ids_rtcs))
            .filter(RTCExames.c.cod_tipo_exame == cod_tipo_exame)
        )
        exames = [exam.cod_exame for exam in exames]
        exames = list(dict.fromkeys(exames))  # remove duplicates
        return exames

    @classmethod
    def render_rtc_html(
        self,
        infos: dict[str, any],
        template: str = MAIN_TEMPLATE,
        logo_empresa: str = LOGO_GRS,
        logo_width: str = LOGO_GRS_WIDTH,
        logo_height: str = LOGO_GRS_HEIGHT,
        render_tipo_sang: bool = True,
    ) -> str:
        """
            Recebe informacoes sobre a Ficha e Funcionario e cria \
                modelo HTML da RTC

            Usar com o dicionario de RTC.buscar_infos_rtc

            Returns:
                str: output text
        """
        pedido: Pedido = Pedido.query.get(infos["id_ficha"])

        infos["render_tipo_sang"] = render_tipo_sang

        # format cpf
        if len(infos["cpf_funcionario"]) == 11:
            infos["cpf_funcionario"] = (
                f"{infos['cpf_funcionario'][:3]}."
                f"{infos['cpf_funcionario'][3:6]}."
                f"{infos['cpf_funcionario'][6:9]}-"
                f"{infos['cpf_funcionario'][9:]}"
            )

        # RTCs
        infos = self.__get_lista_rtcs(infos=infos)

        # criar duas colunas de RTC
        colunas_ab = self._criar_colunas_ab(infos["lista_rtcs"])
        infos["col_rtc_a"] = colunas_ab[0]
        infos["col_rtc_b"] = colunas_ab[1]

        # EXAMES
        infos = self.__get_lista_exames(
            infos=infos, cod_emp_princ=pedido.cod_empresa_principal
        )

        # criar duas colunas de exames
        colunas_ab = self._criar_colunas_ab(infos["lista_exames"])
        infos["col_exames_a"] = colunas_ab[0]
        infos["col_exames_b"] = colunas_ab[1]

        # LOGO
        infos["logo_empresa"] = get_image_file_as_base64_data(img_path=logo_empresa)
        infos["logo_width"] = logo_width
        infos["logo_height"] = logo_height

        # render template as string
        template_loader = jinja2.FileSystemLoader("./")
        template_env = jinja2.Environment(loader=template_loader)  # nosec B701
        template = template_env.get_template(template)
        output_text = template.render(infos)

        return output_text

    @classmethod
    def gerar_pdf(self, infos: dict[str, any], html: str):
        nome = secure_filename(infos["nome_funcionario"]).upper()
        timestamp = int(datetime.now().timestamp())
        filename = f"RTC_{nome}_{timestamp}.pdf"
        if len(infos["cod_exames"]) == 0:
            filename = f"__VAZIO__RTC_{nome}_{timestamp}.pdf"

        file_path = os.path.join(UPLOAD_FOLDER, filename)

        pdfkit.from_string(
            input=html,
            output_path=file_path,
            configuration=self.get_pdfkit_configs(),
            options=self.pdfkit_options,
        )

        return file_path

    @classmethod
    def gerar_zip(self, arquivos: list[str]):
        timestamp = int(datetime.now().timestamp())
        nome_zip = f"RTCS_{timestamp}.zip"
        zip_path = os.path.join(UPLOAD_FOLDER, nome_zip)
        zipar_arquivos(caminhos_arquivos=arquivos, caminho_pasta_zip=zip_path)
        return nome_zip

    @staticmethod
    def gerar_df_erros(erros: list[tuple[Pedido, str]]):
        erros = [(p.seq_ficha, p.nome_funcionario, err) for p, err in erros]
        df = pd.DataFrame(erros, columns=["seq_ficha", "funcionario", "erro"])
        return df

    @staticmethod
    def gerar_csv_erros(df_erros: pd.DataFrame):
        timestamp = int(datetime.now().timestamp())
        filename = f"Erros_RTC_{timestamp}.csv"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        df_erros.to_csv(file_path, sep=";", index=False, encoding="iso-8859-1")
        return file_path

    @staticmethod
    def __get_lista_exames(infos: dict[str, any], cod_emp_princ: int):
        # NOTE: sempre usar filtro de cod_empresa_principal, pois algumas Empresas principais
        # podem ter Exames iguais, causando duplicidade de Exames no RTC
        nomes_exames = (
            database.session.query(Exame)
            .filter(Exame.cod_exame.in_(infos["cod_exames"]))
            .filter(Exame.cod_empresa_principal == cod_emp_princ)
        )
        infos["lista_exames"] = [exame.nome_exame for exame in nomes_exames]
        return infos

    @classmethod
    def __get_lista_rtcs(self, infos: dict[str, any]):
        rtcs_geral = self.query.all()
        infos["lista_rtcs"] = []
        # pegar todas rtc e marcar as usadas
        for i in rtcs_geral:
            if i.id_rtc in infos["ids_rtcs"]:
                infos["lista_rtcs"].append(
                    (self.MARKED_SQUR_SIZE, self.MARKED_SQUR, i.nome_rtc)
                )
            else:
                infos["lista_rtcs"].append(
                    (self.EMPTY_SQUR_SIZE, self.EMPTY_SQUR, i.nome_rtc)
                )
        return infos

    @staticmethod
    def _criar_colunas_ab(lista_itens: list) -> tuple[list, list]:
        if len(lista_itens) <= 1:
            return (lista_itens, [])

        if len(lista_itens) % 2 == 0:  # se for par, divisao igual
            separador = int(len(lista_itens) / 2)
        else:  # se for impar, fazer a coluna A maior do que a B
            separador = int(len(lista_itens) / 2) + 1
        col_a = lista_itens[:separador]
        col_b = lista_itens[separador:]
        return (col_a, col_b)
