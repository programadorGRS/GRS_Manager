import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configurações do servidor de email (ajuste para o seu provedor)
smtp_server = 'smtp.office365.com'  # Exemplo: smtp.gmail.com
smtp_port = 587  # Porta comum para TLS
email_remetente = 'aso.manager@grsnucleo.com.br'
senha_email = 'Robot-Spammer-Clinton-Driver-Suite-Mountain'

# Conteúdo do email
email_destinatario = 'hideki@quaestum.com.br'
assunto = 'Olá do Python!'
mensagem = MIMEMultipart()
mensagem['From'] = email_remetente
mensagem['To'] = email_destinatario
mensagem['Subject'] = assunto
corpo_email = "Este é um email de teste enviado com Python!"
mensagem.attach(MIMEText(corpo_email, 'plain'))

print('a')
# Conexão com o servidor e envio
with smtplib.SMTP(smtp_server, smtp_port) as server:
    print('Inicio')
    server.starttls()  # Inicia conexão segura
    server.login(email_remetente, senha_email)
    texto = mensagem.as_string()
    server.sendmail(email_remetente, email_destinatario, texto)
