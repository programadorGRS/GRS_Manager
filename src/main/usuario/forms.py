from flask import request
from flask_wtf import FlaskForm
from wtforms import (BooleanField, PasswordField, SelectField, StringField,
                     SubmitField, TelField)
from wtforms.validators import (DataRequired, Email, EqualTo, Length, Optional,
                                ValidationError)

from .usuario import Usuario


class FormCriarConta(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(3, 50)])
    nome_usuario = StringField('Nome do Usuário', validators=[DataRequired(), Length(3, 100)])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    tel = TelField('Telefone (Opcional)', validators=[Optional(), Length(0, 20)], render_kw={'placeholder': '(11) 3741-9977'})
    cel = TelField('Celular (Opcional)', validators=[Optional(), Length(0, 20)], render_kw={'placeholder': '(11) 93741-9977'})
    senha = PasswordField('Senha', validators=[DataRequired(), Length(6, 50)])
    confirmacao_senha = PasswordField('Confirmação da Senha', validators=[DataRequired(), EqualTo('senha')])
    tipo_usuario = SelectField('Tipo de usuário', validators=[DataRequired()])
    botao_criarconta = SubmitField('Criar Conta')

    def validate_username(self, username):
        usuario = Usuario.query.filter_by(username=username.data).first()
        if usuario:
            raise ValidationError('Esse username já foi cadastrado')

    def validate_email(self, email):
        usuario = Usuario.query.filter_by(email=email.data).first()
        if usuario:
            raise ValidationError('Esse email já foi cadastrado')

    def validate_tel(self, tel):
        if tel.data:
            if not tel.data.isnumeric():
                raise ValidationError('Apenas dígitos')
    
    def validate_cel(self, cel):
        if cel.data:
            if not cel.data.isnumeric():
                raise ValidationError('Apenas dígitos')


class FormEditarPerfil(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(3, 50)])
    nome_usuario = StringField('Nome do Usuário', validators=[DataRequired(), Length(3, 50)])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    tel = TelField('Telefone (Opcional)', validators=[Optional(), Length(0, 20)], render_kw={'placeholder': '(11) 3741-9977'})
    cel = TelField('Celular (Opcional)', validators=[Optional(), Length(0, 20)], render_kw={'placeholder': '(11) 93741-9977'})
    botao_salvar = SubmitField('Salvar')

    def validate_email(self, email):
        usuario = Usuario.query.get(request.args.get('id_usuario', type=int))
        
        if usuario.email != email.data:
            dono_do_email = Usuario.query.filter_by(email=email.data).first()
            if dono_do_email:
                raise ValidationError('Esse email já está sendo usado')

    def validate_username(self, username):
        usuario = Usuario.query.get(request.args.get('id_usuario', type=int))

        if usuario.username != username.data:
            dono_do_username = Usuario.query.filter_by(username=username.data).first()
            if dono_do_username:
                raise ValidationError('Esse username já está sendo usado')

    def validate_tel(self, tel):
        FormCriarConta.validate_tel(self, tel)

    def validate_cel(self, cel):
        FormCriarConta.validate_cel(self, cel)


class FormAlterarSenha(FlaskForm):
    senha = PasswordField('Senha', validators=[DataRequired(), Length(6, 50)])
    confirmacao_senha = PasswordField('Confirmação da Senha', validators=[DataRequired(), EqualTo('senha')])
    botao_salvar = SubmitField('Salvar')


class FormConfigUsuario(FlaskForm):
    ativo = BooleanField('Usuário Ativo')
    tipo_usuario = SelectField('Tipo de Usuário', choices=[], validators=[DataRequired()])
    botao_salvar = SubmitField('Salvar')


class FormAlterarChave(FlaskForm):
    chave = PasswordField('Chave de Integração', validators=[DataRequired(), Length(6, 50)])
    confirmacao_chave = PasswordField('Confirmação da Chave', validators=[DataRequired(), EqualTo('chave')])
    botao_salvar = SubmitField('Salvar')

