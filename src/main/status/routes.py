import datetime as dt

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from pytz import timezone
from sqlalchemy.exc import IntegrityError

from src import app, database
from src.main.log_acoes.log_acoes import LogAcoes
from src.main.status.status import Status
from src.main.status.status_rac import StatusRAC
from src.utils import admin_required

from .forms import FormCriarStatus


@app.route('/status')
@login_required
def status():
    lista_status = Status.query.all()
    return render_template('status/status.html', title='GRS+Connect', lista_status=lista_status)

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

@app.route('/status_rac')
@login_required
def status_rac():
    lista_status = StatusRAC.query.all()
    return render_template('status/status_rac.html', title='GRS+Connect', lista_status=lista_status)

@app.route('/status_rac/criar', methods=['GET', 'POST'])
@login_required
def criar_status_rac():
    form = FormCriarStatus()

    if form.validate_on_submit():
        status = StatusRAC(
            nome_status=form.nome_status.data,
            data_inclusao=dt.datetime.now(tz=timezone('America/Sao_Paulo')),
            incluido_por=current_user.username
        )

        database.session.add(status)
        database.session.commit()

        LogAcoes.registrar_acao(
            nome_tabela = 'StatusRAC',
            tipo_acao = 'Inclusão',
            id_registro = status.id_status,
            nome_registro = status.nome_status,
        )

        flash('Status RAC criado com sucesso!', 'alert-success')
        return redirect(url_for('status_rac'))
    return render_template('status/status_rac_criar.html', title='GRS+Connect', form=form)

@app.route('/status_rac/editar', methods=['GET', 'POST'])
@login_required
def editar_status_rac():
    status: StatusRAC = StatusRAC.query.get(request.args.get('id_status', type=int))

    # se nao for status padrao
    if not status.status_padrao:
        form = FormCriarStatus(
            nome_status=status.nome_status,
            data_inclusao=status.data_inclusao,
            data_alteracao=status.data_alteracao,
            incluido_por=status.incluido_por,
            alterado_por=status.alterado_por
        )

        if form.validate_on_submit():
            status.nome_status = form.nome_status.data
            status.data_alteracao = dt.datetime.now(tz=timezone('America/Sao_Paulo'))
            status.alterado_por = current_user.username
            database.session.commit()

            # registar acao
            LogAcoes.registrar_acao(
                nome_tabela = 'StatusRAC',
                tipo_acao = 'Alteração',
                id_registro = status.id_status,
                nome_registro = status.nome_status
            )

            flash('Status RAC editado com sucesso!', 'alert-success')
            return redirect(url_for('status_rac'))

        return render_template(
            'status/status_rac_editar.html',
            title='GRS+Connect',
            form=form,
            status=status
        )
    else:
        flash(f'O Status RAC "{status.nome_status}" não pode ser editado', 'alert-danger')
        return redirect(url_for('status_rac'))

@app.route('/status_rac/excluir', methods=['GET', 'POST'])
@login_required
@admin_required
def excluir_status_rac():
    status: StatusRAC = StatusRAC.query.get(request.args.get('id_status', type=int))

    # se nao for status padrao
    if not status.status_padrao:
        try:
            database.session.delete(status)
            database.session.commit()

            LogAcoes.registrar_acao(
                nome_tabela = 'StatusRAC',
                tipo_acao = 'Exclusão',
                id_registro = status.id_status,
                nome_registro = status.nome_status,
            )

            flash(f'Status RAC excluído! Status: {status.id_status} - {status.nome_status}', 'alert-danger')
            return redirect(url_for('status_rac'))
        except IntegrityError:
            database.session.rollback()
            flash(f'O Status RAC: {status.id_status} - {status.nome_status} não pode ser excluído, pois há outros registros associados a ele', 'alert-danger')
            return redirect(url_for('status_rac'))
    else:
        flash(f'O Status RAC"{status.nome_status}" não pode ser excluído', 'alert-danger')
        return redirect(url_for('status_rac'))
