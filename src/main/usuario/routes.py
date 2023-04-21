import datetime as dt
import secrets

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, fresh_login_required, login_required
from pytz import timezone

from src import app, bcrypt, database
from src.main.log_acoes.log_acoes import LogAcoes
from src.main.tipo_usuario.tipo_usuario import TipoUsuario
from src.main.usuario.usuario import Usuario
from src.utils import admin_required

from .forms import (FormAlterarChave, FormAlterarSenha, FormConfigUsuario,
                    FormCriarConta, FormEditarPerfil)


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

@app.route('/usuarios/<int:id_usuario>')
@login_required
def perfil(id_usuario):
    
    usuario = Usuario.query.get(id_usuario)
    
    return render_template(
        'usuario/perfil_usuario.html',
        title='GRS+Connect',
        usuario=usuario
    )

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

