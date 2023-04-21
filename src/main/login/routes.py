import base64
import datetime as dt
import os

from flask import (abort, current_app, flash, redirect, render_template,
                   request, session, url_for)
from flask_login import (confirm_login, current_user, login_fresh,
                         login_required, login_user, logout_user)
from flask_mail import Attachment, Message
from pytz import timezone

from src import app, bcrypt, database, mail
from src.email_connect import EmailConnect
from src.main.login.login import Login
from src.main.usuario.usuario import Usuario
from src.utils import is_safe_url

from .forms import FormLogin, FormOTP


@app.route('/', methods=['GET', 'POST'])
def login():
    form = FormLogin()
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    elif form.validate_on_submit():
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

            email_body = EmailConnect.create_email_body(
                email_template_path='src/email_templates/otp.html',
                replacements={
                    'USER_NAME': usuario.nome_usuario,
                    'USERNAME': usuario.username,
                    'CURRENT_DATETIME': horario,
                    'USER_OTP': otp
                }
            )
            assinatura = EmailConnect.ASSINATURA_BOT.get('img_path')
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

@app.route('/two_factor', methods=['GET', 'POST'])
def login_otp():
    form = FormOTP()        
    if 'username' in session:
        usuario = Usuario.query.filter_by(username=session['username']).first()
        if usuario:
            if form.validate_on_submit():
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

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))
