import datetime as dt

import pdfkit
from flask import (redirect, render_template, request, send_from_directory,
                   url_for)
from flask_login import login_required
from werkzeug.utils import secure_filename

from src import UPLOAD_FOLDER, app
from src.forms import FormBuscarASO
from src.main.pedido.pedido import Pedido
from src.modules.RTC.forms import FormGerarRTC
from src.modules.RTC.models import RTC
from src.utils import get_data_from_form, zipar_arquivos


# BUSCA ----------------------------------------
@app.route('/busca_rtc', methods=['GET', 'POST'])
@login_required
def busca_rtc():
    form = FormBuscarASO()
    form.load_choices()
    
    if form.validate_on_submit():
        parametros = get_data_from_form(data=form.data, ignore_keys=['pesquisa_geral'])
        return redirect(url_for('gerar_rtcs', **parametros))
    return render_template('rtc/busca.html', form=form, title='GRS+Connect')


@app.route('/gerar_rtcs', methods=['GET', 'POST'])
@login_required
def gerar_rtcs():
    form = FormGerarRTC()

    datas = {
        'data_inicio': request.args.get('data_inicio', type=str, default=None),
        'data_fim': request.args.get('data_fim', type=str, default=None)
    }
    for chave, valor in datas.items():
        if valor:
            datas[chave] = dt.datetime.strptime(valor, '%Y-%m-%d').date()

    query_pedidos = Pedido.buscar_pedidos(
        id_grupos=Pedido.handle_group_choice(choice=request.args.get('id_grupos')),
        cod_empresa_principal=request.args.get('cod_empresa_principal', type=int, default=None),
        data_inicio=datas['data_inicio'],
        data_fim=datas['data_fim'],
        id_status=request.args.get('id_status', type=int, default=None),
        id_status_rac=request.args.get('id_status_rac', type=int, default=None),
        id_tag=request.args.get('id_tag', type=int, default=None),
        id_empresa=request.args.get('id_empresa', type=int, default=None),
        id_unidade=request.args.get('id_unidade', type=int, default=None),
        id_prestador=request.args.get('id_prestador', type=int, default=None),
        seq_ficha=request.args.get('seq_ficha', type=int, default=None),
        nome_funcionario=request.args.get('nome_funcionario', type=str, default=None),
        obs=request.args.get('obs', type=str, default=None)
    )

    total = Pedido.get_total_busca(query=query_pedidos)

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
            nome_funcionario = secure_filename(pedido.nome_funcionario).upper()

            infos_ficha = RTC.buscar_infos_rtc(id_ficha)
            html_str = RTC.criar_RTC_html(
                infos=infos_ficha,
                logo_empresa=RTC.LOGO_MANSERV,
                logo_width=RTC.LOGO_MANSERV_WIDTH,
                logo_height=RTC.LOGO_MANSERV_HEIGHT
            )

            nome_pdf = f'{UPLOAD_FOLDER}/RTC_{nome_funcionario}_{int(dt.datetime.now().timestamp())}.pdf'
            if len(infos_ficha['cod_exames']) == 0:
                nome_pdf = f'{UPLOAD_FOLDER}/__VAZIO__RAC_{nome_funcionario}_{int(dt.datetime.now().timestamp())}.pdf'

            pdfkit.from_string(
                input=html_str,
                output_path=nome_pdf,
                configuration=config,
                options=opt
            )
            lista_pdfs.append(nome_pdf)
        
        nome_zip = f'{UPLOAD_FOLDER}/RTCS_{int(dt.datetime.now().timestamp())}.zip'
        zipar_arquivos(caminhos_arquivos=lista_pdfs, caminho_pasta_zip=nome_zip)

        return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=nome_zip.split('/')[-1])

    return render_template(
        'rtc/gerar_rtcs.html',
        title='GRS+Connect',
        busca=query_pedidos,
        total=total,
        form=form
    )

