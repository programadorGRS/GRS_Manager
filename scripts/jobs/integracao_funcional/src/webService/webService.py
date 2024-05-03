# -*- coding: latin-1 -*-

from zeep import Client
from zeep.wsse import UsernameToken
from zeep.transports import Transport
import requests
from zeep.plugins import HistoryPlugin
from lxml import etree as ET
import logging
import json
from datetime import datetime, timedelta
import re
import pandas as pd
import requests
import xmltodict
import zeep
from zeep.settings import Settings
from zeep.wsse.username import UsernameToken
from zeep.wsse.utils import WSU

wsdl_url = 'https://ws1.soc.com.br/WSSoc/FuncionarioModelo2Ws?wsdl'
username = 'U1797850'
password = '78e94c8abc025bc1eca3650c3e688784840b19a2'

session = requests.Session()
timestamp_token1 = WSU.Timestamp()
        # usar horario UTC-0
today_datetime = datetime.utcnow()
expires_datetime = today_datetime + timedelta(minutes=10)
timestamp_elements = [
    WSU.Created(today_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")),
    WSU.Expires(expires_datetime.strftime("%Y-%m-%dT%H:%M:%SZ"))
]
timestamp_token1.extend(timestamp_elements)

username_token = UsernameToken(
    username=username,
    password=password,
    use_digest=True,
    timestamp_token=timestamp_token1
) 
conf = Settings(raw_response=True)
history = HistoryPlugin()

client = zeep.Client(
    wsdl=wsdl_url,
    wsse=username_token,
    settings=conf, 
    plugins=[history]
)

# Access a service method from the client
# Replace 'YourServiceMethod' with the actual method you want to call
# and provide the necessary parameters

factory = client.type_factory(namespace='ns0')
response = client.service._operations
print(response)





identificacao = factory.identificacaoUsuarioWsVo(
    codigoEmpresaPrincipal=423,
    codigoResponsavel=213,
    codigoUsuario=1797850,
    homologacao=False
)


# Funaao para separar as colunas por regex com ;
def separar_colunas(texto):
    # Define o padrao regex para separar as colunas
    padrao = re.compile(r'\s*;\s*')
    # Usa o padrao para separar as colunas
    colunas = padrao.split(texto.strip())
    return colunas

# Funaao para ler o arquivo e separar as colunas
def ler_arquivo(nome_arquivo):
    linhas = []
    with open(nome_arquivo, 'r',  encoding='iso8859-1') as arquivo:
        linhas = arquivo.readlines()[1:]
    return linhas
        



funcionarioCentroCustoWsVo = factory.funcionarioCentroCustoWsVo(
    #codigo='000000001',
    #codigoRh='0',
    #nome='a',
    #tipoBusca='CODIGO'
)

atividadesPerigosasWsVo = factory.atividadesPerigosasWsVo(
    #codigoAtividadePerigosa=''
)

funcionarioCargoWsVo = factory.funcionarioCargoWsVo(
    atualizaDescricaoRequisitosCargoPeloCbo=False,
    #cbo='a',
    #codigo='00001',
    #codigoRh='00001',
    #descricaoDetalhada='a',
    #descricaoLocal='a',
    #educacao='a',
    #experiencia='a',
    #funcao='a',
    #gfip=0,
    #habilidades='a',
    #localTrabalho='a',
    #materialUtilizado='a',
    #mobiliarioUtilizado='a',
    #nome='TESTE CARGO GRS',
    #nomeLegal='a',
    #orientacaoAso='a',
    #requisitosFuncao='a',
    #status='ATIVO',
    #tipoBusca='CODIGO',
    #treinamento='a',
    atividadesPerigosasWsVo=atividadesPerigosasWsVo,
    criarHistoricoDescricao=False
)

funcionarioClassificacaoDeficienciaWsVo = factory.funcionarioClassificacaoDeficienciaWsVo(
    #classificacao='DEFICIENCIA_FISICA',
    #codigo='a',
    #nome='a',
    #tipoBusca='CODIGO',
)

deficienciaWsVo = factory.deficienciaWsVo(
    #cids='a',
    #classificacaoDeficiencia=funcionarioClassificacaoDeficienciaWsVo,
    #codigoLegislacaoReferencia='a',
    #codigoMedico='a',
    #dataEmissaoLaudo='a',
    #deficiencia='a',
    #deficiente=False,
    #gravarHistorico=False,
    #nomeLegislacaoReferencia='a',
    #observacao='a',
    #origemDeficiencia='EM_BRANCO',
    #parecerLaudo='EM_BRANCO',
    #reabilitado=False,
    #tipoBuscaLegislacaoReferencia='CODIGO',
    #dataReabilitacao=''
)

funcionarioWsVo = factory.funcionarioWsVo(
    #autorizadoMensagemSms=False,
    #bairro='a',
    #carteiraNacionalSaude='a',
    #categoria='EM_BRANCO',
    #cep='a',
    #chaveProcuraFuncionario='CPF',
    #cidade='a',
    #cipa='EM_BRANCO',
    #cipaDataFimMandato='a',
    #cipaDataInicioMandato='a',
    #cnpjEmpresaFuncionario='a',
    #codigo='a',
    #codigoEmpresa='423',
    #codigoMunicipio='a',
    #complementoEndereco='a',
    #contatoEmergencia='a',
    #cor='EM_BRANCO',
    #cpf='00000000000',
    #dataAdmissao='01/02/2003',
    #dataAfastamento='a',
    #dataDemissao='a',
    #dataDemissionalCarta='a',
    #dataEmissaoCtps='a',
    #dataFinalEstabilidade='a',
    #dataNascimento='01/02/1996',
    #dataUltimaMovimentacao='a',
    #desabilitarRisco=False,
    #descricaoAtividade='a',
    #email='a',
    #endereco='a',
    #enderecoEmergencia='a',
    #escolaridade='EM_BRANCO',
    #estado='SP',
    #estadoCivil='SOLTEIRO',
    #funcao='a',
    #funcaoBrigadaIncendio='EM_BRANCO',
    #gfip=0,
    #historicoPPP='NAO_EXIBIR',
    #matricula='a',
    #naoPossuiCpf=False,
    #naoPossuiCtps=False,
    #naoPossuiMatricula=False,
    #naoPossuiMatriculaRh=False,
    #naoPossuiPis=False,
    #naturalidade=False,
    #nomeCooperativa='a',
    #nomeFuncionario='Teste GRS',
    #nomeMae='a',
    #nrCtps='a',
    #numeroEndereco='a',
    #observacaoAso='a',
    #observacaoEstabilidade='a',
    #observacaoPpp='a',
    #parentescoContatoEmergencia='a',
    #pis='a',
    #ramal='a',
    #ramalTelefoneEmergencia='a',
    #razaoSocialEmpresaFuncionario='a',
    #regimeRevezamento='a',
    #regimeTrabalho='NORMAL',
    #remuneracaoMensal=0,
    #requisitosFuncao='a',
    #rg='a',
    #rgDataEmissao='a',
    #rgOrgaoEmissor='a',
    #rgUf='SP',
    #serieCtps='a',
    #sexo='MASCULINO',
    #situacao='ATIVO',
    #telefoneCelular='a',
    #telefoneComercial='a',
    #telefoneEmergencia='a',
    #telefoneResidencial='a',
    #telefoneSms='a',
    #tipoBuscaEmpresa='CODIGO_SOC',
    #tipoContratacao='CLT',
    #ufCtps='SP',
    #utilizarDescricaoRequisitoCargo=False,
    #observacaoFuncionario='a',
    #codigoPaisNascimento='a',
    #emailPessoal='a',
    #matriculaRh='a',
    #codigoCategoriaESocial=0,
    #genero='EM_BRANCO',
    #nomeSocial='Teste GRS',
    #tipoVinculo='EM_BRANCO',
    #tipoAdmissao='ADMISSAO',
    #nomePai='a',
    atividadesPerigosasWsVo=atividadesPerigosasWsVo,
    #tipoSanguineo='NENHUM',
    #corDosOlhos='EM_BRANCO',
    #grauInstrucao='EM_BRANCO',
    #cns="",
    #dataInicioPeriodoAquisitivo='a',
    #dataFimPeriodoAquisitivo='a',
    #codigoRh='a',
    #desconsiderarEsocial=False,
    #codigoGenero='a',
    #dataValidadeRg=''
    campoInteiro01 ='',
    campoInteiro02 ='',
    campoInteiro03 ='',
    campoInteiro04 ='',
    campoInteiro05 ='',
    campoInteiro06 ='',
    campoInteiro07 ='',
    campoInteiro08 ='',
    campoInteiro09 ='',
    campoInteiro10 =''
)

motivoLicencaWsVo = factory.motivoLicencaWsVo(
    #codigo = 'a',
    #codigoDeIntegracao = 'a',
    #nome = 'a',
    #tipoBusca = 'CODIGO',
    #campoString01 = ''
)

setorWsVo = factory.setorWsVo(
    #codigo='a',
    #codigoRh='a',
    #descricao='a',
    #nome='a',
    #observacaoAso='a',
    #status='ATIVO',
    #tipoBusca='CODIGO',
    criarHistoricoDescricao=False
)

funcionarioTurnoWsVo = factory.funcionarioTurnoWsVo(
    #cargaHorariaSemanal='a',
    #codigo='a',
    #nome='a',
    #tipoBusca = 'CODIGO',
    #codigoRh=''
)

tiposFichaClinicaWsVo=factory.tiposFichaClinicaWsVo(
    acidente=False,
    admissional=False,
    avaliacaoFisica=False,
    checkup=False,
    consulta=False,
    consultaAssist=False,
    demissional=False,
    enfermagem=False,
    especial=False,
    licencaMedica=False,
    mudancaFuncao=False,
    periodico=False,
    qualidadeVida=False,
    retornoConsulta=False,
    retornoTrabalho=False,
    terceiros=False
)

transferencia = factory.transferencia(
    copiaFichaClinica=False,
    tipoFichaCopia = tiposFichaClinicaWsVo,
    copiaSocGed=False,
    valorizarExamesNaoCobradoNoDestino=False,
    #dataTransferencia='a',
    copiaHistoricoLaboral=False,
    esocial=False,
    copiaCadastroMedico=False,
    copiaHistoricoVacinas=False
)

funcionarioUnidadeWsVo = factory.funcionarioUnidadeWsVo(
    #bairro='a',
    #bairroCobranca='a',
    #cep='a',
    #cepCobranca='a',
    #cidade='a',
    #cidadeCobranca='a',
    #cnpj_cei='CNPJ',
    #codigo='1',
    #codigoArquivo='a',
    #codigoCnae='a',
    #codigoCnpjCei='a',
    #codigoMunicipio='a',
    #codigoMunicipioCobranca='a',
    #codigoRh='a',
    #complemento='a',
    #complementoCobranca='a',
    #dataAssinaturaContrato='a',
    #descricaoCnae='a',
    #endereco='a',
    #enderecoCobranca='a',
    #estado='a',
    #estadoCobranca='a',
    #grauRisco=0,
    #inscricaoEstadual='a',
    #inscricaoMunicipal='a',
    #nome='a',
    #numero='a',
    #numeroCobranca='a',
    #observacaoASO='a',
    #observacaoContrato='a',
    #observacaoPPP='a',
    #percentualCalculoBrigada='a',
    #razaoSocial='a',
    #status='ATIVO',
    #telefoneCat='a',
    #tipoBusca='NOME',
    #tipoCnae='CNAE',
    #unidadeContratante=False,
    #codigoCpf='a',
    #codigoCaepf='a',
    #caracterizacaoProcessosAmbientesTrabalho='a',
    #codigoCno=''
)














try:
    funcionario = factory.Funcionario(    
        atualizarCargo=False,
        atualizarCentroCusto=False,
        atualizarFuncionario=False,
        atualizarMotivoLicenca=False,
        atualizarSetor=False,
        atualizarTurno=False,
        atualizarUnidade=False,
        cargoWsVo=funcionarioCargoWsVo,
        centroCustoWsVo=funcionarioCentroCustoWsVo,
        criarCargo=False,
        criarCentroCusto=True,
        criarFuncionario=True,
        criarHistorico=False,
        criarMotivoLicenca=False,
        criarSetor=False,
        criarTurno=False,
        criarUnidade=False,
        criarUnidadeContratante=False,
        deficienciaWsVo=deficienciaWsVo,
        destravarFuncionarioBloqueado=False,
        funcionarioWsVo=funcionarioWsVo,
        #motivoLicencaWsVo=motivoLicencaWsVo,
        naoImportarFuncionarioSemHierarquia=False,
        setorWsVo=setorWsVo,
        #turnoWsVo=funcionarioTurnoWsVo,
        unidadeContratanteWsVo=funcionarioUnidadeWsVo,
        unidadeWsVo=funcionarioUnidadeWsVo,
        transferirFuncionario=False,
        
        #transferencia=transferencia
        identificacaoWsVo=identificacao
    
)
    print('OK1')
except RuntimeError as error:
        print(error)
        print("The linux_interaction() function wasn't executed.")






















if __name__== "__main__":
    try:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger('zeep').setLevel(logging.DEBUG)
        logging.getLogger('zeep.transports').setLevel(logging.DEBUG)
        print('Inicio do Programa')
        # Chamada da funaao para ler o arquivo
        nome_do_arquivo = 'C:\GitHub\GRS_Manager\Modelo1_Torrent_04042024_232423.txt'
        linhas = ler_arquivo(nome_do_arquivo)
        for linha in linhas:
            colunas = separar_colunas(linha)
            print(colunas)  # Aqui voca pode manipular ou processar as colunas conforme necessario
            
            ''' COLUNAS DO ARQUIVO TXT

            Cod_unid;Nome_unidade;Cod_setor;Nome_setor;Cod_cargo;
            Nome_cargo;Matricula;Cod_funcionario;Nome_funcionario;Dt_nascimento;
            Sexo;Situacao;Dt_admissao;Dt_demissao;Estado_civil;
            Pis_pasep;Contratacao;Rg;Uf_rg;Cpf;
            Cpts;Endereco;Bairro;Cidade;Uf;
            Cep;Tel;Naturalidade;Cor;Email;
            Deficiencia;Cbo;Gfip;Endereco_unidade;Bairro_unidade;
            Cidade_unidade;Estado_unidade;Cep_unidade;Cnpj;Inscricao_unidade;
            Tel1_unidade;Tel2_unidade;Tel3_unidade;Tel4_unidade;Contato_unidade;
            Cnae;Numero_endereco_funcionario;Complemento_endereco_funcionario;Razao_social;Nome_mae_funcionario;
            Centro_custo;Dt_ultima_movimentacao;Cod_unidade_contratante;Razao_social_1;Cnpj_1;
            Turno;Dt_emissao_cart_porf;Serie_cpts;Cnae_2;Cnae_livre;
            Desc_cnae_livre;Cei;Funcao;Cnae_7;Tipo_cnae_utilizado;
            Descricao_detalhada_cargo;Numero_end_unidade;Complemento_end_unidade;Regime_revezamento;Org_exp_rg;
            Campo_livre1;Campo_livre2;Campo_livre3;Telefone_sms;Grau_riscos;
            Uf_cpts;Nome_centro_custo;Autorizacao_sms;Endereco_cobranca_unidade;Numero_cobranca_unidade;
            Bairro_cobranca_unidade;Cidade_cobranca_unidade;Uf_cobranca_unidade;Cep_cobranca_unidade;Complemento_cobranca_unidade;
            Remuneracao_mensal;Telefone_comercial;Telefone_celular;Data_emissao_rg;Codigo_pais_nascimento;
            Origem_desc_detalhada;Unidade_contratante;Escolaridade;Codigo_categoria_esocial;Matricula_rh;
            Genero;Nome_social;Tipo_admissao;Grau_instrucao;Nome_pai;
            Tipo_vinculo;Nome_turno;Campo_livre;Cpf_unidade;Caepf_unidade;
            Tipo_sanguineo;Data_inicio_aquisitivo;Data_fim_aquisitivo;
            
            '''
            funcionarioWsVo.tipoBuscaEmpresa='CODIGO_SOC'
            funcionarioWsVo.codigoEmpresa='562255' #Codigo da EMpresa TORRENT
            funcionarioWsVo.chaveProcuraFuncionario='CPF'
            funcionarioWsVo.cpf='96362137043' #colunas[19].replace('.', '').replace('-', '') #colunas[19]
            funcionarioWsVo.nomeFuncionario=colunas[8]
            funcionarioWsVo.matricula=colunas[6]
            funcionarioWsVo.rg='362260539' #colunas[17]            
            if colunas[16]=='01': funcionarioWsVo.tipoContratacao='CLT'
            elif colunas[16]=='02': funcionarioWsVo.tipoContratacao='COOPERADO'
            elif colunas[16]=='03': funcionarioWsVo.tipoContratacao='TERCERIZADO'
            elif colunas[16]=='04': funcionarioWsVo.tipoContratacao='AUTONOMO'
            elif colunas[16]=='05': funcionarioWsVo.tipoContratacao='TEMPORARIO'
            elif colunas[16]=='06': funcionarioWsVo.tipoContratacao='PESSOA_JURIDICA'
            elif colunas[16]=='07': funcionarioWsVo.tipoContratacao='ESTAGIARIO'
            elif colunas[16]=='08': funcionarioWsVo.tipoContratacao='MENOR_APRENDIZ'
            elif colunas[16]=='09': funcionarioWsVo.tipoContratacao='ESTATUTARIO'
            elif colunas[16]=='10': funcionarioWsVo.tipoContratacao='COMISSIONADO_INTERNO'
            elif colunas[16]=='11': funcionarioWsVo.tipoContratacao='COMISSIONADO_EXTERNO'
            elif colunas[16]=='12': funcionarioWsVo.tipoContratacao='APOSENTADO'
            elif colunas[16]=='13': funcionarioWsVo.tipoContratacao='APOSENTADO_INATIVO_PREFEITURA'
            elif colunas[16]=='14': funcionarioWsVo.tipoContratacao='PENSIONISTA'
            elif colunas[16]=='15': funcionarioWsVo.tipoContratacao='SERVIDOR_PUBLICO_EFETIVO'
            elif colunas[16]=='16': funcionarioWsVo.tipoContratacao='EXTRANUMERARIO'
            elif colunas[16]=='17': funcionarioWsVo.tipoContratacao='AUTARQUICO'
            elif colunas[16]=='18': funcionarioWsVo.tipoContratacao='INATIVO'
            elif colunas[16]=='19': funcionarioWsVo.tipoContratacao='TITULO_PRECARIO'
            elif colunas[16]=='20': funcionarioWsVo.tipoContratacao='SERVIDOR_ADM_CENTRALIZADA_OU_DESCENTRALIZADA'
            funcionarioWsVo.regimeTrabalho='NORMAL'            
            if colunas[13]=='M': funcionarioWsVo.sexo='MASCULINO'
            else: funcionarioWsVo.sexo='FEMININO'
            funcionarioWsVo.estadoCivil='SOLTEIRO'
            funcionarioWsVo.dataNascimento=colunas[9]
            funcionarioWsVo.dataAdmissao=colunas[12]

            if colunas[0] == 1: funcionarioUnidadeWsVo.codigo='002'
            else: funcionarioUnidadeWsVo.codigo='001'
            funcionarioUnidadeWsVo.tipoBusca='CODIGO'
            funcionarioUnidadeWsVo.nome=colunas[1]
            funcionarioUnidadeWsVo.dataAssinaturaContrato = colunas[12]

            setorWsVo.tipoBusca='CODIGO_RH'
            setorWsVo.codigoRh=colunas[2]
            setorWsVo.nome=colunas[3]

            funcionarioCargoWsVo.tipoBusca='NOME'
            funcionarioCargoWsVo.codigo=colunas[4]
            funcionarioCargoWsVo.nome=colunas[5]

            funcionarioCentroCustoWsVo.tipoBusca='CODIGO_RH'
            funcionarioCentroCustoWsVo.codigoRh=colunas[50]
            funcionarioCentroCustoWsVo.nome=colunas[76]

            client.service.importacaoFuncionario(Funcionario=funcionario)
            break
    except RuntimeError as error:
        print(error)
        print("The linux_interaction() function wasn't executed.")