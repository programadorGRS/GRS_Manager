const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))


function toggleCheckBoxes(source, checkItemName) {
    checkboxes = document.getElementsByName(checkItemName);
    for(var i=0, n=checkboxes.length; i<n; i++) {
      checkboxes[i].checked = source.checked;
    }
  }


function CarregarOpcoesBuscaSOCNET(
    idEmpresaPrincipal,
    idEmpresa,
    idPrestador,
    idPesquisaGeral
){
    carregarOpcoesEmpresaSOCNET(idEmpresaPrincipal, idEmpresa, idPesquisaGeral);
    carregarOpcoesPrestador(idEmpresaPrincipal, idPrestador, idPesquisaGeral);
}


function carregarOpcoesEmpresaSOCNET(idEmpresaPrincipal, idEmpresa, idPesquisaGeral){
    let empresa_principal = document.getElementById(idEmpresaPrincipal);
    let empresa = document.getElementById(idEmpresa);

    if (idPesquisaGeral){
        var pesquisaGeral = document.getElementById(idPesquisaGeral);

        if (pesquisaGeral.checked) {
            var todos = 1;
        } else {
            var todos = 0;
        }
    } else {
        var todos = 1;
    };

    if (empresa_principal.value == '') {
        empresa.innerHTML = '<option value="">Selecione</option>';
    } else {
        fetch('/fetch_empresas_socnet/' + empresa_principal.value + '/' + todos).then(function(response) {
            response.json().then(function(data){
                let optionHTML = '<option value="">Selecione</option>';
                for (let i of data.dados) {
                    optionHTML += '<option value="' + i.id + '">' + i.nome + '</option>';
                }
                empresa.innerHTML = optionHTML;
            });
        });
    }
}


function carregarOpcoesEmpresa(idEmpresaPrincipal, idEmpresa, idPesquisaGeral){
    let empresa_principal = document.getElementById(idEmpresaPrincipal);
    let empresa = document.getElementById(idEmpresa);

    if (idPesquisaGeral){
        var pesquisaGeral = document.getElementById(idPesquisaGeral);

        if (pesquisaGeral.checked) {
            var todos = 1;
        } else {
            var todos = 0;
        }
    } else {
        var todos = 1;
    };

    if (empresa_principal.value == '') {
        empresa.innerHTML = '<option value="">Selecione</option>';
    } else {
        fetch('/fetch_empresas/' + empresa_principal.value + '/' + todos).then(function(response) {
            response.json().then(function(data){
                let optionHTML = '<option value="">Selecione</option>';
                for (let i of data.dados) {
                    optionHTML += '<option value="' + i.id + '">' + i.nome + '</option>';
                }
                empresa.innerHTML = optionHTML;
            });
        });
    }
}

function carregarOpcoesEmpresa2(idEmpresaPrincipal, idEmpresa, idEmpresasAtivas){
    let empresaPrincipal = document.getElementById(idEmpresaPrincipal);
    let empresa = document.getElementById(idEmpresa);
    let empresasAtivas = null;

    let statusEmpresas = null;

    if (idEmpresasAtivas){
        empresasAtivas = document.getElementById(idEmpresasAtivas);
        statusEmpresas = empresasAtivas.value;
    }

    if (empresaPrincipal.value == '') {
        empresa.innerHTML = '<option value="">Selecione uma Empresa Principal</option>';
    } else {
        const queryParams = new URLSearchParams({
            cod_empresa_principal: empresaPrincipal.value,
            status_empresas: statusEmpresas
        });

        fetch('/fetch_empresas_v2?' + queryParams)
            .then((resp) => resp.json())
            .then((jsonData) => {
                    let optionHTML = '<option value="">Selecione</option>';
                    for (let i of jsonData) {
                        optionHTML += '<option value="' + i.id + '">' + i.nome + '</option>';
                    }
                    empresa.innerHTML = optionHTML;
                }
            )
            .catch((err) => console.error(err))
    }
}

function carregarOpcoesUnidade(idEmpresaPrincipal, idEmpresa, idUnidade){
    let empresa_principal = document.getElementById(idEmpresaPrincipal);
    let empresa = document.getElementById(idEmpresa);
    let unidade = document.getElementById(idUnidade);

    if (empresa.value == '') {
        unidade.innerHTML = '<option value="">Selecione</option>';
    } else {
        fetch('/fetch_unidades/' + empresa_principal.value + '/' + empresa.value).then(function(response) {
            response.json().then(function(data){
                let optionHTML = '<option value="">Selecione</option>';
                for (let i of data.dados) {
                    optionHTML += '<option value="' + i.id + '">' + i.nome + '</option>';
                }
                unidade.innerHTML = optionHTML;
            });
        });
    }
}


function carregarOpcoesUnidadePublic(idEmpresaPrincipal, idEmpresa, idUnidade){
    let empresa_principal = document.getElementById(idEmpresaPrincipal);
    let empresa = document.getElementById(idEmpresa);
    let unidade = document.getElementById(idUnidade);

    if (empresa.value == '') {
        unidade.innerHTML = '<option value="">Selecione</option>';
    } else {
        fetch('/fetch_unidades_public/' + empresa_principal.value + '/' + empresa.value).then(function(response) {
            response.json().then(function(data){
                let optionHTML = '<option value="">Selecione</option>';
                for (let i of data.dados) {
                    optionHTML += '<option value="' + i.id + '">' + i.nome + '</option>';
                }
                unidade.innerHTML = optionHTML;
            });
        });
    }
}


function carregarOpcoesExame(idEmpresaPrincipal, idExame){
    let empresaPrincipal = document.getElementById(idEmpresaPrincipal);
    let exame = document.getElementById(idExame);

    if (empresaPrincipal.value == '') {
        exame.innerHTML = '<option value="">Selecione</option>';
    } else {
        fetch('/fetch_exames/' + empresaPrincipal.value).then(function(response) {
            response.json().then(function(data){
                let optionHTML = '<option value="">Selecione</option>';
                for (let i of data.dados) {
                    optionHTML += '<option value="' + i.id + '">' + i.nome + '</option>';
                }
                exame.innerHTML = optionHTML;
            });
        });
    }
}


function carregarOpcoesPrestador(idEmpresaPrincipal, idPrestador, idpesquisaGeral){
    let empresaPrincipal = document.getElementById(idEmpresaPrincipal);
    let prestador = document.getElementById(idPrestador);
    let pesquisaGeral = document.getElementById(idpesquisaGeral);

    if (pesquisaGeral.checked) {
        var todos = 1;
    } else {
        var todos = 0;
    }

    if (empresaPrincipal.value == '') {
        prestador.innerHTML = '<option value="">Selecione</option>';
    } else {
        fetch('/fetch_prestadores/' + empresaPrincipal.value + '/' + todos).then(function(response) {
            response.json().then(function(data){
                let optionHTML = '<option value="">Selecione</option>';
                optionHTML += '<option value="0">Vazio</option>';
                for (let i of data.dados) {
                    optionHTML += '<option value="' + i.id + '">' + i.nome + '</option>';
                }
                prestador.innerHTML = optionHTML;
            });
        });
    }
}


function CarregarOpcoesBuscaPedido(
    idEmpresaPrincipal,
    idEmpresa,
    idPrestador,
    idUnidade,
    idPesquisaGeral
){    
    carregarOpcoesEmpresa(idEmpresaPrincipal, idEmpresa, idPesquisaGeral);
    carregarOpcoesPrestador(idEmpresaPrincipal, idPrestador, idPesquisaGeral);
    
    document.getElementById(idUnidade).innerHTML = '<option value="">Selecione</option>';
}


function CarregarOpcoesExamesRealizados(
    idEmpresaPrincipal,
    idEmpresa,
    idUnidade,
    idExame
){    
    carregarOpcoesEmpresa(idEmpresaPrincipal, idEmpresa);
    carregarOpcoesExame(idEmpresaPrincipal, idExame)
    
    document.getElementById(idUnidade).innerHTML = '<option value="">Selecione</option>';
}

function CarregarOpcoesAbsenteismo(
    idEmpresaPrincipal,
    idEmpresa,
    idUnidade,
){
    carregarOpcoesEmpresa(idEmpresaPrincipal, idEmpresa);
    document.getElementById(idUnidade).innerHTML = '<option value="">Selecione um Empresa</option>';
}


function scrollToTop(){
    window.scrollTo(0, 0);
}