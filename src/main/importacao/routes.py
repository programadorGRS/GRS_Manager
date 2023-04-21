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

from .forms import FormImportarDados


@app.route('/importar_dados/atualizar', methods=['GET', 'POST'])
@login_required
@admin_required
def importar_dados_atualizar():
    form = FormImportarDados()

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

    return render_template('/importar_dados.html', title='GRS+Connect', form=form)
