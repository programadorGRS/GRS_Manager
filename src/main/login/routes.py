import base64
import os
from datetime import datetime

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   session, url_for)
from flask_login import (confirm_login, current_user, login_fresh,
                         login_required, login_user, logout_user)
from flask_mail import Attachment, Message
from pytz import timezone

from src import app
from src.email_connect import EmailConnect
from src.extensions import bcrypt, database, limiter, mail
from src.main.client_ip.client_ip import ClientIP
from src.main.login.login import Login
from src.main.usuario.usuario import Usuario
from src.utils import is_safe_url

from .forms import FormLogin, FormOTP

# NOTE: usar o nome user_auth ao invez de login para evitar confitos com flask_login
user_auth = Blueprint(
    name="user_auth",
    import_name=__name__,
    url_prefix="/",
    template_folder="templates",
)


RATE_LIMIT = "5/5 minutes"


@user_auth.route("/", methods=["GET", "POST"])
@limiter.limit(
    limit_value=RATE_LIMIT,
    methods=["POST"],
    exempt_when=ClientIP.is_rate_limit_exempt,
)
def login():
    form = FormLogin()
    if current_user.is_authenticated:  # type: ignore
        return redirect(url_for("home.home"))

    if form.validate_on_submit():
        username = form.username.data
        usuario = Usuario.query.filter_by(username=username).first()

        denied_msg = "Username ou Senha incorretos"

        if not usuario:
            Login.log_attempt(
                username=username,
                tela="login",
                ip=Login.get_ip(),
                obs="Recusado",
            )
            flash(denied_msg, "alert-danger")
            return redirect(url_for("user_auth.login"))

        if not usuario.is_active:
            Login.log_attempt(
                username=username,
                tela="login",
                ip=Login.get_ip(),
                obs="Recusado",
            )
            flash(denied_msg, "alert-danger")
            return redirect(url_for("user_auth.login"))

        pwd_hash = usuario.senha.encode("utf-8")
        pwd_input = form.senha.data
        if bcrypt.check_password_hash(pw_hash=pwd_hash, password=pwd_input):
            '''''
            # gerar otp
            otp = base64.b32encode(os.urandom(10)).decode("utf-8")
            usuario.otp = bcrypt.generate_password_hash(otp).decode("utf-8")
            database.session.commit()  # type: ignore

            # enviar email
            horario = datetime.now(tz=timezone("America/Sao_Paulo")).strftime(
                "%d-%m-%Y %H:%M:%S"
            )

            email_body = EmailConnect.create_email_body(
                email_template_path="src/email_templates/otp.html",
                replacements={
                    "USER_NAME": usuario.nome_usuario,
                    "USERNAME": usuario.username,
                    "CURRENT_DATETIME": horario,
                    "USER_OTP": otp,
                },
            )
            assinatura = EmailConnect.ASSINATURA_BOT.get("img_path")
            anexos = Attachment(
                filename=assinatura,
                content_type="image/png",
                data=app.open_resource(assinatura).read(),  # type: ignore
                disposition="inline",
                headers=[["Content-ID", "<AssEmail>"]],
            )
            msg = Message(
                subject="GRS+Connect - Chave de Acesso",
                recipients=[usuario.email],
                html=email_body,
                attachments=[anexos],
            )
            mail.send(msg)

            Login.log_attempt(
                username=username, tela="login", ip=Login.get_ip(), obs="OK"
            )

            # guardar username na sessao
            session["username"] = username
            flash("A chave temporária foi enviada para o seu email", "alert-info")
            return redirect(url_for("user_auth.login_otp"))
            '''''
            
            #Remover ate o final do return redirect(url_for("home.home")) para habilitar os 2 fatores
            
            # remover username da sessao
            #del session["username"]

            login_user(usuario)

            # registrar tentativa
            Login.log_attempt(
                username=usuario.username,
                tela="login_otp",
                ip=Login.get_ip(),
                obs="OK",
            )

            # atualizar horario do login
            current_user.ultimo_login = datetime.now(tz=timezone("America/Sao_Paulo"))
            database.session.commit()  # type: ignore

            flash(f"Logado com sucesso em: {usuario.username}", "alert-success")
            return redirect(url_for("home.home"))
            
        else:
            Login.log_attempt(
                username=username,
                tela="login",
                ip=Login.get_ip(),
                obs="Recusado",
            )
            flash(denied_msg, "alert-danger")
            return redirect(url_for("user_auth.login"))
    return render_template("login/login.html", form_login=form)


@user_auth.route("/two-factor", methods=["GET", "POST"])
@limiter.limit(
    limit_value=RATE_LIMIT,
    methods=["POST"],
    exempt_when=ClientIP.is_rate_limit_exempt,
)
def login_otp():
    form = FormOTP()

    username = session.get("username")
    if not username:
        return abort(404)

    usuario = Usuario.query.filter_by(username=username).first()
    if not usuario:
        Login.log_attempt(
            username=username,
            tela="login_otp",
            ip=Login.get_ip(),
            obs="Recusado",
        )
        flash("Username ou Senha incorretos", "alert-danger")
        return redirect(url_for("user_auth.login"))

    if form.validate_on_submit():
        otp_hash = usuario.otp.encode("utf-8")
        otp_input = form.otp.data
        if bcrypt.check_password_hash(pw_hash=otp_hash, password=otp_input):
            # remover username da sessao
            del session["username"]

            login_user(usuario)

            # registrar tentativa
            Login.log_attempt(
                username=usuario.username,
                tela="login_otp",
                ip=Login.get_ip(),
                obs="OK",
            )

            # atualizar horario do login
            current_user.ultimo_login = datetime.now(tz=timezone("America/Sao_Paulo"))
            database.session.commit()  # type: ignore

            flash(f"Logado com sucesso em: {usuario.username}", "alert-success")
            return redirect(url_for("home.home"))
        else:
            Login.log_attempt(
                username=usuario.username,
                tela="login_otp",
                ip=Login.get_ip(),
                obs="Recusado",
            )
            flash("Chave inválida", "alert-danger")
    return render_template("login/login_otp.html", form=form, title="GRS+Connect")


@user_auth.route("/refresh-login", methods=["GET", "POST"])
@login_required
def refresh_login():
    form = FormLogin()
    if login_fresh():
        return redirect(url_for("home.home"))

    if form.validate_on_submit():
        username = form.username.data
        usuario = Usuario.query.filter_by(username=username).first()

        if not usuario:
            logout_user()
            Login.log_attempt(
                username=username,
                tela="refresh_login",
                ip=Login.get_ip(),
                obs="Recusado",
            )
            return redirect(url_for("user_auth.login"))

        if not usuario.is_active:
            logout_user()
            Login.log_attempt(
                username=username,
                tela="refresh_login",
                ip=Login.get_ip(),
                obs="Recusado",
            )
            return redirect(url_for("user_auth.login"))

        pw_hash = usuario.senha.encode("utf-8")
        pw_input = form.senha.data
        if bcrypt.check_password_hash(pw_hash=pw_hash, password=pw_input):
            confirm_login()

            Login.log_attempt(
                username=username,
                tela="refresh_login",
                ip=Login.get_ip(),
                obs="OK",
            )

            Usuario.update_ultimo_login()

            # redirecionar
            par_next = request.args.get(key="next", type=str)
            if par_next and is_safe_url(par_next):
                flash(f"Autenticado com sucesso em: {username}", "alert-success")
                return redirect(par_next)
            else:
                return redirect(url_for("home.home"))
        else:
            Login.log_attempt(
                username=username,
                tela="refresh_login",
                ip=Login.get_ip(),
                obs="Recusado",
            )
            flash("Username ou Senha incorretos", "alert-danger")
    return render_template("login.html", form_login=form)


@user_auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("user_auth.login"))
