import os
from datetime import datetime
from typing import Any

import pandas as pd
from flask import (Blueprint, flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import login_required
from werkzeug.utils import secure_filename

from src import UPLOAD_FOLDER, database
from src.main.empresa.empresa import Empresa
from src.main.empresa_principal.empresa_principal import EmpresaPrincipal
from src.main.exame.exame import Exame
from src.main.funcionario.funcionario import Funcionario
from src.main.unidade.unidade import Unidade
from src.utils import get_data_from_form, zipar_arquivos

from .forms import FormBuscarPedidoProcessamento, FormGerarRelatorios
from .models import ConvExames, PedidoProcessamento


conv_exames = Blueprint(
    name="conv_exames",
    import_name=__name__,
    url_prefix="/conv-exames",
    template_folder="templates",
)


@conv_exames.route("/pedido-proc/buscar", methods=["GET", "POST"])
@login_required
def buscar_pedidos_proc():
    form = FormBuscarPedidoProcessamento()
    form.load_choices()
    form.title = "Buscar Pedidos de Processamento"

    if form.validate_on_submit():
        params = get_data_from_form(form.data)

        if "botao_buscar" in request.form:
            return redirect(url_for("conv_exames.listar_pedidos_proc", **params))

        elif "botao_csv" in request.form:
            return redirect(url_for("conv_exames.csv_pedidos_proc", **params))

    return render_template("conv_exames/busca_ped_proc.html", form=form)


@conv_exames.route("/pedido-proc/busca/resultados", methods=["GET", "POST"])
@login_required
def listar_pedidos_proc():
    prev_form = FormBuscarPedidoProcessamento()
    args = prev_form.get_url_args(data=request.args)

    query = PedidoProcessamento.buscar_pedidos_proc(**args)

    total = query.count()

    return render_template("conv_exames/pedidos_proc.html", query=query, total=total)


@conv_exames.route("/pedido-proc/busca/csv")
@login_required
def csv_pedidos_proc():
    prev_form = FormBuscarPedidoProcessamento()
    args = prev_form.get_url_args(data=request.args)

    query = PedidoProcessamento.buscar_pedidos_proc(**args)

    query = query.join(
        EmpresaPrincipal,
        PedidoProcessamento.cod_empresa_principal == EmpresaPrincipal.cod,
    ).add_columns(Empresa.razao_social, EmpresaPrincipal.nome, Empresa.ativo)

    df = pd.read_sql(sql=query.statement, con=database.session.bind)  # type: ignore
    df = df[PedidoProcessamento.COLUNAS_CSV]

    timestamp = int(datetime.now().timestamp())
    nome_arqv = f"PedidosProcessamento_{timestamp}.csv"
    camihno_arqv = f"{UPLOAD_FOLDER}/{nome_arqv}"
    df.to_csv(camihno_arqv, sep=";", index=False, encoding="iso-8859-1")

    return send_from_directory(directory=UPLOAD_FOLDER, path="/", filename=nome_arqv)


@conv_exames.route("/pedido-proc/<int:id_proc>", methods=["GET", "POST"])
@login_required
def pag_pedido_proc(id_proc):
    ped_proc = PedidoProcessamento.query.get(id_proc)

    form: FormGerarRelatorios = FormGerarRelatorios()
    form.form_action = url_for("conv_exames.ped_proc_gerar_reports", id_proc=id_proc)  # type: ignore
    form.load_choices(id_empresa=ped_proc.id_empresa)

    form.title = f"Pedido de Processamento #{ped_proc.id_proc}"  # type: ignore
    form.sub_title = "Gerar Relatórios"  # type: ignore

    if form.validate_on_submit():
        return redirect(url_for("conv_exames.ped_proc_gerar_reports", id_proc=id_proc))

    return render_template(
        "conv_exames/gerar_relatorios.html",
        form=form,
        ped_proc=ped_proc,
        ppt_trigger=ConvExames.PPT_TRIGGER,
    )


@conv_exames.route(
    "/pedido-proc/<int:id_proc>/gerar_relatorios", methods=["GET", "POST"]
)
@login_required
def ped_proc_gerar_reports(id_proc):
    ped_proc: PedidoProcessamento = PedidoProcessamento.query.get(id_proc)

    empresa: Empresa = Empresa.query.get(ped_proc.id_empresa)

    prev_form = FormGerarRelatorios()
    args: dict[str, Any] = prev_form.get_request_form_data(data=request.form)

    query = (
        database.session.query(  # type: ignore
            ConvExames,
            Empresa.razao_social,
            Unidade.nome_unidade,
            Funcionario.cpf_funcionario,
            Funcionario.nome_funcionario,
            Funcionario.cod_setor,
            Funcionario.nome_setor,
            Funcionario.cod_cargo,
            Funcionario.nome_cargo,
            Exame.nome_exame,
        )
        .join(Empresa, ConvExames.id_empresa == Empresa.id_empresa)
        .join(Unidade, ConvExames.id_unidade == Unidade.id_unidade)
        .join(Funcionario, ConvExames.id_funcionario == Funcionario.id_funcionario)
        .join(Exame, ConvExames.id_exame == Exame.id_exame)
        .filter(ConvExames.id_proc == ped_proc.id_proc)
    )

    nome_unidade = "Todas"
    unidades: list[int] = args.get("unidades")  # type: ignore
    if unidades:
        query = query.filter(ConvExames.id_unidade.in_(unidades))

        if len(unidades) == 1:
            nome_unidade = Unidade.query.get(unidades[0]).nome_unidade
        elif len(unidades) > 1:
            nome_unidade = "Várias"

    arquivos = ConvExames.criar_relatorios2(
        query=query,
        nome_empresa=empresa.razao_social,
        gerar_ppt=args.get("gerar_ppt"),  # type: ignore
        nome_unidade=nome_unidade,
        data_origem=ped_proc.data_criacao,
        filtro_status=args.get("status"),  # type: ignore
        filtro_a_vencer=args.get("a_vencer"),  # type: ignore
    )

    if arquivos:
        nome_empresa = secure_filename(empresa.razao_social).replace(".", "_").upper()
        timestamp = int(datetime.now().timestamp())
        nome_pasta = os.path.join(
            UPLOAD_FOLDER, f"ConvExames_{nome_empresa}_{timestamp}.zip"
        )

        pasta_zip = zipar_arquivos(
            caminhos_arquivos=list(arquivos.values()), caminho_pasta_zip=nome_pasta
        )
        return send_from_directory(
            directory=UPLOAD_FOLDER, path="/", filename=os.path.basename(pasta_zip)
        )
    else:
        flash("Sem resultados", "alert-info")
        return redirect(
            url_for("conv_exames.pag_pedido_proc", id_proc=ped_proc.id_proc)
        )
