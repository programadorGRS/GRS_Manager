import datetime as dt
import os

import pdfkit
from flask import (redirect, render_template, request, send_from_directory,
                   url_for)
from flask_login import login_required
from werkzeug.utils import secure_filename

from src import UPLOAD_FOLDER, app
from src.main.pedido.forms import FormBuscarASO
from src.main.pedido.pedido import Pedido
from src.utils import get_data_from_args, get_data_from_form, zipar_arquivos

from .forms import FormGerarRTC
from .models import RTC


@app.route('/buscar-rtcs', methods=['GET', 'POST'])
@login_required
def busca_rtc():
    form = FormBuscarASO()
    form.load_choices()

    if form.validate_on_submit():
        parametros = get_data_from_form(data=form.data, ignore_keys=['pesquisa_geral'])
        return redirect(url_for('gerar_rtcs', **parametros))

    return render_template('rtc/busca.html', form=form)


@app.route('/gerar-rtcs', methods=['GET', 'POST'])
@login_required
def gerar_rtcs():
    form: FormGerarRTC = FormGerarRTC()

    data = get_data_from_args(prev_form=FormBuscarASO(), data=request.args)

    id_grupos = data.get('id_grupos')
    if id_grupos is not None:
        data['id_grupos'] = Pedido.handle_group_choice(choice=id_grupos)

    query = Pedido.buscar_pedidos(**data)

    total = Pedido.get_total_busca(query=query)

    if form.validate_on_submit():
        config = pdfkit.configuration(wkhtmltopdf=app.config['WKHTMLTOPDF_PATH'])

        opt = {
            'margin-top': '5mm',
            'margin-right': '5mm',
            'margin-bottom': '5mm',
            'margin-left': '5mm'
        }

        lista_pdfs: list[str] = []
        for id_ficha in request.form.getlist('checkItem', type=int):
            pedido: Pedido = Pedido.query.get(id_ficha)

            infos_ficha = RTC.buscar_infos_rtc(id_ficha)

            html_str = RTC.criar_RTC_html(
                infos=infos_ficha,
                logo_empresa=RTC.LOGO_MANSERV,
                logo_width=RTC.LOGO_MANSERV_WIDTH,
                logo_height=RTC.LOGO_MANSERV_HEIGHT,
                render_tipo_sang=form.tipo_sang.data
            )

            nome_funcionario = secure_filename(pedido.nome_funcionario).upper()
            timestamp = int(dt.datetime.now().timestamp())
            nome_arquivo = f'RTC_{nome_funcionario}_{timestamp}.pdf'
            if len(infos_ficha['cod_exames']) == 0:
                nome_arquivo = f'__VAZIO__RTC_{nome_funcionario}_{timestamp}.pdf'

            file_path = os.path.join(UPLOAD_FOLDER, nome_arquivo)

            pdfkit.from_string(
                input=html_str,
                output_path=file_path,
                configuration=config,
                options=opt
            )
            lista_pdfs.append(file_path)

        timestamp = int(dt.datetime.now().timestamp())
        nome_zip = f'RTCS_{timestamp}.zip'
        zip_path = os.path.join(UPLOAD_FOLDER, nome_zip)

        zipar_arquivos(caminhos_arquivos=lista_pdfs, caminho_pasta_zip=zip_path)

        return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=nome_zip)

    return render_template(
        'rtc/gerar_rtcs.html',
        page_title='Gerar RTCs',
        query=query,
        total=total,
        form=form
    )

