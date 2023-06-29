from io import StringIO
from sys import getsizeof

import pandas as pd
from flask import flash, redirect, render_template, request, url_for
from flask_login import login_required

from src import app, database
from src.main.empresa.empresa import Empresa
from src.main.exame.exame import Exame
from src.main.unidade.unidade import Unidade
from src.utils import admin_required, tratar_emails

from ..funcionario.funcionario import Funcionario
from ..pedido.pedido import Pedido
from ..processamento.processamento import Processamento
from .forms import FormAtualizarTabela, FormImportarDados


@app.route('/importacao/atualizar-tabelas', methods=['GET', 'POST'])
@login_required
@admin_required
def atualizar_tabelas():
    form = FormAtualizarTabela()

    if form.validate_on_submit():
        # ler arquivo
        arqv = request.files['csv']
        data = arqv.read().decode('iso-8859-1')

        # tamnho maximo
        max_size_mb = app.config['MAX_UPLOAD_SIZE_MB']
        max_bytes = max_size_mb * 1024 * 1024

        if getsizeof(data) > max_bytes:
            flash(f'O arquivo deve ser menor que {max_size_mb} MB', 'alert-danger')
            return redirect(url_for('importar_dados_atualizar'))
        
        else:
            # ler string como objeto para csv
            df = pd.read_csv(
                filepath_or_buffer=StringIO(data),
                sep=';',
                encoding='iso-8859-1',
            )

            tabela = int(form.tabela.data)
            
            match tabela:
                case 1: # Empresa
                    colunas = ['id_empresa', 'emails']
                    if list(df.columns) == colunas:
                        colunas_atualizadas = list(df.columns[1:])
                        df.drop_duplicates(subset='id_empresa', inplace=True, ignore_index=True)
                        if 'emails' in df.columns:
                            df['emails'] = list(map(tratar_emails, df['emails']))
                        df = df.to_dict(orient='records')
                        database.session.bulk_update_mappings(Empresa, df)
                        database.session.commit()
                        flash(f'Empresas atualizadas com sucesso! Linhas: {len(df)}, Colunas: {colunas_atualizadas}', 'alert-success')
                        return redirect(url_for('importar_dados_atualizar'))
                    else:
                        flash('Erro ao validar as Colunas do Arquivo', 'alert-danger')
                        return redirect(url_for('importar_dados_atualizar'))

                case 2: # Unidade
                    colunas = ['id_unidade', 'emails']
                    if list(df.columns) == colunas:
                        colunas_atualizadas = list(df.columns[1:])
                        df.drop_duplicates(subset='id_unidade', inplace=True, ignore_index=True)
                        if 'emails' in df.columns:
                            df['emails'] = list(map(tratar_emails, df['emails']))
                        df = df.to_dict(orient='records')
                        database.session.bulk_update_mappings(Unidade, df)
                        database.session.commit()
                        flash(f'Unidades atualizadas com sucesso! Linhas: {len(df)}, Colunas: {colunas_atualizadas}', 'alert-success')
                        return redirect(url_for('importar_dados_atualizar'))
                    else:
                        flash('Erro ao validar as Colunas do Arquivo', 'alert-danger')
                        return redirect(url_for('importar_dados_atualizar'))

                case 3: # Exame
                    colunas = ['id_exame', 'prazo']
                    if list(df.columns) == colunas:
                        colunas_atualizadas = list(df.columns[1:])
                        df.drop_duplicates(subset='id_exame', inplace=True, ignore_index=True)
                        df = df.to_dict(orient='records')
                        database.session.bulk_update_mappings(Exame, df)
                        database.session.commit()
                        flash(f'Exames atualizados com sucesso! Linhas: {len(df)}, Colunas: {colunas_atualizadas}', 'alert-success')
                        return redirect(url_for('importar_dados_atualizar'))
                    else:
                        flash('Erro ao validar as Colunas do Arquivo', 'alert-danger')
                        return redirect(url_for('importar_dados_atualizar'))

    return render_template('importacao/upload.html', title='GRS+Connect', form=form)

@app.route('/importacao/sincronizar-soc', methods=['GET', 'POST'])
@login_required
def importar_dados():
    form: FormImportarDados = FormImportarDados()
    form.load_choices()

    if form.validate_on_submit():
        tabela = int(form.tabela.data)

        # validar tarefa
        task = Processamento.buscar_tarefas_ativas(tipo=tabela)
        if task:
            flash(
                'Já existe um processo deste tipo \
                em andamento. Tente novamente em alguns \
                minutos.',
                'alert-info'
            )
            return redirect(url_for('importar_dados'))

        match tabela:
            case 1:
                new_task_id = Processamento.nova_tarefa(tipo=1)
                infos = Pedido.carregar_pedidos(
                    id_empresa=int(form.id_empresa.data),
                    dataInicio=form.data_inicio.data,
                    dataFim=form.data_fim.data
                )
            case 2:
                new_task_id = Processamento.nova_tarefa(tipo=2)
                infos = Funcionario.carregar_funcionarios(
                    id_empresa=int(form.id_empresa.data),
                    data_inicio=form.data_inicio.data,
                    data_fim=form.data_fim.data
                )

        if infos.ok:
            flash(
                f'Dados importados com sucesso! \
                Tabela: {infos.tabela} | \
                Inseridos: {infos.qtd_inseridos} | \
                Atualizados: {infos.qtd_atualizados}',
                'alert-success'
            )
            Processamento.concluir_tarefa(id=new_task_id)
        else:
            flash(f'Erro: {infos.erro}','alert-danger')
            Processamento.concluir_tarefa(
                id=new_task_id,
                status=4,
                erro=infos.erro
            )

        return redirect(url_for('importar_dados'))
    return render_template(
        'importacao/carregar.html',
        page_title='Importar Dados SOC',
        form=form
    )

