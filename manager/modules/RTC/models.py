from datetime import datetime

import jinja2
from werkzeug.utils import secure_filename

from manager import UPLOAD_FOLDER, database
from manager.models import Exame, Funcionario, Pedido
from manager.utils import get_image_file_as_base64_data


RTCExames = database.Table(
    'RTCExames',
    database.Column('id_rtc', database.Integer, database.ForeignKey('RTC.id_rtc')),
    database.Column('cod_tipo_exame', database.Integer, database.ForeignKey('TipoExame.cod_tipo_exame')),
    database.Column('cod_exame', database.String(255))
)


RTCCargos = database.Table(
    'RTCCargos',
    database.Column('cod_cargo', database.String(255)),
    database.Column('id_rtc', database.ForeignKey('RTC.id_rtc'))
    )


class RTC(database.Model):
    __tablename__ = 'RTC'
    id_rtc = database.Column(database.Integer, primary_key=True, autoincrement=False)
    nome_rtc = database.Column(database.String(255), nullable=False)

    MAIN_TEMPLATE = 'manager/modules/RTC/templates/base_rtc.html'

    # NOTE: em Windows, o tamanho de EMPTY_SQUR é diferente 
    # do tamaho de MARKED_SQUR. Em Linux os dois tem o 
    # mesmo tamanho. Portando, sempre manter os tamanhos iguais
    EMPTY_SQUR = '&#9633;'
    EMPTY_SQUR_SIZE = '15pt'
    MARKED_SQUR = '&#9746;'
    MARKED_SQUR_SIZE = '15pt'

    LOGO_GRS = 'manager/static/images/grs/Logo GRS-01.jpg'
    LOGO_GRS_WIDTH = '70px'
    LOGO_GRS_HEIGHT = '30px'

    LOGO_MANSERV = 'manager/modules/RTC/templates/logo_manserv.png'
    LOGO_MANSERV_WIDTH = '150px'
    LOGO_MANSERV_HEIGHT = '30px'

    @classmethod
    def buscar_infos_rtc(self, id_ficha: int):
        pedido: Pedido = Pedido.query.get(id_ficha)

        # buscar Funcionario da Ficha
        funcionario: Funcionario = (
            database.session.query(Funcionario)
            .filter(Funcionario.cod_funcionario == pedido.cod_funcionario)
            .filter(Funcionario.id_empresa == pedido.id_empresa)
            .first()
        )

        # buscar RTCs que atendem o Cargo do Funcionario
        ids_rtcs_do_cargo = (
            database.session.query(RTCCargos)
            .filter(RTCCargos.c.cod_cargo == funcionario.cod_cargo)
        )
        ids_rtcs_do_cargo = [i.id_rtc for i in ids_rtcs_do_cargo]

        # buscar exames que fazem parte das RTCs de acordo com Tipo de Ficha
        exames_do_rtc = (
            database.session.query(RTCExames)
            .filter(RTCExames.c.id_rtc.in_(ids_rtcs_do_cargo))
            .filter(RTCExames.c.cod_tipo_exame == pedido.cod_tipo_exame)
        )
        exames_do_rtc = [i.cod_exame for i in exames_do_rtc]
        exames_do_rtc = list(dict.fromkeys(exames_do_rtc)) # remove duplicates

        infos = {
            'id_ficha': pedido.id_ficha,
            'nome_funcionario': pedido.nome_funcionario,
            'cpf_funcionario': pedido.cpf,
            'data_adm': funcionario.data_adm,
            'cargo_funcionario': funcionario.nome_cargo,
            'setor_funcionario': funcionario.nome_setor,
            'ids_rtcs': ids_rtcs_do_cargo,
            'cod_exames': exames_do_rtc
        }

        return infos

    @classmethod
    def criar_RTC_html(
        self,
        infos: dict[str, any],
        template: str = MAIN_TEMPLATE,
        logo_empresa: str = LOGO_GRS,
        logo_width: str = LOGO_GRS_WIDTH,
        logo_height: str = LOGO_GRS_HEIGHT,
        criar_arquivo: bool = False
    ) -> str:
        """Recebe informacoes sobre a Ficha e Funcionario e cria modelo HTML da RTC

        Usar com o dicionario de RTC.buscar_infos_rtc

        Returns:
            if criar_rtc:
                str: html file path
            else:
                str: html body str
        """
        PEDIDO: Pedido = Pedido.query.get(infos['id_ficha'])


        # format cpf
        if len(infos['cpf_funcionario']) == 11:
            infos['cpf_funcionario'] = f"{infos['cpf_funcionario'][:3]}.{infos['cpf_funcionario'][3:6]}.{infos['cpf_funcionario'][6:9]}-{infos['cpf_funcionario'][9:]}"


        # RTCs
        rtcs_geral = RTC.query.all()
        infos['lista_rtcs'] = []
        # pegar todas rtc e marcar as usadas
        for i in rtcs_geral:
            if i.id_rtc in infos['ids_rtcs']:
                infos['lista_rtcs'].append((self.MARKED_SQUR_SIZE, self.MARKED_SQUR, i.nome_rtc))
            else:
                infos['lista_rtcs'].append((self.EMPTY_SQUR_SIZE, self.EMPTY_SQUR, i.nome_rtc))

        # criar duas colunas de RTC
        colunas_ab = self._criar_colunas_ab(infos['lista_rtcs'])
        infos['col_rtc_a'] = colunas_ab[0]
        infos['col_rtc_b'] = colunas_ab[1]


        # EXAMES
        # NOTE: sempre usar filtro de cod_empresa_principal, pois algumas Empresas principais
        # podem ter Exames iguais, causando duplicidade de Exames no RTC
        nomes_exames = (
            database.session.query(Exame)
            .filter(Exame.cod_exame.in_(infos['cod_exames']))
            .filter(Exame.cod_empresa_principal == PEDIDO.cod_empresa_principal)
        )
        infos['lista_exames'] = [i.nome_exame for i in nomes_exames]

        # criar duas colunas de exames
        colunas_ab = self._criar_colunas_ab(infos['lista_exames'])
        infos['col_exames_a'] = colunas_ab[0]
        infos['col_exames_b'] = colunas_ab[1]


        # LOGO
        infos['logo_empresa'] = get_image_file_as_base64_data(img_path=logo_empresa)
        infos['logo_width'] = logo_width
        infos['logo_height'] = logo_height


        # render template as string
        template_loader = jinja2.FileSystemLoader('./')
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.get_template(self.MAIN_TEMPLATE)
        output_text = template.render(infos)

        if criar_arquivo:
            nome_funcionario = secure_filename(infos['nome_funcionario']).upper()
            file_name = f"{UPLOAD_FOLDER}/RTC_{nome_funcionario}_{int(datetime.now().timestamp())}.html"
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(output_text)
            return file_name
        else:
            return output_text

    @staticmethod
    def _criar_colunas_ab(lista_itens: list) -> tuple[list, list]:
        if len(lista_itens) <= 1:
            return (lista_itens, [])

        if len(lista_itens) % 2 == 0: # se for par, divisao igual
            separador = int(len(lista_itens) / 2)
        else: # se for impar, fazer a coluna A maior do que a B
            separador = int(len(lista_itens) / 2) + 1
        col_a = lista_itens[:separador]
        col_b = lista_itens[separador:]
        return (col_a, col_b)

