import datetime as dt

import pandas as pd
from flask import (flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required
from pytz import timezone
from sqlalchemy import delete, insert

from src import UPLOAD_FOLDER, app, database
from src.main.empresa.empresa import Empresa
from src.main.empresa_socnet.empresa_socnet import EmpresaSOCNET
from src.main.grupo.grupo import (Grupo, grupo_empresa, grupo_empresa_socnet,
                                  grupo_prestador, grupo_usuario)
from src.main.log_acoes.log_acoes import LogAcoes
from src.main.prestador.prestador import Prestador
from src.main.usuario.usuario import Usuario
from src.utils import zipar_arquivos

from .forms import FormCriarGrupo, FormGrupoPrestadores


@app.route('/grupos')
@login_required
def grupos():
    lista_grupos = Grupo.query.order_by(Grupo.nome_grupo).all()
    return render_template('grupo/grupos.html', title='GRS+Connect', lista_grupos=lista_grupos)

@app.route('/grupos/criar', methods=['GET', 'POST'])
@login_required
def grupos_criar():
    form = FormCriarGrupo()

    if form.validate_on_submit():
        grupo = Grupo(
            nome_grupo=form.nome_grupo.data,
            data_inclusao=dt.datetime.now(tz=timezone('America/Sao_Paulo')),
            incluido_por=current_user.username 
        )
        database.session.add(grupo)
        database.session.commit()

        grupo_criado = Grupo.query.filter_by(nome_grupo=form.nome_grupo.data).first()

        LogAcoes.registrar_acao(
            nome_tabela='Grupo',
            tipo_acao='Inclusão',
            id_registro=grupo_criado.id_grupo,
            nome_registro=grupo_criado.nome_grupo,
        )

        flash('Grupo criado com sucesso!', 'alert-success')
        return redirect(url_for('grupos'))
    return render_template('grupo/grupo_criar.html', title='GRS+Connect', form=form)

@app.route('/grupos/editar', methods=['GET', 'POST'])
@login_required
def grupos_editar():
    grupo = Grupo.query.get(request.args.get('id_grupo', type=int))

    form = FormCriarGrupo(
        nome_grupo=grupo.nome_grupo,
        data_inclusao=grupo.data_inclusao,
        data_alteracao=grupo.data_alteracao,
        incluido_por=grupo.incluido_por,
        alterado_por=grupo.alterado_por
    )

    if form.validate_on_submit():
        grupo.nome_grupo = form.nome_grupo.data

        grupo.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
        grupo.alterado_por = current_user.username

        database.session.commit()

        LogAcoes.registrar_acao(
            nome_tabela='Grupo',
            tipo_acao='Alteração',
            id_registro=grupo.id_grupo,
            nome_registro=form.nome_grupo.data
        )
        
        flash('Grupo editado com sucesso!', 'alert-success')
        return redirect(url_for('grupos'))
        
    return render_template(
        'grupo/grupo_editar.html',
        title='GRS+Connect',
        grupo=grupo,
        form=form
    )

@app.route('/grupos/usuarios',  methods=['GET', 'POST'])
@login_required
def grupos_usuarios():
    grupo: Grupo = Grupo.query.get(request.args.get('id_grupo', type=int))
    
    # already in group
    pre_selected = [i.id_usuario for i in grupo.usuarios]
    
    # create form with pre selected values
    form = FormGrupoPrestadores(select=pre_selected)
    form.select.choices = [
        (i.id_usuario, i.username)
        for i in Usuario.query.all()
    ]
    # sort choices by name, ascending
    form.select.choices.sort(key=lambda tup: tup[1], reverse=False)
    
    if form.validate_on_submit():
        Grupo.update_grupo_usuario(
            id_grupo=grupo.id_grupo,
            id_usuarios=request.form.getlist(key='select', type=int),
            alterado_por=current_user.username
        )

        LogAcoes.registrar_acao(
            nome_tabela='Grupo',
            tipo_acao='Editar Usuários',
            id_registro=grupo.id_grupo,
            nome_registro=grupo.nome_grupo
        )

        return redirect(url_for('grupos'))

    return render_template(
        'grupo/grupo_usuarios.html',
        title='GRS+Connect',
        form=form,
        grupo=grupo
    )

@app.route('/grupos/prestadores',  methods=['GET', 'POST'])
@login_required
def grupos_prestadores():
    grupo: Grupo = Grupo.query.get(request.args.get('id_grupo', type=int))
    
    #  already in group
    pre_selected = [i.id_prestador for i in grupo.prestadores]
    
    # create form with pre selected values
    form = FormGrupoPrestadores(select=pre_selected)
    form.select.choices = [
        (i.id_prestador, i.nome_prestador)
        for i in Prestador.query.all()
    ]
    # sort choices by name, ascending
    form.select.choices.sort(key=lambda tup: tup[1], reverse=False)
    
    if form.validate_on_submit():
        Grupo.update_grupo_prestador(
            id_grupo=grupo.id_grupo,
            id_prestadores=request.form.getlist(key='select', type=int),
            alterado_por=current_user.username
        )

        LogAcoes.registrar_acao(
            nome_tabela='Grupo',
            tipo_acao='Editar Prestadores',
            id_registro=grupo.id_grupo,
            nome_registro=grupo.nome_grupo
        )

        return redirect(url_for('grupos'))
    
    return render_template(
        'grupo/grupo_prestadores.html',
        title='GRS+Connect',
        form=form,
        grupo=grupo
    )

@app.route('/grupos/empresas',  methods=['GET', 'POST'])
@login_required
def grupos_empresas():
    grupo: Grupo = Grupo.query.get(request.args.get('id_grupo', type=int))
    
    # already in group
    pre_selected = [i.id_empresa for i in grupo.empresas]
    
    # create form with pre selected values
    form = FormGrupoPrestadores(select=pre_selected)
    form.select.choices = [
        (i.id_empresa, i.razao_social)
        for i in Empresa.query.all()
    ]
    # sort choices by name, ascending
    form.select.choices.sort(key=lambda tup: tup[1], reverse=False)
    
    if form.validate_on_submit():
        Grupo.update_grupo_empresa(
            id_grupo=grupo.id_grupo,
            id_empresas=request.form.getlist(key='select', type=int),
            alterado_por=current_user.username
        )

        LogAcoes.registrar_acao(
            nome_tabela='Grupo',
            tipo_acao='Editar Empresas',
            id_registro=int(grupo.id_grupo),
            nome_registro=grupo.nome_grupo
        )

        return redirect(url_for('grupos'))

    return render_template(
        'grupo/grupo_empresas.html',
        title='GRS+Connect',
        form=form,
        grupo=grupo
    )

@app.route('/grupos_csv')
@login_required
def grupos_csv():
    timestamp = int(dt.datetime.now().timestamp())
    
    # empresas
    q = (
        database.session.query(
            Empresa.id_empresa,
            Empresa.razao_social,
            grupo_empresa.columns.id_grupo,
            Grupo.nome_grupo,
        )
        .outerjoin(grupo_empresa, Empresa.id_empresa == grupo_empresa.columns.id_empresa)
        .outerjoin(Grupo, Grupo.id_grupo == grupo_empresa.columns.id_grupo)
        .order_by(Empresa.razao_social)
    )
    df = pd.read_sql(sql=q.statement, con=database.session.bind)
    df.to_csv(
        f'{UPLOAD_FOLDER}/grupo_empresas_{timestamp}.csv',
        sep=';',
        index=False,
        encoding='iso-8859-1',
        float_format='%.0f'
    )
    
    # empresas SOCNET
    q = (
        database.session.query(
            EmpresaSOCNET.id_empresa,
            EmpresaSOCNET.nome_empresa,
            grupo_empresa_socnet.columns.id_grupo,
            Grupo.nome_grupo,
        )
        .outerjoin(grupo_empresa_socnet, EmpresaSOCNET.id_empresa == grupo_empresa_socnet.columns.id_empresa)
        .outerjoin(Grupo, Grupo.id_grupo == grupo_empresa_socnet.columns.id_grupo)
        .order_by(EmpresaSOCNET.nome_empresa)
    )
    df = pd.read_sql(sql=q.statement, con=database.session.bind)
    df.to_csv(
        f'{UPLOAD_FOLDER}/grupo_empresas_socnet_{timestamp}.csv',
        sep=';',
        index=False,
        encoding='iso-8859-1',
        float_format='%.0f'
    )
    
    # prestadores
    q = (
        database.session.query(
            Prestador.id_prestador,
            Prestador.nome_prestador,
            grupo_prestador.columns.id_grupo,
            Grupo.nome_grupo,
        )
        .outerjoin(grupo_prestador, Prestador.id_prestador == grupo_prestador.columns.id_prestador)
        .outerjoin(Grupo, Grupo.id_grupo == grupo_prestador.columns.id_grupo)
        .order_by(Prestador.nome_prestador)
    )
    df = pd.read_sql(sql=q.statement, con=database.session.bind)
    df.to_csv(
        f'{UPLOAD_FOLDER}/grupo_prestadores_{timestamp}.csv',
        sep=';',
        index=False,
        encoding='iso-8859-1',
        float_format='%.0f'
    )
    
    # usuarios
    q = (
        database.session.query(
            Usuario.id_usuario,
            Usuario.username,
            grupo_usuario.columns.id_grupo,
            Grupo.nome_grupo,
        )
        .outerjoin(grupo_usuario, Usuario.id_usuario == grupo_usuario.columns.id_usuario)
        .outerjoin(Grupo, Grupo.id_grupo == grupo_usuario.columns.id_grupo)
        .order_by(Usuario.username)
    )
    df = pd.read_sql(sql=q.statement, con=database.session.bind)
    df.to_csv(
        f'{UPLOAD_FOLDER}/grupo_usuarios_{timestamp}.csv',
        sep=';',
        index=False,
        encoding='iso-8859-1',
        float_format='%.0f'
    )
    
    # compactar
    pasta_zip = zipar_arquivos(
        caminhos_arquivos=[
            f'{UPLOAD_FOLDER}/grupo_empresas_{timestamp}.csv',
            f'{UPLOAD_FOLDER}/grupo_empresas_socnet_{timestamp}.csv',
            f'{UPLOAD_FOLDER}/grupo_prestadores_{timestamp}.csv',
            f'{UPLOAD_FOLDER}/grupo_usuarios_{timestamp}.csv'
        ],
        caminho_pasta_zip= f'{UPLOAD_FOLDER}/Grupos_{timestamp}.zip'
    )
    pasta_zip = pasta_zip.split('/')[-1]
    
    return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=pasta_zip)

@app.route('/grupos/excluir', methods=['GET', 'POST'])
@login_required
def grupos_excluir():
    grupo = Grupo.query.get(request.args.get('id_grupo', type=int))
    
    database.session.delete(grupo)
    database.session.commit()

    # registrar acao
    LogAcoes.registrar_acao(
        nome_tabela='Grupo',
        tipo_acao='Exclusão',
        id_registro=int(grupo.id_grupo),
        nome_registro=grupo.nome_grupo
    )
    
    flash('Grupo excluído!', 'alert-danger')
    return redirect(url_for('grupos'))

@app.route('/grupos/empresas_socnet',  methods=['GET', 'POST'])
@login_required
def grupos_empresas_socnet():
    grupo = Grupo.query.get(request.args.get('id_grupo', type=int))
    
    # already in group
    pre_selected = [i.id_empresa for i in grupo.empresas_socnet]
    
    # create form with pre selected values
    form = FormGrupoPrestadores(select=pre_selected)
    form.select.choices = [
        (i.id_empresa, i.nome_empresa)
        for i in EmpresaSOCNET.query.all()
    ]
    # sort choices by name, ascending
    form.select.choices.sort(key=lambda tup: tup[1], reverse=False)
    
    if form.validate_on_submit():
        # reset current group
        delete_query = database.session.execute(
            delete(grupo_empresa_socnet).
            where(grupo_empresa_socnet.c.id_grupo == grupo.id_grupo)
        )

        # insert all the selected objects
        insert_items = [
            {'id_grupo': grupo.id_grupo, 'id_empresa': i}
            for i in request.form.getlist(key='select', type=int)
        ]
        insert_query = database.session.execute(
            insert(grupo_empresa_socnet).
            values(insert_items)
        )

        grupo.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
        grupo.alterado_por = current_user.username
        database.session.commit()

        # registrar acao
        LogAcoes.registrar_acao(
            nome_tabela='Grupo',
            tipo_acao='Editar Empresas SOCNET',
            id_registro=int(grupo.id_grupo),
            nome_registro=grupo.nome_grupo
        )
    
        return redirect(url_for('grupos'))
    
    return render_template(
        'grupo/grupo_empresas_socnet.html',
        title='GRS+Connect',
        form=form,
        grupo=grupo
    )

