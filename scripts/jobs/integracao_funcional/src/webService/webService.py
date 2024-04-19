from zeep import Client
from zeep.wsse import UsernameToken
from zeep.transports import Transport
import requests


import json
from datetime import datetime, timedelta

import pandas as pd
import requests
import xmltodict
import zeep
from zeep.settings import Settings
from zeep.wsse.username import UsernameToken
from zeep.wsse.utils import WSU

wsdl_url = 'https://ws1.soc.com.br/WSSoc/FuncionarioModelo2Ws?wsdl'
username = 'your_username'
password = 'your_password'

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

client = zeep.Client(
    wsdl=wsdl_url,
    wsse=username_token,
    settings=conf
)

# Access a service method from the client
# Replace 'YourServiceMethod' with the actual method you want to call
# and provide the necessary parameters

factory = client.type_factory(namespace='ns0')

identificacao = factory.identificacaoUsuarioWsVo(
    codigoEmpresaPrincipal=423,
    codigoResponsavel=213,
    codigoUsuario=1797850
)
'''
<xs:simpleType name="situacao">
    <xs:enumeration value="ATIVO"/>
    <xs:enumeration value="INATIVO"/>
</xs:simpleType>

<xs:simpleType name="tipoBuscaCargoEnum">
    <xs:enumeration value="CODIGO"/>
    <xs:enumeration value="CODIGO_RH"/>
    <xs:enumeration value="NOME"/>
</xs:simpleType>

<xs:simpleType name="tipoBuscaCentroCustoEnum">
    <xs:enumeration value="CODIGO"/>
    <xs:enumeration value="CODIGO_RH"/>
    <xs:enumeration value="NOME"/>
</xs:simpleType>

<xs:simpleType name="classificacaoDeficienciaEnum">
    <xs:enumeration value="DEFICIENCIA_FISICA"/>
    <xs:enumeration value="DEFICIENCIA_AUDITIVA"/>
    <xs:enumeration value="DEFICIENCIA_VISUAL"/>
    <xs:enumeration value="DEFICIENCIA_MENTAL"/>
    <xs:enumeration value="DEFICIENCIA_MULTIPLA"/>
    <xs:enumeration value="REABILITACAO"/>
    <xs:enumeration value="DEFICIENCIA_INTELECTUAL"/>
</xs:simpleType>

<xs:simpleType name="tipoBuscaEnum">
    <xs:enumeration value="CODIGO"/>
    <xs:enumeration value="NOME"/>
</xs:simpleType>

<xs:simpleType name="situacao">
    <xs:enumeration value="ATIVO"/>
    <xs:enumeration value="INATIVO"/>
</xs:simpleType>

<xs:simpleType name="origemDeficienciaEnum">
    <xs:enumeration value="EM_BRANCO"/>
    <xs:enumeration value="ACIDENTE_DE_TRABALHO"/>
    <xs:enumeration value="CONGENITA"/>
    <xs:enumeration value="ACIDENTE_COMUM"/>
    <xs:enumeration value="DOENCA"/>
    <xs:enumeration value="ADQUIRIDA_EM_POS_OPERATORIO"/>
    <xs:enumeration value="DESCONHECIDA"/>
    <xs:enumeration value="OUTRAS"/>
</xs:simpleType>

<xs:simpleType name="parecerLaudoEnum">
    <xs:enumeration value="EM_BRANCO"/>
    <xs:enumeration value="APTO_PARA_FUNCAO"/>
    <xs:enumeration value="INAPTO_PARA_FUNCAO"/>
</xs:simpleType>

<xs:simpleType name="origemDeficienciaEnum">
    <xs:enumeration value="EM_BRANCO"/>
    <xs:enumeration value="ACIDENTE_DE_TRABALHO"/>
    <xs:enumeration value="CONGENITA"/>
    <xs:enumeration value="ACIDENTE_COMUM"/>
    <xs:enumeration value="DOENCA"/>
    <xs:enumeration value="ADQUIRIDA_EM_POS_OPERATORIO"/>
    <xs:enumeration value="DESCONHECIDA"/>
    <xs:enumeration value="OUTRAS"/>
</xs:simpleType>

<xs:simpleType name="tipoCategoriaEnum">
    <xs:enumeration value="EM_BRANCO"/>
    <xs:enumeration value="CONTRIB_INDIVIDUAL_AUTONOMO_CONTRATADO_EMPRESAS_GERAL"/>
    <xs:enumeration value="CONTRIB_INDIVIDUAL_AUTONOMO_CONTRATADO_CONTRIB_INDIVIDUAL_PESSOA_FISICA_OU_MISSAO_DIPLOMATICA_E_REPARTICAO_CONSULAR_ESTRANGEIRAS"/>
    <xs:enumeration value="CONTRIB_INDIVIDUAL_AUTONOMO_CONTRATADO_ENTIDADE_BENEFICENTE_ISENTA_COTA_PATRONAL"/>
    <xs:enumeration value="EXCLUIDO"/>
    <xs:enumeration value="CONTRIB_INDIVIDUAL_TRANSPORTADOR_AUTONOMO_CONTRATADO_EMPRESAS_GERAL"/>
    <xs:enumeration value="CONTRIB_INDIVIDUAL_TRANSPORTADOR_AUTONOMO_CONTRATADO_CONTRIB_INDIVIDUAL_PESSOA_FISICA_OU_MISSAO_DIPLOMATICA_E_REPARTICAO_CONSULAR_ESTRANGEIRAS"/>
    <xs:enumeration value="CONTRIB_INDIVIDUAL_TRANSPORTADOR_AUTONOMO_CONTRATADO_ENTIDADE_BENEFICENTE_ISENTA_COTA_PATRONAL"/>
</xs:simpleType>

<xs:simpleType name="chaveProcura">
    <xs:enumeration value="CODIGO"/>
    <xs:enumeration value="MATRICULA"/>
    <xs:enumeration value="MATRICULA_RH"/>
    <xs:enumeration value="CPF"/>
    <xs:enumeration value="DATA_NASCIMENTO"/>
    <xs:enumeration value="CPF_PENDENTE"/>
    <xs:enumeration value="CPF_ATIVO"/>
    <xs:enumeration value="CPF_DATA_ADMISSAO"/>
    <xs:enumeration value="CPF_DATA_ADMISSAO_PERIODO"/>
    <xs:enumeration value="CODIGO_RH"/>
</xs:simpleType>

<xs:simpleType name="tipoCipaEnum">
    <xs:enumeration value="EM_BRANCO"/>
    <xs:enumeration value="EFETIVO"/>
    <xs:enumeration value="SUPLENTE"/>
    <xs:enumeration value="RESPONSAVEL"/>
</xs:simpleType>

<xs:simpleType name="corEnum">
    <xs:enumeration value="EM_BRANCO"/>
    <xs:enumeration value="BRANCO"/>
    <xs:enumeration value="NEGRO"/>
    <xs:enumeration value="AMARELO"/>
    <xs:enumeration value="PARDO"/>
    <xs:enumeration value="INDIGENA"/>
    <xs:enumeration value="MULATO"/>
</xs:simpleType>

<xs:simpleType name="tipoEscolaridadeEnum">
    <xs:enumeration value="EM_BRANCO"/>
    <xs:enumeration value="ENSINO_FUNDAMENTAL_INCOMPLETO"/>
    <xs:enumeration value="ENSINO_FUNDAMENTAL_COMPLETO"/>
    <xs:enumeration value="ENSINO_MEDIO_INCOMPLETO"/>
    <xs:enumeration value="ENSINO_MEDIO_COMPLETO"/>
    <xs:enumeration value="ENSINO_SUPERIOR_INCOMPLETO"/>
    <xs:enumeration value="ENSINO_SUPERIOR_COMPLETO"/>
    <xs:enumeration value="PROFISSIONALIZANTE"/>
    <xs:enumeration value="TECNICO_INCOMPLETO"/>
    <xs:enumeration value="TECNICO_COMPLETO"/>
    <xs:enumeration value="TECNOLOGO_INCOMPLETO"/>
    <xs:enumeration value="TECNOLOGO_COMPLETO"/>
    <xs:enumeration value="POS_GRADUACAO_INCOMPLETA"/>
    <xs:enumeration value="POS_GRADUACAO_COMPLETA"/>
    <xs:enumeration value="MESTRADO_INCOMPLETO"/>
    <xs:enumeration value="MESTRADO_COMPLETO"/>
    <xs:enumeration value="DOUTORADO_INCOMPLETO"/>
    <xs:enumeration value="DOUTORADO_COMPLETO"/>
    <xs:enumeration value="PHD_INCOMPLETO"/>
    <xs:enumeration value="PHD_COMPLETO"/>
    <xs:enumeration value="NAO_INFORMADO"/>
    <xs:enumeration value="ANALFABETO"/>
</xs:simpleType>

<xs:simpleType name="estadosEnum">
    <xs:enumeration value="AC"/>
    <xs:enumeration value="AL"/>
    <xs:enumeration value="AM"/>
    <xs:enumeration value="AP"/>
    <xs:enumeration value="BA"/>
    <xs:enumeration value="CE"/>
    <xs:enumeration value="DF"/>
    <xs:enumeration value="ES"/>
    <xs:enumeration value="GO"/>
    <xs:enumeration value="MA"/>
    <xs:enumeration value="MG"/>
    <xs:enumeration value="MS"/>
    <xs:enumeration value="MT"/>
    <xs:enumeration value="PA"/>
    <xs:enumeration value="PB"/>
    <xs:enumeration value="PE"/>
    <xs:enumeration value="PI"/>
    <xs:enumeration value="PR"/>
    <xs:enumeration value="RJ"/>
    <xs:enumeration value="RN"/>
    <xs:enumeration value="RO"/>
    <xs:enumeration value="RR"/>
    <xs:enumeration value="RS"/>
    <xs:enumeration value="SC"/>
    <xs:enumeration value="SE"/>
    <xs:enumeration value="SP"/>
    <xs:enumeration value="TO"/>
</xs:simpleType>

estadoCivilEnum
    <xs:enumeration value="SOLTEIRO"/>
    <xs:enumeration value="CASADO"/>
    <xs:enumeration value="SEPARADO"/>
    <xs:enumeration value="DIVORCIADO"/>
    <xs:enumeration value="VIUVO"/>
    <xs:enumeration value="OUTROS"/>
    <xs:enumeration value="DESQUITADO"/>
    <xs:enumeration value="UNIAO_ESTAVEL"/>

tipoFuncaoBrigadaEnum
    <xs:enumeration value="EM_BRANCO"/>
    <xs:enumeration value="COORDENADOR_GERAL"/>
    <xs:enumeration value="LIDER"/>
    <xs:enumeration value="CHEFE_DE_BRIGADA"/>
    <xs:enumeration value="BRIGADISTA"/>

historicoPPP
    <xs:enumeration value="EXIBIR"/>
    <xs:enumeration value="NAO_EXIBIR"/>
    
reguneTrabalhoEnum
    <xs:enumeration value="NORMAL"/>
    <xs:enumeration value="TURNO"/>

regimeTrabalhoEnum
    <xs:enumeration value="NORMAL"/>
    <xs:enumeration value="TURNO"/>

sexoEnum
    <xs:enumeration value="MASCULINO"/>
    <xs:enumeration value="FEMININO"/>

situacaoFuncionario
        <xs:enumeration value="ATIVO"/>
        <xs:enumeration value="AFASTADO"/>
        <xs:enumeration value="PENDENTE"/>
        <xs:enumeration value="FERIAS"/>
        <xs:enumeration value="INATIVO"/>

tipoBuscaEmpresaEnum
        <xs:enumeration value="CODIGO_SOC"/>
        <xs:enumeration value="CODIGO_CLIENTE"/>

tipoContratacaoEnum 
        <xs:enumeration value="CLT"/>
        <xs:enumeration value="COOPERADO"/>
        <xs:enumeration value="TERCERIZADO"/>
        <xs:enumeration value="AUTONOMO"/>
        <xs:enumeration value="TEMPORARIO"/>
        <xs:enumeration value="PESSOA_JURIDICA"/>
        <xs:enumeration value="ESTAGIARIO"/>
        <xs:enumeration value="MENOR_APRENDIZ"/>
        <xs:enumeration value="ESTATUTARIO"/>
        <xs:enumeration value="COMISSIONADO_INTERNO"/>
        <xs:enumeration value="COMISSIONADO_EXTERNO"/>
        <xs:enumeration value="APOSENTADO"/>
        <xs:enumeration value="APOSENTADO_INATIVO_PREFEITURA"/>
        <xs:enumeration value="PENSIONISTA"/>
        <xs:enumeration value="SERVIDOR_PUBLICO_EFETIVO"/>
        <xs:enumeration value="EXTRANUMERARIO"/>
        <xs:enumeration value="AUTARQUICO"/>
        <xs:enumeration value="INATIVO"/>
        <xs:enumeration value="TITULO_PRECARIO"/>
        <xs:enumeration value="SERVIDOR_ADM_CENTRALIZADA_OU_DESCENTRALIZADA"/>

generoEnum
        <xs:enumeration value="EM_BRANCO"/>
        <xs:enumeration value="TRAVESTI"/>
        <xs:enumeration value="TRANSEXUAL"/>

tipoVinculoEnum 
        <xs:enumeration value="EM_BRANCO"/>
        <xs:enumeration value="EMPREGATICIO"/>
        <xs:enumeration value="ASSOCIATIVO"/>

tipoAdmissaoEnum
        <xs:enumeration value="EM_BRANCO"/>
        <xs:enumeration value="ADMISSAO"/>
        <xs:enumeration value="TRANSFERENCIA_EMPRESA_MESMO_GRUPO"/>
        <xs:enumeration value="TRANSFERENCIA_EMPRESA_CONSORCIADA"/>
        <xs:enumeration value="TRANSFERENCIA_MOTIVO_SUCESSAO"/>

tipoSanguineoEnum 
        <xs:enumeration value="NENHUM"/>
        <xs:enumeration value="O_POSITIVO"/>
        <xs:enumeration value="A_POSITIVO"/>
        <xs:enumeration value="AB_POSITIVO"/>
        <xs:enumeration value="B_POSITIVO"/>
        <xs:enumeration value="O_NEGATIVO"/>
        <xs:enumeration value="A_NEGATIVO"/>
        <xs:enumeration value="AB_NEGATIVO"/>
        <xs:enumeration value="B_NEGATIVO"/>

corOlhoNorma13Enum 
        <xs:enumeration value="EM_BRANCO"/>
        <xs:enumeration value="AZUL"/>
        <xs:enumeration value="AZUL_ESVERDEADO"/>
        <xs:enumeration value="CASTANHO"/>
        <xs:enumeration value="CINZA"/>
        <xs:enumeration value="VERDE"/>
        <xs:enumeration value="AVELA"/>
        <xs:enumeration value="AMBAR"/>
        <xs:enumeration value="VERMELHO"/>
        <xs:enumeration value="VIOLETA"/>

funcionarioGrauInstrucaoEnum
        <xs:enumeration value="EM_BRANCO"/>
        <xs:enumeration value="ANALFABETO"/>
        <xs:enumeration value="QUINTO_INCOMPLETO"/>
        <xs:enumeration value="QUINTO_COMPLETO"/>
        <xs:enumeration value="FUNDAMENTAL_INCOMPLETO"/>
        <xs:enumeration value="FUNDAMENTAL_COMPLETO"/>
        <xs:enumeration value="MEDIO_INCOMPLETO"/>
        <xs:enumeration value="MEDIO_COMPLETO"/>
        <xs:enumeration value="SUPERIOR_INCOMPLETO"/>
        <xs:enumeration value="SUPERIOR_COMPLETO"/>
        <xs:enumeration value="POS_GRADUACAO_COMPLETA"/>
        <xs:enumeration value="MESTRADO_COMPLETO"/>
        <xs:enumeration value="DOUTORADO_COMPLETO"/>

tipoBuscaMotivoLicencaEnum
        <xs:enumeration value="CODIGO"/>
        <xs:enumeration value="CODIGO_INTEGRACAO"/>
        <xs:enumeration value="NOME"/>

tipoBuscaSetorEnum 
        <xs:enumeration value="CODIGO"/>
        <xs:enumeration value="CODIGO_RH"/>
        <xs:enumeration value="NOME"/>

xs:simpleType name="tipoBuscaTurnoEnum">
    <xs:enumeration value="CODIGO"/>
    <xs:enumeration value="NOME"/>
    <xs:enumeration value="CODIGO_RH"/>
</xs:simpleType>

<xs:simpleType name="cnpjCei">
    <xs:enumeration value="CNPJ"/>
    <xs:enumeration value="CEI"/>
    <xs:enumeration value="CPF"/>
    <xs:enumeration value="CAEPF"/>
    <xs:enumeration value="CNO"/>
</xs:simpleType>

<xs:simpleType name="tipoBuscaUnidadeEnum">
    <xs:enumeration value="CODIGO"/>
    <xs:enumeration value="CODIGO_RH"/>
    <xs:enumeration value="NOME"/>
</xs:simpleType>

<xs:simpleType name="tipoCnae">
    <xs:enumeration value="CNAE"/>
    <xs:enumeration value="CNAE_2"/>
    <xs:enumeration value="CNAE_7"/>
    <xs:enumeration value="CNAE_LIVRE"/>

'''

funcionarioCentroCustoWsVo = factory.funcionarioCentroCustoWsVo(
    codigo='',
    codigoRh='0',
    nome='',
    tipoBusca='CODIGO'
)

atividadesPerigosasWsVo = factory.atividadesPerigosasWsVo(
    codigoAtividadePerigosa=''
)

funcionarioCargoWsVo = factory.funcionarioCargoWsVo(
    atualizaDescricaoRequisitosCargoPeloCbo=False,
    cbo='',
    codigo='',
    codigoRh='',
    descricaoDetalhada='',
    descricaoLocal='',
    educacao='',
    experiencia='',
    funcao='',
    gfip=0,
    habilidades='',
    localTrabalho='',
    materialUtilizado='',
    mobiliarioUtilizado='',
    nome='',
    nomeLegal='',
    orientacaoAso='',
    requisitosFuncao='',
    status='ATIVO',
    tipoBusca='CODIGO',
    treinamento='',
    atividadesPerigosasWsVo=atividadesPerigosasWsVo,
    criarHistoricoDescricao=False
)

funcionarioClassificacaoDeficienciaWsVo = factory.funcionarioClassificacaoDeficienciaWsVo(
    classificacao='DEFICIENCIA_FISICA',
    codigo='',
    nome='',
    tipoBusca='CODIGO',
)

deficienciaWsVo = factory.deficienciaWsVo(
    cids='',
    classificacaoDeficiencia=funcionarioClassificacaoDeficienciaWsVo,
    codigoLegislacaoReferencia='',
    codigoMedico='',
    dataEmissaoLaudo='',
    deficiencia='',
    deficiente=False,
    gravarHistorico=False,
    nomeLegislacaoReferencia='',
    observacao='',
    origemDeficiencia='EM_BRANCO',
    parecerLaudo='EM_BRANCO',
    reabilitado=False,
    tipoBuscaLegislacaoReferencia='CODIGO',
    dataReabilitacao=''
)

funcionarioWsVo = factory.funcionarioWsVo(
    autorizadoMensagemSms=False,
    bairro='',
    campoInteiro01=0,
    campoInteiro02=0,
    campoInteiro03=0,
    campoInteiro04=0,
    campoInteiro05=0,
    campoInteiro06=0,
    campoInteiro07=0,
    campoInteiro08=0,
    campoInteiro09=0,
    campoInteiro10=0,
    campoString01='',
    campoString02='',
    campoString03='',
    campoString04='',
    campoString05='',
    campoString06='',
    campoString07='',
    campoString08='',
    campoString09='',
    campoString10='',
    campoString11='',
    campoString12='',
    campoString13='',
    campoString14='',
    campoString15='',
    campoString16='',
    campoString17='',
    campoString18='',
    campoString19='',
    campoString20='',
    campoString21='',
    campoString22='',
    campoString23='',
    campoString24='',
    campoString25='',
    campoString26='',
    campoString27='',
    campoString28='',
    campoString29='',
    campoString30='',
    carteiraNacionalSaude='',
    categoria='EM_BRANCO',
    cep='',
    chaveProcuraFuncionario='CODIGO',
    cidade='',
    cipa='EM_BRANCO',
    cipaDataFimMandato='',
    cipaDataInicioMandato='',
    cnpjEmpresaFuncionario='',
    codigo='',
    codigoEmpresa='',
    codigoMunicipio='',
    complementoEndereco='',
    contatoEmergencia='',
    cor='EM_BRANCO',
    cpf='',
    dataAdmissao='',
    dataAfastamento='',
    dataDemissao='',
    dataDemissionalCarta='',
    dataEmissaoCtps='',
    dataFinalEstabilidade='',
    dataNascimento='',
    dataUltimaMovimentacao='',
    desabilitarRisco=False,
    descricaoAtividade='',
    email='',
    endereco='',
    enderecoEmergencia='',
    escolaridade='EM_BRANCO',
    estado='SP',
    estadoCivil='SOLTEIRO',
    funcao='',
    funcaoBrigadaIncendio='EM_BRANCO',
    gfip=0,
    historicoPPP='NAO_EXIBIR',
    matricula='',
    naoPossuiCpf=False,
    naoPossuiCtps=False,
    naoPossuiMatricula=False,
    naoPossuiMatriculaRh=False,
    naoPossuiPis=False,
    naturalidade=False,
    nomeCooperativa='',
    nomeFuncionario='',
    nomeMae='',
    nrCtps='',
    numeroEndereco='',
    observacaoAso='',
    observacaoEstabilidade='',
    observacaoPpp='',
    parentescoContatoEmergencia='',
    pis='',
    ramal='',
    ramalTelefoneEmergencia='',
    razaoSocialEmpresaFuncionario='',
    regimeRevezamento='',
    regimeTrabalho='NORMAL',
    remuneracaoMensal=0,
    requisitosFuncao='',
    rg='',
    rgDataEmissao='',
    rgOrgaoEmissor='',
    rgUf='SP',
    serieCtps='',
    sexo='MASCULINO',
    situacao='ATIVO',
    telefoneCelular='',
    telefoneComercial='',
    telefoneEmergencia='',
    telefoneResidencial='',
    telefoneSms='',
    tipoBuscaEmpresa='CODIGO_SOC',
    tipoContratacao='CLT',
    ufCtps='SP',
    utilizarDescricaoRequisitoCargo=False,
    observacaoFuncionario='',
    codigoPaisNascimento='',
    emailPessoal='',
    matriculaRh='',
    codigoCategoriaESocial=0,
    genero='EM_BRANCO',
    nomeSocial='',
    tipoVinculo='EM_BRANCO',
    tipoAdmissao='EM_BRANCO',
    nomePai='',
    atividadesPerigosasWsVo=atividadesPerigosasWsVo,
    tipoSanguineo='NENHUM',
    corDosOlhos='EM_BRANCO',
    grauInstrucao='EM_BRANCO',
    cns="",
    dataInicioPeriodoAquisitivo='',
    dataFimPeriodoAquisitivo='',
    codigoRh='',
    desconsiderarEsocial=False,
    codigoGenero='',
    dataValidadeRg=''
)

motivoLicencaWsVo = factory.motivoLicencaWsVo(
    codigo = '',
    codigoDeIntegracao = '',
    nome = '',
    tipoBusca = 'CODIGO',
    campoString01 = ''
)

setorWsVo = factory.setorWsVo(
    codigo='',
    codigoRh='',
    descricao='',
    nome='',
    observacaoAso='',
    status='ATIVO',
    tipoBusca='CODIGO',
    criarHistoricoDescricao=False
)

funcionarioTurnoWsVo = factory.funcionarioTurnoWsVo(
    cargaHorariaSemanal='',
    codigo='',
    nome='',
    tipoBusca = 'CODIGO',
    codigoRh=''
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
    dataTransferencia='',
    copiaHistoricoLaboral=False,
    esocial=False,
    copiaCadastroMedico=False,
    copiaHistoricoVacinas=False
)

funcionarioUnidadeWsVo = factory.funcionarioUnidadeWsVo(
    bairro='',
    bairroCobranca='',
    cep='',
    cepCobranca='',
    cidade='',
    cidadeCobranca='',
    cnpj_cei='CNPJ',
    codigo='',
    codigoArquivo='',
    codigoCnae='',
    codigoCnpjCei='',
    codigoMunicipio='',
    codigoMunicipioCobranca='',
    codigoRh='',
    complemento='',
    complementoCobranca='',
    dataAssinaturaContrato='',
    descricaoCnae='',
    endereco='',
    enderecoCobranca='',
    estado='',
    estadoCobranca='',
    grauRisco=0,
    inscricaoEstadual='',
    inscricaoMunicipal='',
    nome='',
    numero='',
    numeroCobranca='',
    observacaoASO='',
    observacaoContrato='',
    observacaoPPP='',
    percentualCalculoBrigada='',
    razaoSocial='',
    status='ATIVO',
    telefoneCat='',
    tipoBusca='CODIGO',
    tipoCnae='CNAE',
    unidadeContratante=False,
    codigoCpf='',
    codigoCaepf='',
    caracterizacaoProcessosAmbientesTrabalho='',
    codigoCno=''
)

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
    criarCentroCusto=False,
    criarFuncionario=False,
    criarHistorico=False,
    criarMotivoLicenca=False,
    criarSetor=False,
    criarTurno=False,
    criarUnidade=False,
    criarUnidadeContratante=False,
    deficienciaWsVo=deficienciaWsVo,
    destravarFuncionarioBloqueado=False,
    funcionarioWsVo=funcionarioWsVo,
    motivoLicencaWsVo=motivoLicencaWsVo,
    naoImportarFuncionarioSemHierarquia=False,
    setorWsVo=setorWsVo,
    turnoWsVo=funcionarioTurnoWsVo,
    unidadeContratanteWsVo=funcionarioUnidadeWsVo,
    unidadeWsVo=funcionarioUnidadeWsVo,
    transferirFuncionario=False,
    transferencia=transferencia
)

try:
    client.service.importacaoFuncionario(Funcionario=funcionario)
except RuntimeError as error:
    print(error)
    print("The linux_interaction() function wasn't executed.")


def xml_to_dataframe(xml_string: str) -> pd.DataFrame:
    """Recebe corpo do Response de Exporta Dados e retorna \
    DataFrame contido na tag 'retorno'
    """
    xml_dic = xmltodict.parse(xml_string)
    dados = json.loads(
    xml_dic['soap:Envelope']['soap:Body']\
        ['ns2:exportaDadosWsResponse']['return']['retorno']
    )
    return pd.DataFrame(data=dados)
