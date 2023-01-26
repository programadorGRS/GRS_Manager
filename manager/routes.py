import base64
import datetime as dt
import os
import secrets
import traceback
from random import randint
from time import sleep

import pandas as pd
from flask import (abort, flash, redirect, render_template,
                   request, send_from_directory, session, url_for)
from flask_login import (confirm_login, current_user, fresh_login_required,
                         login_fresh, login_required, login_user, logout_user)
from flask_mail import Attachment, Message
from pytz import timezone
from sqlalchemy.exc import IntegrityError
from sqlalchemy import delete, insert

from manager import UPLOAD_FOLDER, app, bcrypt, database, mail
from manager.email import corpo_email_otp
from manager.forms import (FormAlterarChave, FormAlterarSenha,
                           FormConfigUsuario, FormCriarConta, FormCriarGrupo,
                           FormCriarStatus, FormEditarPerfil,
                           FormGrupoPrestadores, FormLogAcoes, FormLogin,
                           FormOTP)
from manager.models import (Empresa, Grupo, LogAcoes, Login,
                            Prestador, Status, TipoUsuario, Usuario,
                            grupo_empresa,
                            grupo_prestador, grupo_usuario)
from manager.models_socnet import EmpresaSOCNET, grupo_empresa_socnet
from manager.utils import admin_required, is_safe_url, zipar_arquivos

# TODO: verificar duplicidade de pedidos
# TODO: incluir colunas de grupo no relatorio de ASOs

# TODO: criar pag para emitir relatorios de absenteismo no site (igual aos exames realizados)

# TODO: incluir funcao para atualizar os pedidos SOCNET que ja existem quando a planilha for inserida

# TODO: refazer telas de associacao de Grupos (basear na route de prestadores)
# TODO: incluir funcoes de tag prev liberacao para SOCNET
# TODO: incluir funcao de atualizar status via CSV
# TODO: incluir funcao do executavel de emails nao compareceu para o criador da ficha
# TODO: criar tabela para registrar envios das convocacaoes de exames
# TODO: criar tabela para registrar requests e responses entre Connect e SOC (eliminar necessidade de reports via email)

# NOTE: ao importar modulos de fora do pacote "manager",
# manter import dentro da funcao para evitar conflitos de importacao
# ex: from modules.funcoes_database import atualizar_pedidos (dentro da route)


# LOGIN-----------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    form = FormLogin()
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    elif form.validate_on_submit():
        sleep(randint(0, 5))
        
        usuario = Usuario.query.filter_by(username=form.username.data).first()
        if usuario and usuario.is_active and bcrypt.check_password_hash(
            usuario.senha.encode('utf-8'),
            form.senha.data
        ):
            # gerar otp
            otp = base64.b32encode(os.urandom(10)).decode('utf-8')
            usuario.otp = bcrypt.generate_password_hash(otp).decode('utf-8')
            database.session.add(usuario)
            database.session.commit()

            # eviar email
            horario = (
                dt.datetime.now(tz=timezone('America/Sao_Paulo'))
                .strftime('%d-%m-%Y %H:%M:%S')
            )
            email_body = corpo_email_otp(
                nome_dest=usuario.nome_usuario,
                username_dest=usuario.username,
                current_datetime=horario,
                otp_usuario=otp
            )
            assinatura = 'static/images/ass_bot.png'
            anexos = Attachment(
                filename=assinatura,
                content_type='image/png',
                data=app.open_resource(assinatura).read(),
                disposition='inline',
                headers=[['Content-ID','<AssEmail>']]
            )
            msg = Message(
                subject=f'Manager - Chave de acesso',
                recipients=[usuario.email],
                html=email_body,
                attachments=[anexos]
            )
            mail.send(msg)

            # registrar tentativa
            Login.log_attempt(
                username=form.username.data,
                tela='login',
                ip=Login.get_ip(),
                obs='OK'
            )
            
            # guardar username na sessao
            session['username'] = usuario.username
            flash('A chave temporária foi enviada para o seu email', 'alert-info')
            return redirect(url_for('login_otp'))
        else:
            # registrar tentativa
            Login.log_attempt(
                username=form.username.data,
                tela='login',
                ip=Login.get_ip(),
                obs='Recusado'
            )
            flash(f'Username ou Senha incorretos', 'alert-danger')
    return render_template('login/login.html', form_login=form, title='GRS+Connect')


# LOGIN OTP-----------------------------------------------------
@app.route('/two_factor', methods=['GET', 'POST'])
def login_otp():
    form = FormOTP()        
    if 'username' in session:
        usuario = Usuario.query.filter_by(username=session['username']).first()
        if usuario:
            if form.validate_on_submit():
                sleep(randint(0, 5))
                
                if bcrypt.check_password_hash(
                    usuario.otp.encode('utf-8'),
                    form.otp.data
                ):
                    # remover username da sessao
                    del session['username']

                    login_user(usuario)

                    # registrar tentativa
                    Login.log_attempt(
                        username=usuario.username,
                        tela='login_otp',
                        ip=Login.get_ip(),
                        obs='OK'
                    )

                    # atualizar horario do login
                    current_user.ultimo_login = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
                    database.session.commit()
                    
                    flash(f'Logado com sucesso em: {usuario.username}', 'alert-success')
                    return redirect(url_for('home'))
                else:
                    Login.log_attempt(
                        username=usuario.username,
                        tela='login_otp',
                        ip=Login.get_ip(),
                        obs='Recusado'
                    )
                    flash(f'Chave inválida', 'alert-danger')
        else:
            flash(f'Username ou Senha incorretos', 'alert-danger')
            return redirect(url_for('login'))
    else:
        abort(404)
    return render_template('login/login_otp.html', form=form, title='GRS+Connect')


# REFRESH LOGIN-----------------------------------------------------
@app.route('/refresh_login', methods=['GET', 'POST'])
@login_required
def refresh_login():
    form = FormLogin()
    if login_fresh():
        return redirect(url_for('home'))
    elif form.validate_on_submit():
        usuario = Usuario.query.filter_by(username=form.username.data).first()
        if usuario and usuario.is_active and bcrypt.check_password_hash(
            usuario.senha.encode('utf-8'),
            form.senha.data
        ):
            confirm_login()

            # resgistrar tentativa
            Login.log_attempt(
                username=usuario.username,
                tela='refresh_login',
                ip=Login.get_ip(),
                obs='OK'
            )

            # atualizar horario do login
            Usuario.update_ultimo_login()

            # redirecionar
            par_next = request.args.get(key='next', type=str)
            if par_next and is_safe_url(par_next):
                flash(f'Autenticado com sucesso em: {usuario.username}', 'alert-success')
                return redirect(par_next)
            else:
                return redirect(url_for('home'))
        else:
            Login.log_attempt(
                username=usuario.username,
                tela='refresh_login',
                ip=Login.get_ip(),
                obs='Recusado'
            )
            flash(f'Username ou Senha incorretos', 'alert-danger')
    return render_template('login.html', form_login=form, title='GRS+Connect')


# HOME--------------------------------------------------------
@app.route('/home')
@login_required
def home():
    return render_template('home.html', title='GRS+Connect')


# USUARIOS--------------------------------------------------------------
@app.route('/usuarios')
@login_required
def usuarios():
    lista_usuarios = (
        database.session.query(Usuario)
        .order_by(Usuario.tipo_usuario, Usuario.username)
    )

    return render_template(
        'usuario/usuarios.html',
        lista_usuarios=lista_usuarios,
        title='GRS+Connect'
    )


# USUARIO-------------------------------------------------------------
@app.route('/usuarios/<int:id_usuario>')
@login_required
def perfil(id_usuario):
    
    usuario = Usuario.query.get(id_usuario)
    
    return render_template(
        'usuario/perfil_usuario.html',
        title='GRS+Connect',
        usuario=usuario
    )


# CRIAR USUARIO--------------------------------------------------
@app.route('/usuarios/criar', methods=['GET', 'POST'])
@fresh_login_required
@admin_required
def criar_conta():
    form = FormCriarConta()

    form.tipo_usuario.choices = (
        [('', 'Selecione')] +
        [(role.id_role, role.nome) for role in TipoUsuario.query.all()]
    )

    if form.validate_on_submit():
        usuario = Usuario.criar_usuario(
            username=form.username.data,
            nome_usuario=form.nome_usuario.data,
            telefone=form.tel.data,
            celular=form.cel.data,
            email=form.email.data,
            senha=form.senha.data,
            tipo_usuario=form.tipo_usuario.data,
            incluido_por=current_user.username
        )

        LogAcoes.registrar_acao(
            nome_tabela='Usuario',
            tipo_acao='Inclusão',
            id_registro=usuario.id_usuario,
            nome_registro=usuario.username
        )

        flash(f'Conta criada com sucesso para: {form.username.data}', 'alert-success')
        return redirect(url_for('usuarios'))
    return render_template('usuario/criar_usuario.html', form_criarconta=form, title='GRS+Connect')


# EDITAR USUARIO----------------------------------------------------
@app.route('/usuarios/editar', methods=['GET', 'POST'])
@fresh_login_required
def editar_perfil():
    id_usuario = request.args.get('id_usuario', type=int)
    usuario = Usuario.query.get(id_usuario)

    form = FormEditarPerfil(
        username=usuario.username,
        nome_usuario=usuario.nome_usuario,
        email=usuario.email,
        tel=usuario.telefone,
        cel=usuario.celular
    )

    if current_user.id_usuario == id_usuario or current_user.tipo_usuario == 1:
        if form.validate_on_submit():
            
            # se mudar username, atualizar id cookie
            if form.username.data != usuario.username:
                usuario.id_cookie = secrets.token_hex(16)

            usuario.username = form.username.data
            usuario.nome_usuario = form.nome_usuario.data
            usuario.email = form.email.data
            usuario.telefone = form.tel.data
            usuario.celular = form.cel.data
            usuario.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
            usuario.alterado_por = current_user.username

            database.session.commit()

            LogAcoes.registrar_acao(
                nome_tabela = 'Usuario',
                tipo_acao = 'Alteração de Nome/Email',
                id_registro = usuario.id_usuario,
                nome_registro = usuario.username,
            )
            
            flash(f'Perfil atualizado com sucesso!', 'alert-success')
            return redirect(url_for('usuarios', id_usuario=usuario.id_usuario))
    else:
        flash('Você não tem permissão para executar esta ação', 'alert-danger')
        return redirect(url_for('editar_perfil', id_usuario=usuario.id_usuario))
    
    return render_template(
        'usuario/editar_usuario.html',
        form=form,
        title='GRS+Connect',
        usuario=usuario
    )


# ALTERAR SENHA---------------------------------------------------
@app.route('/usuarios/alterar_senha', methods=['GET', 'POST'])
@fresh_login_required
def alterar_senha():
    id_usuario = request.args.get('id_usuario', type=int)
    usuario = Usuario.query.get(id_usuario)

    form = FormAlterarSenha()
    if current_user.id_usuario == id_usuario or current_user.tipo_usuario == 1:
        if form.validate_on_submit():
            # criptografar a senha
            senha = form.senha.data
            senha_cript = bcrypt.generate_password_hash(senha).decode('utf-8')
            usuario.senha = senha_cript

            # gerar novo id cookie aleatorio
            usuario.id_cookie = secrets.token_hex(16)
            usuario.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
            usuario.alterado_por = current_user.username
            database.session.commit()
            
            LogAcoes.registrar_acao(
                nome_tabela = 'Usuario',
                tipo_acao = 'Alteração de Senha',
                id_registro = usuario.id_usuario,
                nome_registro = usuario.username,
            )
            
            flash(f'Senha alterada com sucesso!', 'alert-success')
            return redirect(url_for('usuarios', id_usuario=usuario.id_usuario))
    else:
        flash('Você não tem permissão para executar esta ação', 'alert-danger')
        return redirect(url_for('alterar_senha', id_usuario=usuario.id_usuario))

    return render_template(
        'usuario/editar_senha.html',
        form=form,
        title='GRS+Connect',
        usuario=usuario
    )


# CONFIGS DO USUARIO--------------------------------------------------
@app.route('/usuarios/config', methods=['GET', 'POST'])
@fresh_login_required
@admin_required
def config_usuario():
    id_usuario = request.args.get('id_usuario', type=int)
    usuario = Usuario.query.get(id_usuario)

    form = FormConfigUsuario(
        ativo = usuario.ativo,
        tipo_usuario = usuario.role.id_role
    )

    form.tipo_usuario.choices = (
        [('', 'Selecione')] +
        [(role.id_role, role.nome) for role in TipoUsuario.query.all()]
    )

    if form.validate_on_submit():
        usuario.ativo = form.ativo.data
        usuario.tipo_usuario = form.tipo_usuario.data

        # gerar novo id cookie aleatorio
        usuario.id_cookie = secrets.token_hex(16)

        usuario.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
        usuario.alterado_por = current_user.username

        database.session.commit()

        LogAcoes.registrar_acao(
            nome_tabela = 'Usuario',
            tipo_acao = 'Alteração de Configs usuario',
            id_registro = usuario.id_usuario,
            nome_registro = usuario.username
        )

        flash('Configurações do usuário alteradas com sucesso!', 'alert-success')
        return redirect(url_for('config_usuario', id_usuario=usuario.id_usuario))
    
    return render_template(
        'usuario/configs_usuario.html',
        title='GRS+Connect',
        form=form,
        usuario=usuario
    )


# ALTERAR CHAVE---------------------------------------------------
@app.route('/usuarios/alterar_chave', methods=['GET', 'POST'])
@fresh_login_required
def alterar_chave():
    id_usuario = request.args.get('id_usuario', type=int)
    usuario = Usuario.query.get(id_usuario)

    form = FormAlterarChave()


    if current_user.id_usuario == id_usuario or current_user.tipo_usuario == 1:
        if form.validate_on_submit():
            # criptografar a chave
            chave = form.chave.data
            chave_cript = bcrypt.generate_password_hash(chave).decode('utf-8')
            usuario.chave_api = chave_cript
            
            usuario.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
            usuario.alterado_por = current_user.username
            
            database.session.commit()
            
            LogAcoes.registrar_acao(
                nome_tabela = 'Usuario',
                tipo_acao = 'Alteração de Chave integracao',
                id_registro = usuario.id_usuario,
                nome_registro = usuario.username
            )

            flash(f'Chave de Acesso alterada com sucesso!', 'alert-success')
            return redirect(url_for('usuarios', id_usuario=usuario.id_usuario))
    else:
        flash('Você não tem permissão para executar esta ação', 'alert-danger')
        return redirect(url_for('alterar_chave', id_usuario=usuario.id_usuario))
    
    return render_template(
        'usuario/alterar_chave.html',
        form=form,
        title='GRS+Connect',
        usuario=usuario
    )


# EXCLUIR USUARIO---------------------------------------------------------
@app.route('/usuarios/excluir', methods=['GET', 'POST'])
@fresh_login_required
@admin_required
def excluir_usuario():
    id_usuario = request.args.get('id_usuario', type=int)
    usuario = Usuario.query.get(id_usuario)

    database.session.delete(usuario)
    database.session.commit()

    LogAcoes.registrar_acao(
        nome_tabela = 'Usuario',
        tipo_acao = 'Exclusão',
        id_registro = usuario.id_usuario,
        nome_registro = usuario.username
    )
    
    flash('Usuário excluído!', 'alert-danger')
    return redirect(url_for('usuarios'))



# GRUPOS-----------------------------------------------------------------------
@app.route('/grupos')
@login_required
def grupos():
    lista_grupos = Grupo.query.order_by(Grupo.nome_grupo).all()
    return render_template('grupo/grupos.html', title='GRS+Connect', lista_grupos=lista_grupos)


# GRUPOS CRIAR---------------------------------------------------------------
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


# GRUPOS EDITAR---------------------------------------------------------------
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


# GRUPO EDITAR USUARIOS----------------------------------------------------
@app.route('/grupos/usuarios',  methods=['GET', 'POST'])
@login_required
def grupos_usuarios():
    grupo = Grupo.query.get(request.args.get('id_grupo', type=int))
    
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
        selected = request.form.getlist(key='select', type=int)
        to_include = [i for i in selected if i not in pre_selected]
        to_remove = [i for i in pre_selected if i not in selected]
       
        if to_remove:
            for i in to_remove:
                try:
                    member = Usuario.query.get(i)
                    grupo.usuarios.remove(member)
                    database.session.commit()
                except ValueError:
                    pass
        
        if to_include:
            for i in to_include:
                try:
                    member = Usuario.query.get(i)
                    grupo.usuarios.append(member)
                    database.session.commit()
                except ValueError:
                    pass
        
        grupo.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
        grupo.alterado_por = current_user.username
        database.session.add(grupo)
        database.session.commit()

        # registrar acao
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


# GRUPO EDITAR PRESTADORES----------------------------------------------------
@app.route('/grupos/prestadores',  methods=['GET', 'POST'])
@login_required
def grupos_prestadores():
    grupo = Grupo.query.get(request.args.get('id_grupo', type=int))
    
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
        # reset current group
        delete_query = database.session.execute(
            delete(grupo_prestador).
            where(grupo_prestador.c.id_grupo == grupo.id_grupo)
        )

        # insert all the selected objects
        insert_items = [
            {'id_grupo': grupo.id_grupo, 'id_prestador': i}
            for i in request.form.getlist(key='select', type=int)
        ]
        insert_query = database.session.execute(
            insert(grupo_prestador).
            values(insert_items)
        )

        grupo.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
        grupo.alterado_por = current_user.username
        database.session.commit()

        # registrar acao
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


# GRUPO EDITAR EMPRESAS----------------------------------------------------
@app.route('/grupos/empresas',  methods=['GET', 'POST'])
@login_required
def grupos_empresas():
    grupo = Grupo.query.get(request.args.get('id_grupo', type=int))
    
    #  already in group
    pre_selected = [i.id_empresa for i in grupo.empresas]
    
    # create form with pre selected values
    form = FormGrupoPrestadores(select=pre_selected)
    form.select.choices = [
        (i.id_empresa, i.razao_social)
        for i in Empresa.query.order_by(Empresa.razao_social).all()
    ]
    # sort choices by name, ascending
    form.select.choices.sort(key=lambda tup: tup[1], reverse=False)
    
    if form.validate_on_submit():
        selected = request.form.getlist(key='select', type=int)
        to_include = [i for i in selected if i not in pre_selected]
        to_remove = [i for i in pre_selected if i not in selected]
    
        if to_remove:
            for i in to_remove:
                try:
                    member = Empresa.query.get(i)
                    grupo.empresas.remove(member)
                    database.session.commit()
                except ValueError:
                    pass
    
        if to_include:
            for i in to_include:
                try:
                    member = Empresa.query.get(i)
                    grupo.empresas.append(member)
                    database.session.commit()
                except ValueError:
                    pass

        grupo.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
        grupo.alterado_por = current_user.username
        database.session.add(grupo)
        database.session.commit()

        # registrar acao
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


# GRUPOS GERAR CSV----------------------------------------
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


# GRUPOS EXCLUIR--------------------------------------------------------------------
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


# STATUS-----------------------------------------------
@app.route('/status')
@login_required
def status():
    lista_status = Status.query.all()
    return render_template('status/status.html', title='GRS+Connect', lista_status=lista_status)


# CRIAR STATUS-----------------------------------------------
@app.route('/status/criar', methods=['GET', 'POST'])
@login_required
def criar_status():
    form = FormCriarStatus()

    if form.validate_on_submit():
        status = Status(
            nome_status=form.nome_status.data,
            finaliza_processo=form.finaliza_processo.data,
            data_inclusao=dt.datetime.now(tz=timezone('America/Sao_Paulo')),
            incluido_por=current_user.username
        )

        database.session.add(status)
        database.session.commit()

        LogAcoes.registrar_acao(
            nome_tabela = 'Status',
            tipo_acao = 'Inclusão',
            id_registro = status.id_status,
            nome_registro = status.nome_status,
        )

        flash('Status criado com sucesso!', 'alert-success')
        return redirect(url_for('status'))
    return render_template('status/status_criar.html', title='GRS+Connect', form=form)


# EDITAR STATUS-------------------------------------
@app.route('/status/editar', methods=['GET', 'POST'])
@login_required
def editar_status():
    status: Status = Status.query.get(request.args.get('id_status', type=int))

    # se nao for status padrao
    if not status.status_padrao:
        form = FormCriarStatus(
            nome_status=status.nome_status,
            finaliza_processo=status.finaliza_processo,
            data_inclusao=status.data_inclusao,
            data_alteracao=status.data_alteracao,
            incluido_por=status.incluido_por,
            alterado_por=status.alterado_por
        )

        if form.validate_on_submit():
            status.nome_status = form.nome_status.data
            status.finaliza_processo = form.finaliza_processo.data
            status.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
            status.alterado_por = current_user.username
            database.session.commit()

            # registar acao
            LogAcoes.registrar_acao(
                nome_tabela = 'Status',
                tipo_acao = 'Alteração',
                id_registro = status.id_status,
                nome_registro = status.nome_status
            )

            flash('Status editado com sucesso!', 'alert-success')
            return redirect(url_for('status'))

        return render_template(
            'status/status_editar.html',
            title='GRS+Connect',
            form=form,
            status=status
        )
    else:
        flash(f'O Status "{status.nome_status}" não pode ser editado', 'alert-danger')
        return redirect(url_for('status'))


# EXCLUIR STATUS---------------------------------------------------------------
@app.route('/status/excluir', methods=['GET', 'POST'])
@login_required
@admin_required
def excluir_status():
    status: Status = Status.query.get(request.args.get('id_status', type=int))

    # se nao for status padrao
    if not status.status_padrao:
        try:
            database.session.delete(status)
            database.session.commit()

            LogAcoes.registrar_acao(
                nome_tabela = 'Status',
                tipo_acao = 'Exclusão',
                id_registro = status.id_status,
                nome_registro = status.nome_status,
            )

            flash(f'Status excluído! Status: {status.id_status} - {status.nome_status}', 'alert-danger')
            return redirect(url_for('status'))
        except IntegrityError:
            database.session.rollback()
            flash(f'O Status: {status.id_status} - {status.nome_status} não pode ser excluído, pois há outros registros associados a ele', 'alert-danger')
            return redirect(url_for('status'))
    else:
        flash(f'O Status "{status.nome_status}" não pode ser excluído', 'alert-danger')
        return redirect(url_for('status'))


# LOG ACOES--------------------------------------------------------------------
@app.route('/log_acoes', methods=['GET', 'POST'])
@login_required
@admin_required
def log_acoes():
    form = FormLogAcoes()
    
    form.tabela.choices = (
        [('', 'Selecione')] + (
            LogAcoes.query.with_entities(LogAcoes.tabela, LogAcoes.tabela)
            .order_by(LogAcoes.tabela)
            .distinct()
            .all()
        )
    )
    
    form.usuario.choices = (
        [('', 'Selecione')] + (
            LogAcoes.query.with_entities(LogAcoes.id_usuario, LogAcoes.username)
            .order_by(LogAcoes.username)
            .distinct()
            .all()
        )
    )

    if form.validate_on_submit():
        query = LogAcoes.pesquisar_log(
            inicio=form.data_inicio.data,
            fim=form.data_fim.data,
            usuario=form.usuario.data,
            tabela=form.tabela.data
        )

        df = pd.read_sql(sql=query.statement, con=database.session.bind)
        
        # remover decimais da hora
        df['hora'] = list(map(lambda x: str(x).split('.')[0], df['hora']))
        
        # criar csv dentro da pasta
        nome_arqv = f'Log_acoes_{int(dt.datetime.now().timestamp())}.csv'
        camihno_arqv = f'{UPLOAD_FOLDER}/{nome_arqv}'
        df.to_csv(
            camihno_arqv,
            sep=';',
            index=False,
            encoding='iso-8859-1'
        )
        return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=nome_arqv)
    
    return render_template('log_acoes.html', title='GRS+Connect', form=form)


# MANUAL API-----------------------------------------------------
@app.route('/manual')
@login_required
def manual():
    return render_template('manual.html', title='GRS+Connect')


# LOGOUT-----------------------------------------------------
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.errorhandler(404)
def erro404(erro):
    return render_template(
        'erro.html',
        title='GRS+Connect',
        cod_erro=404,
        titulo_erro='Essa página não existe'
    ), 404


@app.errorhandler(Exception)
def erro500(erro):
    if current_user.is_authenticated:
        return render_template(
            'erro.html',
            title='GRS+Connect',
            cod_erro=500,
            titulo_erro=erro,
            texto_erro=traceback.format_exc()
        ), 500
    else:
        return {"message": "Erro interno"}, 500
