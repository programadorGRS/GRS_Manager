import datetime as dt
from io import StringIO
from sys import getsizeof

import numpy as np
import pandas as pd
from flask import (flash, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required

from src import TIMEZONE_SAO_PAULO, UPLOAD_FOLDER, app, database
from src.main.empresa.empresa import Empresa
from src.main.unidade.unidade import Unidade
from src.modules.forms import FormConfigRelatoriosAgendados
from src.utils import admin_required, tratar_emails, zipar_arquivos


@app.route('/relatorios_agendados/config', methods=['GET', 'POST'])
@login_required
@admin_required
def config_relatorios_agendados():
    form = FormConfigRelatoriosAgendados()

    if form.validate_on_submit() and 'btn_upload' in request.form:
        # ler arquivo
        arqv = request.files['csv']
        data = arqv.read().decode('iso-8859-1')

        # tamnho maximo
        max_size_mb = app.config['MAX_UPLOAD_SIZE_MB']
        max_bytes = max_size_mb * 1024 * 1024

        if getsizeof(data) > max_bytes:
            flash(f'O arquivo deve ser menor que {max_size_mb} MB', 'alert-danger')
            return redirect(url_for('importar_dados'))
        else:
            # ler string como objeto para csv
            df: pd.DataFrame = pd.read_csv(
                filepath_or_buffer=StringIO(data),
                sep=';',
                encoding='iso-8859-1',
            )

            COLS_EMAIL = [
                'conv_exames_emails',
                'exames_realizados_emails',
                'absenteismo_emails'
            ]

            COLS_BOOL = [
                'conv_exames',
                'exames_realizados',
                'absenteismo',
            ]

            tabela = int(form.tabela.data)
            match tabela:
                case 1: # Empresas
                    tabela = Empresa
                    coluna_chave = 'id_empresa'

                    # checar colunas
                    colunas_erro = ''
                    for col in df.columns:
                        if col not in COLS_BOOL + COLS_EMAIL + [coluna_chave]:
                            colunas_erro = colunas_erro + str(col)
                    if colunas_erro:
                        flash(f'Colunas erradas: {colunas_erro}', 'alert-danger')
                        return redirect(url_for('config_relatorios_agendados'))

                    modelos_query = [
                        (Empresa.id_empresa),
                        (Empresa.razao_social),
                        (Empresa.conv_exames),
                        (Empresa.conv_exames_emails),
                        (Empresa.exames_realizados),
                        (Empresa.exames_realizados_emails),
                        (Empresa.absenteismo),
                        (Empresa.absenteismo_emails)
                    ]

                    filtros = [Empresa.id_empresa.in_(df[coluna_chave].drop_duplicates().astype(int))]

                case 2: # Unidades
                    tabela = Unidade
                    coluna_chave = 'id_unidade'

                    # checar colunas
                    colunas_erro = ''
                    for col in df.columns:
                        if col not in COLS_BOOL + COLS_EMAIL + [coluna_chave]:
                            colunas_erro = colunas_erro + str(col)
                    if colunas_erro:
                        flash(f'Colunas erradas: {colunas_erro}', 'alert-danger')
                        return redirect(url_for('config_relatorios_agendados'))

                    modelos_query = [
                        (Unidade.id_unidade), # inserir nome da empresa
                        (Unidade.nome_unidade),
                        (Unidade.conv_exames),
                        (Unidade.conv_exames_emails),
                        (Unidade.exames_realizados),
                        (Unidade.exames_realizados_emails),
                        (Unidade.absenteismo),
                        (Unidade.absenteismo_emails)
                    ]

                    filtros = [Unidade.id_unidade.in_(df[coluna_chave].drop_duplicates().astype(int))]
            
            # tratar df
            df.drop_duplicates(subset=coluna_chave, ignore_index=True, inplace=True)
            df = df.replace(to_replace={'': None, pd.NA: None, np.nan: None})

            for col in df.columns:
                if 'email' in col:
                    df[col] = list(map(tratar_emails, df[col]))

            df['data_alteracao'] = dt.datetime.now(tz=TIMEZONE_SAO_PAULO)
            df['alterado_por'] = current_user.username
            df = df.to_dict(orient='records')
            if form.celulas_null.data:
                # se celulas null for True, manter as celulas vazias para \
                # que a informacao correspondente seja excluida na tabela da database
                df_final = df
            else:
                # se for False, eliminar as celulas vazias para que a informacao \
                # nao seja apagada na database
                df_final = []
                for dicionario in df:
                    df_final.append({chave: valor for chave, valor in dicionario.items() if valor is not None})

            # backup antes de atualizar
            timestamp = int(dt.datetime.now().timestamp())
            query_backup = (
                database.session.query(*modelos_query)
                .filter(*filtros)
            )
            df_backup = pd.read_sql(query_backup.statement, con=database.session.bind)
            df_backup.to_csv(
                path_or_buf=f'{UPLOAD_FOLDER}/backup_{timestamp}.csv',
                index=False,
                sep=';',
                encoding='iso-8859-1'
            )

            # atualizar
            database.session.bulk_update_mappings(tabela, df_final)
            database.session.commit()

            # gerar report das atualizacoes
            query_alteracoes = (
                database.session.query(*modelos_query)
                .filter(*filtros)
            )
            df_alteracoes = pd.read_sql(query_alteracoes.statement, con=database.session.bind)
            df_alteracoes.to_csv(
                path_or_buf=f'{UPLOAD_FOLDER}/alteracoes_{timestamp}.csv',
                index=False,
                sep=';',
                encoding='iso-8859-1'
            )

            caminho_arquivos = zipar_arquivos(
                caminhos_arquivos=[
                    f'{UPLOAD_FOLDER}/alteracoes_{timestamp}.csv',
                    f'{UPLOAD_FOLDER}/backup_{timestamp}.csv'
                ],
                caminho_pasta_zip=f'{UPLOAD_FOLDER}/report_{timestamp}.zip'
            ).split('/')[-1]
            

            return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename=caminho_arquivos)

    return render_template('configs_relatorios_agendados.html', title='GRS+Connect', form=form)


@app.route('/relatorios_agendados/modelo_empresas', methods=['GET', 'POST'])
@login_required
@admin_required
def relatorios_agendados_modelo_empresas():
    colunas = [
        'id_empresa',
        'conv_exames',
        'conv_exames_emails',
        'exames_realizados',
        'exames_realizados_emails',
        'absenteismo',
        'absenteismo_emails'
    ]

    df = pd.DataFrame(columns=colunas)

    # criar arquivo dentro da pasta
    df.to_csv(
        f'{UPLOAD_FOLDER}/Relatorios_Agendados_Empresas.csv',
        sep=';',
        index=False,
        encoding='iso-8859-1'
    )
    return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename='Relatorios_Agendados_Empresas.csv')


@app.route('/relatorios_agendados/modelo_unidades', methods=['GET', 'POST'])
@login_required
@admin_required
def relatorios_agendados_modelo_unidades():
    colunas = [
        'id_unidade',
        'conv_exames',
        'conv_exames_emails',
        'exames_realizados',
        'exames_realizados_emails',
        'absenteismo',
        'absenteismo_emails'
    ]

    df = pd.DataFrame(columns=colunas)

    # criar arquivo dentro da pasta
    df.to_csv(
        f'{UPLOAD_FOLDER}/Relatorios_Agendados_Unidades.csv',
        sep=';',
        index=False,
        encoding='iso-8859-1'
    )
    return send_from_directory(directory=UPLOAD_FOLDER, path='/', filename='Relatorios_Agendados_Unidades.csv')

