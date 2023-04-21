# import base64
# import datetime as dt
# import os
# import secrets
# import traceback

# import pandas as pd
# from flask import (abort, flash, redirect, render_template, request,
#                    send_from_directory, session, url_for)
# from flask_login import (confirm_login, current_user, fresh_login_required,
#                          login_fresh, login_required, login_user, logout_user)
# from flask_mail import Attachment, Message
# from pytz import timezone
# from sqlalchemy.exc import IntegrityError
# from werkzeug.exceptions import HTTPException

# from src import UPLOAD_FOLDER, app, bcrypt, database, mail
# from src.email_connect import EmailConnect
# from src.forms import (FormAlterarChave, FormAlterarSenha, FormConfigUsuario,
#                        FormCriarConta, FormCriarGrupo, FormCriarStatus,
#                        FormEditarPerfil, FormGrupoPrestadores, FormLogAcoes,
#                        FormLogin, FormOTP)
# from src.main.empresa.empresa import Empresa
# from src.main.empresa_socnet.empresa_socnet import EmpresaSOCNET
# from src.main.grupo.grupo import (Grupo, grupo_empresa, grupo_empresa_socnet,
#                                   grupo_prestador, grupo_usuario)
# from src.main.log_acoes.log_acoes import LogAcoes
# from src.main.login.login import Login
# from src.main.prestador.prestador import Prestador
# from src.main.status.status import Status
# from src.main.status.status_rac import StatusRAC
# from src.main.tipo_usuario.tipo_usuario import TipoUsuario
# from src.main.usuario.usuario import Usuario
# from src.utils import admin_required, is_safe_url, zipar_arquivos


# @app.errorhandler(404)
# def erro404(erro):
#     return render_template(
#         'erro.html',
#         title='GRS+Connect',
#         cod_erro=404,
#         titulo_erro='Essa página não existe'
#     ), 404

# @app.errorhandler(Exception)
# def internalExceptions(erro):
#     if current_user.is_authenticated:
#         return render_template(
#             'erro.html',
#             title='GRS+Connect',
#             cod_erro=500,
#             titulo_erro=erro,
#             texto_erro=traceback.format_exc()
#         ), 500
#     else:
#         return {"message": "Internal Server Error"}, 500

# @app.errorhandler(HTTPException)
# def httpExeptions(error: HTTPException):
#     """Return JSON instead of HTML for HTTP errors."""
#     return {"message": error.name}, error.code
