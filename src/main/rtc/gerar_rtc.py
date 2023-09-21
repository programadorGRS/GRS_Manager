import os
from datetime import datetime
from typing import Any

import pandas as pd
import pdfkit
from jinja2 import Template
from werkzeug.utils import secure_filename

from src import UPLOAD_FOLDER, app
from src.extensions import database as db
from src.main.exame.exame import Exame
from src.main.funcionario.funcionario import Funcionario
from src.main.pedido.pedido import Pedido
from src.utils import zipar_arquivos

from .exceptions import RTCGeneratioError
from .infos_rtc import InfosRtc
from .models import RTC, RTCCargos, RTCExames


class GerarRTC:
    def __init__(self) -> None:
        self.pdfkit_options: dict[str, str] = {
            "margin-top": "5mm",
            "margin-right": "5mm",
            "margin-bottom": "5mm",
            "margin-left": "5mm",
        }

    @staticmethod
    def get_pdfkit_configs():
        return pdfkit.configuration(wkhtmltopdf=app.config["WKHTMLTOPDF_PATH"])

    def get_infos_rtc(self, id_ficha: int) -> InfosRtc:
        pedido: Pedido = Pedido.query.get(id_ficha)

        funcionario = self.__get_funcionario(
            cod_funcionario=pedido.cod_funcionario, id_empresa=pedido.id_empresa
        )
        if not funcionario:
            raise RTCGeneratioError("Funcionário não encontrado.")

        rtcs = self.__get_rtcs_cargo(cod_cargo=funcionario.cod_cargo)
        if not rtcs:
            raise RTCGeneratioError("Nenhuma RTC encontrada para o Cargo")

        exames = self.__get_exames_rtc(
            ids_rtcs=[rtc.id_rtc for rtc in rtcs],
            cod_tipo_exame=pedido.cod_tipo_exame,
            cod_emp_princ=pedido.cod_empresa_principal,
        )
        if not exames:
            raise RTCGeneratioError("Nenhum Exame encontrado para as RTCs dessa Ficha")

        infos = InfosRtc(
            empresa=pedido.empresa,
            pedido=pedido,
            funcionario=funcionario,
            exames=exames,
            rtcs=rtcs,
        )

        return infos

    @staticmethod
    def __get_funcionario(cod_funcionario: int, id_empresa: int) -> Funcionario | None:
        funcionario: Funcionario = (
            db.session.query(Funcionario)  # type: ignore
            .filter(Funcionario.cod_funcionario == cod_funcionario)
            .filter(Funcionario.id_empresa == id_empresa)
            .first()
        )
        return funcionario

    @staticmethod
    def __get_rtcs_cargo(cod_cargo: str) -> list[RTC]:
        rtc_cargos = db.session.query(RTCCargos.c.id_rtc).filter(  # type: ignore
            RTCCargos.c.cod_cargo == cod_cargo
        )

        rtcs = db.session.query(RTC).filter(RTC.id_rtc.in_(rtc_cargos)).all()  # type: ignore
        return rtcs

    @staticmethod
    def __get_exames_rtc(
        ids_rtcs: list[int], cod_tipo_exame: int, cod_emp_princ: int
    ) -> list[tuple[Exame.cod_exame, Exame.nome_exame]]:
        rtc_exames = (
            db.session.query(RTCExames.c.cod_exame)  # type: ignore
            .filter(RTCExames.c.id_rtc.in_(ids_rtcs))
            .filter(RTCExames.c.cod_tipo_exame == cod_tipo_exame)
        )

        exames = (
            db.session.query(Exame.cod_exame, Exame.nome_exame)  # type: ignore
            .filter(Exame.cod_empresa_principal == cod_emp_princ)
            .filter(Exame.cod_exame.in_(rtc_exames))
            .group_by(Exame.cod_exame, Exame.nome_exame)  # avoid duplicates
            .order_by(Exame.nome_exame)
            .all()
        )
        return exames

    def render_rtc_html(
        self,
        infos: InfosRtc,
        template_body: str,
        logo_empresa: str | None = None,
        qr_code: str | None = None,
        render_tipo_sang: bool = True,
    ) -> str:
        template_data: dict[str, Any] = {}

        template_data["funcionario"] = infos.funcionario

        if infos.funcionario.cpf_funcionario:
            template_data["cpf_formatado"] = self.__format_cpf(
                cpf=infos.funcionario.cpf_funcionario
            )

        template_data["render_tipo_sang"] = render_tipo_sang

        # RTCs
        template_data["rtc_checkboxes"] = self.__get_rtc_checkboxes(
            ids_rtc=[rtc.id_rtc for rtc in infos.rtcs]
        )
        # criar duas colunas de RTC
        cols = self.list_to_columns(item_list=template_data["rtc_checkboxes"])
        template_data["rtc_col_a"] = cols[0]
        template_data["rtc_col_b"] = cols[1]

        # EXAMES
        # criar duas colunas de exames
        cols = self.list_to_columns(item_list=infos.exames)
        template_data["exames_col_a"] = cols[0]
        template_data["exames_col_b"] = cols[1]

        # images
        template_data["logo_empresa"] = logo_empresa
        template_data["qr_code"] = qr_code

        # render template as string
        template = Template(source=template_body)
        output_text = template.render(template_data)

        return output_text

    def gerar_pdf(self, html: str, nome_funcionario: str, qtd_exames: int):
        nome = secure_filename(nome_funcionario).upper()
        timestamp = int(datetime.now().timestamp())
        filename = f"RTC_{nome}_{timestamp}.pdf"
        if qtd_exames == 0:
            filename = f"__VAZIO__RTC_{nome}_{timestamp}.pdf"

        file_path = os.path.join(UPLOAD_FOLDER, filename)

        pdfkit.from_string(
            input=html,
            output_path=file_path,
            configuration=self.get_pdfkit_configs(),
            options=self.pdfkit_options,
        )

        return file_path

    @staticmethod
    def __format_cpf(cpf: str) -> str:
        if len(cpf) == 11:
            return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        else:
            return cpf

    def __get_rtc_checkboxes(self, ids_rtc: list[int]) -> list[tuple[bool, str]]:
        query: list[RTC] = RTC.query.all()
        res = []

        for rtc in query:
            if rtc.id_rtc in ids_rtc:
                res.append((True, rtc.nome_rtc))
            else:
                res.append((False, rtc.nome_rtc))

        return res

    @staticmethod
    def list_to_columns(item_list: list[Any]) -> tuple[list[Any], list[Any]]:
        if len(item_list) <= 1:
            return (item_list, [])

        if len(item_list) % 2 == 0:  # se for par, divisao igual
            sep = int(len(item_list) / 2)
        else:  # se for impar, fazer a coluna A maior do que a B
            sep = int(len(item_list) / 2) + 1

        col_a = item_list[:sep]
        col_b = item_list[sep:]
        return (col_a, col_b)

    @staticmethod
    def gerar_zip(arquivos: list[str]):
        timestamp = int(datetime.now().timestamp())
        nome_zip = f"RTCS_{timestamp}.zip"
        zip_path = os.path.join(UPLOAD_FOLDER, nome_zip)
        zipar_arquivos(caminhos_arquivos=arquivos, caminho_pasta_zip=zip_path)
        return nome_zip

    @staticmethod
    def gerar_df_erros(erros: list[tuple[Pedido, str]]):
        erros2: list[tuple[int, str, str]] = [
            (p.seq_ficha, p.nome_funcionario, err) for p, err in erros
        ]
        df = pd.DataFrame(erros2, columns=["seq_ficha", "funcionario", "erro"])
        return df

    @staticmethod
    def gerar_csv_erros(df_erros: pd.DataFrame):
        timestamp = int(datetime.now().timestamp())
        filename = f"Erros_RTC_{timestamp}.csv"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        df_erros.to_csv(file_path, sep=";", index=False, encoding="iso-8859-1")
        return file_path
